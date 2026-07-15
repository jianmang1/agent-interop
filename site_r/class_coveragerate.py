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

# 读取土地利用数据
land_file = 'F:\\个人\\CLASS\\ioa_class1_resampled_exported.tif'
print(f"Reading land use data from: {land_file}")
if not os.path.exists(land_file):
    raise FileNotFoundError(f"Land use file not found: {land_file}")
land_data, land_x_size, land_y_size, land_geo_transform, land_projection = read_raster(land_file)

# 找到特定值的像元位置
values_to_extract = [21, 22, 23, 24, 31, 32, 33, 61, 62, 63, 64, 65,66,67]

# 初始化存储结果的字典
results = {value: {'means': [], 'stds': [], 'min_values': [], 'q1_values': [], 'medians': [], 'q3_values': [], 'max_values': [], 'values': [], 'pixel_counts': []} for value in values_to_extract}

# 读取分块的草覆盖度数据
grassland_dir = 'F:\\个人\\grasslandcover\\masked_veg'
grassland_files = [os.path.join(grassland_dir, f) for f in os.listdir(grassland_dir) if f.startswith('grassland_cc_') and f.endswith('.tif')]

# 定义重采样函数
def resample_raster(src_file, dst_file, dst_x_size, dst_y_size, dst_geo_transform, dst_projection, method=gdal.GRA_Average):
    options = gdal.WarpOptions(format='GTiff', width=dst_x_size, height=dst_y_size,
                               outputBounds=[dst_geo_transform[0],
                                             dst_geo_transform[3] + dst_y_size * dst_geo_transform[5],
                                             dst_geo_transform[0] + dst_x_size * dst_geo_transform[1],
                                             dst_geo_transform[3]],
                               dstSRS=dst_projection, resampleAlg=method)
    gdal.Warp(dst_file, src_file, options=options)
    return read_raster(dst_file)[0]

# 处理每个分块文件
for grassland_file in grassland_files:
    print(f"Reading and resampling grassland cover data from: {grassland_file}")

    # 临时文件路径
    temp_file = os.path.join(grassland_dir, 'temp_resampled.tif')

    # 重采样
    grassland_data = resample_raster(grassland_file, temp_file, land_x_size, land_y_size, land_geo_transform, land_projection)

    # 对每个特定值进行处理
    for value in values_to_extract:
        mask_chunk = (land_data == value)
        grassland_values = grassland_data[mask_chunk].flatten()

        if len(grassland_values) > 0:
            # 过滤掉 NaN、无穷大值和无效像元（值为255）
            valid_values = grassland_values[(np.isfinite(grassland_values)) & (grassland_values != 255)]

            if len(valid_values) > 0:
                # 计算统计量
                mean_grassland = np.mean(valid_values)
                std_grassland = np.std(valid_values)
                min_value = np.min(valid_values)
                q1_value = np.percentile(valid_values, 25)
                median_value = np.median(valid_values)
                q3_value = np.percentile(valid_values, 75)
                max_value = np.max(valid_values)

                # 存储结果
                results[value]['means'].append(mean_grassland)
                results[value]['stds'].append(std_grassland)
                results[value]['min_values'].append(min_value)
                results[value]['q1_values'].append(q1_value)
                results[value]['medians'].append(median_value)
                results[value]['q3_values'].append(q3_value)
                results[value]['max_values'].append(max_value)
                results[value]['values'].extend(valid_values)
                results[value]['pixel_counts'].append(len(valid_values))

# 输出到Excel
excel_file = 'F:\\个人\\grassland_cover_results.xlsx'
writer = pd.ExcelWriter(excel_file, engine='openpyxl')

for value in values_to_extract:
    if results[value]['values']:
        means = results[value]['means']
        stds = results[value]['stds']
        min_values = results[value]['min_values']
        q1_values = results[value]['q1_values']
        medians = results[value]['medians']
        q3_values = results[value]['q3_values']
        max_values = results[value]['max_values']
        pixel_counts = results[value]['pixel_counts']

        # 创建DataFrame
        df = pd.DataFrame({
            'Mean Grassland Cover': means,
            'Std Grassland Cover': stds,
            'Min Value': min_values,
            'Q1 Value': q1_values,
            'Median Value': medians,
            'Q3 Value': q3_values,
            'Max Value': max_values,
            'Pixel Count': pixel_counts
        })

        # 写入Excel
        sheet_name = f'Value_{value}'
        df.to_excel(writer, sheet_name=sheet_name, index=False)

# 保存Excel文件
writer.close()
print(f"Results exported to: {excel_file}")

# 删除临时文件
if os.path.exists(temp_file):
    os.remove(temp_file)