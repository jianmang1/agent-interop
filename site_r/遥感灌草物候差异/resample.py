import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
import pandas as pd


def resample_raster(source_path, target_path, output_path):
    """将源栅格重采样到目标栅格的空间参考系统"""
    with rasterio.open(target_path) as target:
        target_profile = target.profile.copy()
        target_crs = target.crs
        target_transform = target.transform
        target_width = target.width
        target_height = target.height

    with rasterio.open(source_path) as source:
        # 创建新数据数组
        data = source.read(1)
        resampled_data = np.zeros((target_height, target_width), dtype=source.dtypes[0])

        # 执行重投影和重采样
        reproject(
            source=data,
            destination=resampled_data,
            src_transform=source.transform,
            src_crs=source.crs,
            dst_transform=target_transform,
            dst_crs=target_crs,
            resampling=Resampling.nearest  # 分类数据用最近邻法
        )

        # 保存重采样结果
        with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=target_height,
                width=target_width,
                count=1,
                dtype=source.dtypes[0],
                crs=target_crs,
                transform=target_transform,
                nodata=-9999  # 设置无效值为 -9999
        ) as dst:
            dst.write(resampled_data, 1)


# 路径配置
source_raster_path = r'F:\个人\CLASS\新建文件夹\中科院_mode_resampled_clipped.tif'
mean_raster_path = r'D:\MODIS43A4_2024\SOS\mean_values.tif'
resampled_source_path = r'F:\个人\CLASS\新建文件夹\中科院_mode_resampled_clipped_FINAL.tif'  # 重采样后文件
output_excel_path = r'D:\MODIS43A4_2024\SOS\output.xlsx'

# 步骤1：执行重采样
print("正在重采样源栅格...")
resample_raster(source_raster_path, mean_raster_path, resampled_source_path)
print("重采样完成，保存至:", resampled_source_path)


# 步骤2：执行原分析流程（修改版）
def process_data():
    with rasterio.open(resampled_source_path) as src, \
            rasterio.open(mean_raster_path) as mean_src:

        # 双重验证空间一致性
        if src.shape != mean_src.shape:
            raise ValueError(f"栅格尺寸不一致 源: {src.shape} vs 目标: {mean_src.shape}")
        if src.crs != mean_src.crs:
            raise ValueError(f"CRS不一致 源: {src.crs} vs 目标: {mean_src.crs}")

        src_array = src.read(1)
        mean_array = mean_src.read(1)

        # 过滤无效值
        src_array[src_array < 0] = -9999  # 将所有负值设为无效值
        mean_array[mean_array < 0] = -9999

        rows, cols = np.where((src_array == 22) & (mean_array != -9999))  # 确保有效值参与计算
        data = []

        for row, col in zip(rows, cols):
            # 3x3邻域范围计算
            min_row = max(0, row - 1)
            max_row = min(src.height - 1, row + 1)
            min_col = max(0, col - 1)
            max_col = min(src.width - 1, col + 1)

            # 邻域统计
            window = src_array[min_row:max_row + 1, min_col:max_col + 1]
            n31 = np.count_nonzero(window == 31)
            n32 = np.count_nonzero(window == 32)
            n33 = np.count_nonzero(window == 33)

            if (n31 + n32 + n33) == 0:
                continue

            # 获取对应值
            sos22 = mean_array[row, col]

            # 计算邻域均值（优化版）
            def calc_mean(value):
                mask = (window == value) & (mean_array[min_row:max_row + 1, min_col:max_col + 1] != -9999)
                return mean_array[min_row:max_row + 1, min_col:max_col + 1][mask].mean() if mask.any() else 0.0

            sos31 = calc_mean(31)
            sos32 = calc_mean(32)
            sos33 = calc_mean(33)

            data.append([n31, n32, n33, sos22, sos31, sos32, sos33])

    if data:
        df = pd.DataFrame(data, columns=['n31', 'n32', 'n33', 'sos22', 'sos31', 'sos32', 'sos33'])
        df.to_excel(output_excel_path, index=False)
        print(f"分析完成，结果保存至: {output_excel_path}")
    else:
        print("未找到符合条件的记录")


print("开始数据分析...")
process_data()