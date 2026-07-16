import os
import numpy as np
from osgeo import gdal
import pandas as pd


# 定义函数读取栅格数据
def read_raster(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ds = gdal.Open(file_path)
    if ds is None:
        raise RuntimeError(f"Failed to open file: {file_path}")

    band = ds.GetRasterBand(1)
    data = band.ReadAsArray().astype(np.float32)  # 确保数据类型为 float32
    return data, ds.RasterXSize, ds.RasterYSize, ds.GetGeoTransform(), ds.GetProjection()


# 定义重采样函数
def resample_raster(src_file, dst_file, dst_x_size, dst_y_size, dst_geo_transform, dst_projection,
                    method=gdal.GRA_Average):
    options = gdal.WarpOptions(format='GTiff', width=dst_x_size, height=dst_y_size,
                               outputBounds=[dst_geo_transform[0],
                                             dst_geo_transform[3] + dst_y_size * dst_geo_transform[5],
                                             dst_geo_transform[0] + dst_x_size * dst_geo_transform[1],
                                             dst_geo_transform[3]],
                               dstSRS=dst_projection, resampleAlg=method)
    gdal.Warp(dst_file, src_file, options=options)
    return read_raster(dst_file)[0]


# 读取EVI文件
evi_file = 'F:\个人\SOS\\allplant\evi_cubicfitting_1_threshold__SoS_doy_2021.tif'
print(f"Reading EVI data from: {evi_file}")
evi_data, evi_x_size, evi_y_size, evi_geo_transform, evi_projection = read_raster(evi_file)

# 读取分块的草覆盖度数据
grassland_dir = 'F:\个人\grasslandcover\masked_veg'
grassland_files = [os.path.join(grassland_dir, f) for f in os.listdir(grassland_dir) if
                   f.startswith('grassland_cc_') and f.endswith('.tif')]

# 初始化存储结果的字典
results = {'coverage': [], 'means': [], 'stds': [], 'pixel_counts': []}

# 处理每个分块文件
for grassland_file in grassland_files:
    print(f"Reading and resampling grassland cover data from: {grassland_file}")

    # 临时文件路径
    temp_file = os.path.join(grassland_dir, 'temp_resampled.tif')

    # 读取草覆盖度数据
    grassland_data, _, _, _, _ = read_raster(grassland_file)

    # 重采样草覆盖度数据到EVI文件的分辨率
    grassland_data_resampled = resample_raster(grassland_file, temp_file, evi_x_size, evi_y_size, evi_geo_transform,
                                               evi_projection)

    # 对于0到100之间的每个值计算EVI统计信息
    for coverage_value in range(101):  # 包括0和100
        mask_chunk = (grassland_data_resampled == coverage_value)
        grassland_values = grassland_data_resampled[mask_chunk].flatten()

        if len(grassland_values) > 0:
            evi_values = evi_data[mask_chunk].flatten()

            if len(evi_values) > 0:
                evi_values = np.array(evi_values)
                evi_values = evi_values[np.isfinite(evi_values)]

                if len(evi_values) > 0:
                    mean_evi = np.mean(evi_values)
                    std_evi = np.std(evi_values)

                    # 存储结果
                    results['coverage'].append(coverage_value)
                    results['means'].append(mean_evi)
                    results['stds'].append(std_evi)
                    results['pixel_counts'].append(len(evi_values))

# 输出到Excel
excel_file = 'F:\\个人\\ALLsos_results1.xlsx'
writer = pd.ExcelWriter(excel_file, engine='openpyxl')

# 创建DataFrame
df = pd.DataFrame({
    'Coverage Value': results['coverage'],
    'Mean EVI': results['means'],
    'Std EVI': results['stds'],
    'Pixel Count': results['pixel_counts']
})

# 写入Excel
df.to_excel(writer, sheet_name='Results', index=False)

# 保存Excel文件
writer.close()
print(f"Results exported to: {excel_file}")

# 删除临时文件
if os.path.exists(temp_file):
    os.remove(temp_file)