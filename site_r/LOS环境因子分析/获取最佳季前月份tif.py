import numpy as np
from osgeo import gdal
import glob
import os

# 定义基础路径和变量
base_path = r'I:\output\SOS_climate_pcorr'
climate_vars = ['SOS_ppt', 'SOS_soil', 'SOS_srad', 'SOS_tmax', 'SOS_tmin', 'SOS_vpd']  # 气候变量列表
preseason_months = 3  # 季前月数
sos_path = r'I:\SOS1\resampled_mean_values.tif'  # 物候数据路径


def Tifoutput(data, outpath, reference_path):
    """保存栅格图像"""
    if data.size == 0 or data.shape[0] == 0 or data.shape[1] == 0:
        print(f"警告: 数据数组为空，无法创建栅格文件: {outpath}")
        return

    # 打开参考栅格以获取投影和地理变换信息
    ref_tif = gdal.Open(reference_path)
    if ref_tif is None:
        print(f"错误: 无法打开参考栅格文件: {reference_path}")
        return

    gtiff_driver = gdal.GetDriverByName('GTiff')
    out_tif = gtiff_driver.Create(
        outpath,
        data.shape[1],
        data.shape[0],
        1,
        gdal.GDT_Float32
    )

    if out_tif is None:
        print(f"错误: 无法创建输出栅格文件: {outpath}")
        ref_tif = None
        return

    out_tif.SetProjection(ref_tif.GetProjection())
    out_tif.SetGeoTransform(ref_tif.GetGeoTransform())
    out_band = out_tif.GetRasterBand(1)
    out_band.WriteArray(data)
    out_band.FlushCache()

    # 释放资源
    out_band = None
    out_tif = None
    ref_tif = None


def read_raster(file_path):
    """读取栅格数据"""
    raster = gdal.Open(file_path)
    if raster is None:
        print(f"警告: 无法打开文件 {file_path}")
        return None
    return raster.GetRasterBand(1).ReadAsArray().astype(np.float32)


def find_best_preseason(data_list, mask):
    """为每个像元找到最佳季前月份"""
    best_month = np.full_like(mask, -1000.0)
    height, width = mask.shape

    for i in range(height):
        for j in range(width):
            if mask[i][j] > 0 and not np.isnan(mask[i][j]):  # 只处理有效物候像元
                max_corr = -np.inf
                best_m = -1

                # 遍历所有季前月份
                for m, data in enumerate(data_list):
                    # 遍历所有气候变量，找到该像元在当前季前月份的最大相关系数
                    current_max_corr = -np.inf
                    for var in climate_vars:
                        if data[var] is not None and i < data[var].shape[0] and j < data[var].shape[1]:
                            corr_value = data[var][i][j]
                            if not np.isnan(corr_value) and abs(corr_value) > current_max_corr:
                                current_max_corr = abs(corr_value)

                    # 比较当前季前月份的最大相关系数与全局最大值
                    if current_max_corr > max_corr:
                        max_corr = current_max_corr
                        best_m = m + 1

                best_month[i][j] = best_m if best_m > 0 else np.nan

    return np.where(best_month == -1000, np.nan, best_month)


# 读取物候数据作为掩膜
print("正在读取物候数据...")
sos_raster = gdal.Open(sos_path)
if sos_raster is None:
    raise FileNotFoundError(f"无法找到物候数据文件: {sos_path}")

sos_data = sos_raster.GetRasterBand(1).ReadAsArray().astype(np.float32)
sos_height, sos_width = sos_data.shape
print(f"物候数据尺寸: {sos_height} x {sos_width}")

# 获取参考栅格文件路径（从preseason_1文件夹中获取一个文件作为参考）
reference_file_pattern = os.path.join(base_path, 'preseason_1', '*.tif')
reference_files = glob.glob(reference_file_pattern)
if not reference_files:
    raise FileNotFoundError(f"在 {os.path.join(base_path, 'preseason_1')} 中未找到任何TIF文件作为参考")

reference_file = reference_files[0]  # 使用第一个找到的文件作为参考
print(f"使用参考栅格文件: {reference_file}")

print("正在读取所有季前月份的气候变量数据...")
data_per_preseason = []

# 遍历每个季前月，读取数据
for month in range(1, preseason_months + 1):
    data_per_var = {}
    for var in climate_vars:
        file_path = os.path.join(base_path, f'preseason_{month}', f'{var}_pcorr.tif')
        data_per_var[var] = read_raster(file_path)
    data_per_preseason.append(data_per_var)

# 检查是否有数据加载失败
all_data_loaded = True
for data in data_per_preseason:
    for var_data in data.values():
        if var_data is None:
            all_data_loaded = False
            break
    if not all_data_loaded:
        break

if not all_data_loaded:
    print("错误: 部分数据未能加载，程序终止...")
    exit(1)

# 检查数据形状是否一致
first_shape = None
for data in data_per_preseason:
    for var_data in data.values():
        if var_data is not None:
            if first_shape is None:
                first_shape = var_data.shape
            elif var_data.shape != first_shape:
                print(f"警告: 数据形状不一致 {var_data.shape} vs {first_shape}")
                all_data_loaded = False
                break
    if not all_data_loaded:
        break

if not all_data_loaded:
    print("错误: 数据形状不一致，程序终止...")
    exit(1)

print(f"所有气候变量数据形状: {first_shape}")

# 找到最佳季前月份
print("正在计算最佳季前月份...")
best_month_data = find_best_preseason(data_per_preseason, sos_data)

# 检查结果数据是否有效
if best_month_data.size == 0:
    print("错误: 最佳季前月份数据为空，程序终止...")
    exit(1)

# 输出结果
outfile = os.path.join(base_path, 'best_month_complete')
if not os.path.exists(outfile):
    os.makedirs(outfile)

output_file = os.path.join(outfile, 'best_month_complete.tif')

# 保存结果
Tifoutput(best_month_data, output_file, reference_file)
print(f'最佳季前月份结果已保存至: {output_file}')

print("处理完成！")



