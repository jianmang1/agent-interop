import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
import pandas as pd
from scipy.ndimage import convolve
import warnings

# 忽略一些非关键的警告
warnings.filterwarnings("ignore")


def resample_to_template(source_path, template_path):
    """
    将源栅格重采样到模板栅格的网格、投影和分辨率上。
    返回重采样后的 numpy 数组。
    """
    with rasterio.open(template_path) as template:
        target_crs = template.crs
        target_transform = template.transform
        target_width = template.width
        target_height = template.height
        target_dtype = template.dtypes[0]

    with rasterio.open(source_path) as source:
        # 创建目标数组
        dest = np.zeros((target_height, target_width), dtype=source.dtypes[0])

        # 执行重投影
        reproject(
            source=rasterio.band(source, 1),
            destination=dest,
            src_transform=source.transform,
            src_crs=source.crs,
            dst_transform=target_transform,
            dst_crs=target_crs,
            resampling=Resampling.nearest,  # 分类数据必须用最近邻
            src_nodata=source.nodata,
            dst_nodata=-9999
        )
        return dest


def calculate_neighborhood_stats_vectorized(class_array):
    """
    一次性计算整个数组中每个像素 3x3 邻域内 31, 32, 33 的数量。
    返回三个数组: n31_map, n32_map, n33_map
    """
    # 创建布尔掩码
    mask_31 = (class_array == 31).astype(np.float32)
    mask_32 = (class_array == 32).astype(np.float32)
    mask_33 = (class_array == 33).astype(np.float32)

    # 定义 3x3 的核
    kernel = np.ones((3, 3), dtype=np.float32)

    # 使用卷积计算邻域和。mode='constant', cval=0 处理边界
    n31_map = convolve(mask_31, kernel, mode='constant', cval=0.0)
    n32_map = convolve(mask_32, kernel, mode='constant', cval=0.0)
    n33_map = convolve(mask_33, kernel, mode='constant', cval=0.0)

    return n31_map, n32_map, n33_map


def calculate_neighborhood_means_vectorized(class_array, mean_array, target_classes, nodata_val_mean):
    """
    一次性计算整个数组中每个像素 3x3 邻域内各目标类别的 mean 值的均值。
    返回一个字典，键为目标类别，值为对应的均值数组。
    """
    height, width = class_array.shape
    means_dict = {}

    # 创建有效的 mean 掩码
    mean_valid_mask = (mean_array != nodata_val_mean) & (mean_array >= 0)

    # 遍历每个目标类别
    for cls in target_classes:
        # 创建该类别的掩码
        class_mask = (class_array == cls)

        # 计算分子：邻域内该类别且 mean 有效的值之和
        # 使用卷积计算加权和
        numerator_sum = convolve(
            (mean_array * class_mask * mean_valid_mask).astype(np.float64),
            np.ones((3, 3), dtype=np.float64),
            mode='constant', cval=0.0
        )

        # 计算分母：邻域内该类别且 mean 有效的数量
        denominator_count = convolve(
            (class_mask * mean_valid_mask).astype(np.float64),
            np.ones((3, 3), dtype=np.float64),
            mode='constant', cval=0.0
        )

        # 计算均值，避免除零
        mean_vals = np.divide(numerator_sum, denominator_count,
                              out=np.zeros_like(numerator_sum, dtype=np.float32),
                              where=(denominator_count != 0))

        means_dict[cls] = mean_vals

    return means_dict


def process_data_fast(mean_config, source_raster_path, output_excel_path):
    print("开始高效数据分析流程 (包含差异值计算)...")

    all_results = []

    for i, (mean_path, prefix) in enumerate(mean_config):
        print(f"\n[{i + 1}/{len(mean_config)}] 正在处理 {prefix} 数据: {mean_path}")

        # 1. 读取 Mean 数据
        with rasterio.open(mean_path) as mean_src:
            mean_array = mean_src.read(1).astype(np.float32)
            nodata_val_mean = mean_src.nodata if mean_src.nodata is not None else -9999
            mean_mask_invalid = (mean_array == nodata_val_mean) | (mean_array < 0)

            height, width = mean_array.shape
            transform = mean_src.transform
            crs = mean_src.crs

        # 2. 动态重采样 Source (分类图) 到 Mean 的网格
        print(f"  -> 将分类图重采样到 {prefix} 的网格...")
        class_array = resample_to_template(source_raster_path, mean_path)

        # 设置分类图的无效值
        class_invalid_mask = (class_array == -9999)

        # 3. 向量化计算邻域统计 (3x3 window for 31, 32, 33)
        print(f"  -> 计算 3x3 邻域统计量 (向量化)...")
        n31_map, n32_map, n33_map = calculate_neighborhood_stats_vectorized(class_array)

        # 4. 确定有效分析区域
        center_is_22 = (class_array == 22)
        mean_is_valid = ~mean_mask_invalid
        neighbor_has_target = (n31_map + n32_map + n33_map) > 0
        final_mask = center_is_22 & mean_is_valid & neighbor_has_target

        # 获取所有满足条件的像素索引
        rows, cols = np.where(final_mask)

        if len(rows) == 0:
            print(f"  -> 警告：{prefix} 未找到符合条件的记录。")
            continue

        print(f"  -> 找到 {len(rows)} 个有效样本点，正在计算邻域均值及差异值...")

        # 5. 向量化提取中心像素值
        center_values = mean_array[rows, cols]  # 这是 value

        # 6. 向量化计算邻域均值
        target_classes = [31, 32, 33, 61, 62, 63, 64, 65, 66]
        all_means_dict = calculate_neighborhood_means_vectorized(class_array, mean_array, target_classes,
                                                                 nodata_val_mean)

        # 7. 向量化计算差异值 (邻域均值 - 中心值)
        result_dict = {
            'row': rows,
            'col': cols,
            'n31': n31_map[rows, cols],
            'n32': n32_map[rows, cols],
            'n33': n33_map[rows, cols],
            f'{prefix}_value': center_values
        }

        for cls in target_classes:
            raw_neighbor_mean = all_means_dict[cls][rows, cols]
            # 新逻辑：如果 raw_neighbor_mean != 0，则计算差值；否则为 0
            diff_values = np.where(raw_neighbor_mean != 0.0, raw_neighbor_mean - center_values, 0.0)
            result_dict[f'{prefix}_{cls}'] = diff_values  # 存储的是差异值

        # 转换为 DataFrame
        df_batch = pd.DataFrame(result_dict)
        all_results.append(df_batch)
        print(f"  -> {prefix} 处理完成。")

    # 合并所有结果
    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        final_df.to_excel(output_excel_path, index=False)
        print(f"\n所有数据处理完成！共 {len(final_df)} 条记录。")
        print(f"结果保存至: {output_excel_path}")
    else:
        print("\n未找到任何符合条件的记录。")


# ================= 主程序配置 =================

# 路径配置
source_raster_path = r'F:\个人\CLASS\新建文件夹\中科院_mode_resampled_clipped1.tif'

# 多个 mean 文件的配置
mean_config = [
    (r'D:\MODIS43A4_2024\SOS2\masked2_masked_all_SoS_DOY_2023_masked_tibet.tif', 'sos'),
    (r'D:\MODIS43A4_2024\POS2\masked2_masked_all_PoS_DOY_2023_masked_tibet.tif', 'pos'),
    (r'D:\MODIS43A4_2024\EOS2\masked2_masked_all_EoS_DOY_2023_masked_tibet.tif', 'eos'),
]

output_excel_path = r'D:\MODIS43A4_2024\combined_output2.xlsx'

if __name__ == "__main__":
    # 执行处理
    process_data_fast(mean_config, source_raster_path, output_excel_path)