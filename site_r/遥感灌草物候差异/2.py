import rasterio
from rasterio.warp import reproject, Resampling, calculate_default_transform
import numpy as np
import pandas as pd
from scipy.ndimage import generic_filter
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
        target_dtype = template.dtypes[0]  # 通常目标数据类型不影响分类值，但保持兼容

    with rasterio.open(source_path) as source:
        # 创建目标数组
        dest = np.zeros((target_height, target_width), dtype=source.dtypes[0])

        # 执行重投影
        # source=源数据, destination=目标数组
        # src_transform/crs=源的元数据
        # dst_transform/crs=目标的元数据 (从 template 获取)
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


def count_classes_in_window(window_flat):
    """
    用于 generic_filter 的函数。
    输入是一个展平的 3x3 窗口 (9个值)。
    返回一个包含 [n31, n32, n33] 的元组。
    """
    # window_flat 是 1D 数组，长度为 9
    n31 = np.count_nonzero(window_flat == 31)
    n32 = np.count_nonzero(window_flat == 32)
    n33 = np.count_nonzero(window_flat == 33)
    # 返回一个标量？不行，generic_filter 通常返回标量。
    # 为了返回多个值，我们需要分别调用三次，或者使用特殊的技巧。
    # 更简单的做法：分别计算三个通道的卷积，或者在这里只返回一个编码值，后面再解码？
    # 不，最高效的方法是分别对 31, 32, 33 做布尔运算后求和。
    return n31  # 这个函数只能返回一个标量，所以我们需要调用三次


# 更好的向量化策略：不使用 generic_filter 返回多值，而是直接利用布尔数组和卷积
def calculate_neighborhood_stats_vectorized(class_array):
    """
    一次性计算整个数组中每个像素 3x3 邻域内 31, 32, 33 的数量。
    返回三个数组: n31_map, n32_map, n33_map
    """
    from scipy.ndimage import uniform_filter

    # 创建布尔掩码
    mask_31 = (class_array == 31).astype(np.float32)
    mask_32 = (class_array == 32).astype(np.float32)
    mask_33 = (class_array == 33).astype(np.float32)

    # 定义 3x3 的核
    kernel = np.ones((3, 3), dtype=np.float32)

    from scipy.ndimage import convolve

    # 使用卷积计算邻域和。mode='constant', cval=0 处理边界，即边界外视为0
    # 注意：convolve 会计算包括中心像素在内的 3x3 总和，这正是我们需要的
    n31_map = convolve(mask_31, kernel, mode='constant', cval=0.0)
    n32_map = convolve(mask_32, kernel, mode='constant', cval=0.0)
    n33_map = convolve(mask_33, kernel, mode='constant', cval=0.0)

    return n31_map, n32_map, n33_map


def process_data_fast(mean_config, source_raster_path, output_excel_path):
    print("开始高效数据分析流程...")

    all_results = []

    # 我们不需要预先重采样 source 到一个固定文件。
    # 因为每个 mean 文件可能（虽然通常不会）有微小的差异，或者为了保险起见，
    # 最佳实践是：针对每一个 mean 文件，将 source 重采样到该 mean 的网格上。
    # 这样保证 100% 像素对齐。

    for i, (mean_path, prefix) in enumerate(mean_config):
        print(f"\n[{i + 1}/{len(mean_config)}] 正在处理 {prefix} 数据: {mean_path}")

        # 1. 读取 Mean 数据
        with rasterio.open(mean_path) as mean_src:
            mean_array = mean_src.read(1).astype(np.float32)
            # 假设 <0 为无效值 (根据原逻辑)
            # 如果原数据有特定的 nodata 值，最好用 mean_src.nodata
            nodata_val = mean_src.nodata if mean_src.nodata is not None else -9999
            mean_mask_invalid = (mean_array == nodata_val) | (mean_array < 0)

            height, width = mean_array.shape
            transform = mean_src.transform
            crs = mean_src.crs

        # 2. 动态重采样 Source (分类图) 到 Mean 的网格
        print(f"  -> 将分类图重采样到 {prefix} 的网格...")
        class_array = resample_to_template(source_raster_path, mean_path)

        # 设置分类图的无效值 (重采样时设置的 -9999)
        class_invalid_mask = (class_array == -9999)

        # 3. 向量化计算邻域统计 (3x3 window)
        print(f"  -> 计算 3x3 邻域统计量 (向量化)...")
        n31_map, n32_map, n33_map = calculate_neighborhood_stats_vectorized(class_array)

        # 4. 确定有效分析区域
        # 条件 A: 中心像素分类必须是 22 (根据原代码: src_array == 22)
        # 条件 B: 对应的 mean 值必须有效
        # 条件 C: 分类图本身有效 (通常由A隐含，但显式检查更安全)

        center_is_22 = (class_array == 22)
        mean_is_valid = ~mean_mask_invalid

        # 综合掩码
        valid_analysis_mask = center_is_22 & mean_is_valid

        # 进一步筛选：邻域内必须有 31, 32 或 33 (原代码逻辑: if (n31+n32+n33)==0: continue)
        neighbor_has_target = (n31_map + n32_map + n33_map) > 0
        final_mask = valid_analysis_mask & neighbor_has_target

        # 获取所有满足条件的像素索引
        rows, cols = np.where(final_mask)

        if len(rows) == 0:
            print(f"  -> 警告：{prefix} 未找到符合条件的记录。")
            continue

        print(f"  -> 找到 {len(rows)} 个有效样本点，正在提取数值...")

        # 5. 向量化提取邻域均值
        # 原代码逻辑：对于每个点，取其 3x3 窗口，分别计算窗口内类别为 31,32...66 的 mean 值的平均数

        # 为了效率，我们不能对每个点切片。我们需要构建所有点的窗口视图。
        # 但由于不同类别的分布是稀疏的，且类别较多 (31-33, 61-66)，
        # 我们可以采用“广播”或“步进”策略。
        # 这里使用一种通用的滑动窗口提取方法 (strides)，但考虑到内存，我们分块或直接计算。

        # 优化策略：
        # 我们只需要计算那些 final_mask 为 True 的位置。
        # 对于这些位置，我们需要提取它们周围 3x3 的 mean_array 值和 class_array 值。

        # 准备存储结果的列表
        batch_data = []

        # 定义需要计算的类别列表
        target_classes = [31, 32, 33, 61, 62, 63, 64, 65, 66]

        # 由于 Python 循环在大量数据下仍慢，我们尝试完全向量化。
        # 构造偏移量
        offsets = [(-1, -1), (-1, 0), (-1, 1),
                   (0, -1), (0, 0), (0, 1),
                   (1, -1), (1, 0), (1, 1)]

        # 预分配结果数组
        num_points = len(rows)
        res_n31 = n31_map[rows, cols]
        res_n32 = n32_map[rows, cols]
        res_n33 = n33_map[rows, cols]
        res_mean_val = mean_array[rows, cols]

        # 初始化结果字典的列
        result_dict = {
            'row': rows,
            'col': cols,
            'n31': res_n31,
            'n32': res_n32,
            'n33': res_n33,
            f'{prefix}_value': res_mean_val
        }

        for cls in target_classes:
            result_dict[f'{prefix}_{cls}'] = np.zeros(num_points, dtype=np.float32)

        # 核心向量化逻辑：
        # 对于每个偏移量 (dr, dc)，提取 shifted_mean 和 shifted_class
        # 然后累加到对应类别的和中，并计数。

        sum_vals = {cls: np.zeros(num_points, dtype=np.float64) for cls in target_classes}
        count_vals = {cls: np.zeros(num_points, dtype=np.int32) for cls in target_classes}

        for dr, dc in offsets:
            # 计算偏移后的坐标
            r_shifted = rows + dr
            c_shifted = cols + dc

            # 处理边界：超出边界的索引设为 -1 (或其他无效索引，稍后掩码)
            # 但 numpy 高级索引不支持自动忽略越界，我们需要手动掩码
            valid_shift_mask = (r_shifted >= 0) & (r_shifted < height) & \
                               (c_shifted >= 0) & (c_shifted < width)

            if not np.any(valid_shift_mask):
                continue

            r_valid = r_shifted[valid_shift_mask]
            c_valid = c_shifted[valid_shift_mask]
            idx_valid = np.where(valid_shift_mask)[0]  # 原始结果数组中的索引

            # 提取值
            shifted_mean = mean_array[r_valid, c_valid]
            shifted_class = class_array[r_valid, c_valid]

            # 检查 mean 是否有效 (排除 nodata)
            mean_valid_mask = (shifted_mean != nodata_val) & (shifted_mean >= 0)

            # 合并有效掩码
            final_shift_mask = mean_valid_mask
            if not np.any(final_shift_mask):
                continue

            r_final = r_valid[final_shift_mask]
            c_final = c_valid[final_shift_mask]
            idx_final = idx_valid[final_shift_mask]

            m_vals = shifted_mean[final_shift_mask]
            c_vals = shifted_class[final_shift_mask]

            # 对每个目标类别进行累加
            for cls in target_classes:
                class_match = (c_vals == cls)
                if np.any(class_match):
                    sum_vals[cls][idx_final[class_match]] += m_vals[class_match]
                    count_vals[cls][idx_final[class_match]] += 1

        # 计算均值 (避免除以零)
        for cls in target_classes:
            counts = count_vals[cls]
            means = np.divide(sum_vals[cls], counts, out=np.zeros_like(sum_vals[cls]), where=counts != 0)
            result_dict[f'{prefix}_{cls}'] = means

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
# 注意：原代码中的 resampled_source_path (_FINAL.tif) 不再需要生成，我们在内存中处理

# 多个 mean 文件的配置
mean_config = [
    (r'D:\MODIS43A4_2024\SOS2\masked2_masked_all_SoS_DOY_2023_masked_tibet.tif', 'sos'),
    (r'D:\MODIS43A4_2024\POS2\\masked2_masked_all_PoS_DOY_2023_masked_tibet.tif', 'pos'),
    (r'D:\MODIS43A4_2024\EOS2\masked2_masked_all_EoS_DOY_2023_masked_tibet.tif', 'eos'),
]

output_excel_path = r'D:\MODIS43A4_2024\combined_output1.xlsx'

if __name__ == "__main__":
    # 执行处理
    process_data_fast(mean_config, source_raster_path, output_excel_path)