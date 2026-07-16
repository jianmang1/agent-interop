import os
import rasterio
import numpy as np
from scipy.stats import linregress

# 定义文件路径
directory = r'D:\MODIS43A4_2024\LOS'
years = list(range(2001, 2025))  # 年份列表
print(years)
files_direct = [os.path.join(directory, f'LOS_{year}.tif') for year in years if
                os.path.exists(os.path.join(directory, f'LOS_{year}.tif'))]

print(files_direct)

# 检查文件数量是否正确
if len(files_direct) != len(years):
    raise ValueError("文件数量与年份数量不匹配")

# 使用第一个文件来获取元信息
with rasterio.open(files_direct[0]) as src:
    profile = src.profile
    windows = [window for _, window in src.block_windows()]

# 初始化输出数组的模板
mean_values_template = np.zeros((profile['height'], profile['width']), dtype=np.float32)
rmse_values_template = np.zeros_like(mean_values_template)
slope_values_template = np.zeros_like(mean_values_template)
p_values_template = np.zeros_like(mean_values_template)

for window in windows:
    data = []
    for file in files_direct:
        with rasterio.open(file) as src:
            band = src.read(1, window=window).astype(np.float32)
            # 将 -9999 转换为 NaN
            band = np.where(band == -9999, np.nan, band)
            data.append(band)

    data_array = np.array(data)

    mean_values = np.zeros_like(data_array[0], dtype=np.float32)
    rmse_values = np.zeros_like(data_array[0], dtype=np.float32)
    slope_values = np.zeros_like(data_array[0], dtype=np.float32)
    p_values = np.zeros_like(data_array[0], dtype=np.float32)

    for i in range(data_array.shape[1]):
        for j in range(data_array.shape[2]):
            pixel_values = data_array[:, i, j]
            valid_mask = ~np.isnan(pixel_values)
            valid_years = np.array(years)[valid_mask]
            valid_pixel_values = pixel_values[valid_mask]

            if len(valid_years) > 1:
                slope, intercept, r_value, p_value, std_err = linregress(valid_years, valid_pixel_values)
                slope_values[i, j] = slope
                p_values[i, j] = p_value

            if len(valid_pixel_values) > 0:
                mean_values[i, j] = np.mean(valid_pixel_values)
                rmse_values[i, j] = np.sqrt(np.mean((valid_pixel_values - mean_values[i, j]) ** 2))
            else:
                mean_values[i, j] = np.nan
                rmse_values[i, j] = np.nan

    mean_values = np.where(np.isnan(mean_values), -9999.0, mean_values).astype(np.float32)
    rmse_values = np.where(np.isnan(rmse_values), -9999.0, rmse_values).astype(np.float32)
    slope_values = np.where(np.isnan(slope_values), -9999.0, slope_values).astype(np.float32)
    p_values = np.where(np.isnan(p_values), -9999.0, p_values).astype(np.float32)

    # 更新对应窗口位置的结果
    mean_values_template[window.row_off:window.row_off + window.height,
    window.col_off:window.col_off + window.width] = mean_values
    rmse_values_template[window.row_off:window.row_off + window.height,
    window.col_off:window.col_off + window.width] = rmse_values
    slope_values_template[window.row_off:window.row_off + window.height,
    window.col_off:window.col_off + window.width] = slope_values
    p_values_template[window.row_off:window.row_off + window.height,
    window.col_off:window.col_off + window.width] = p_values

# 更新 nodata 属性
profile.update(dtype=rasterio.float32, nodata=-9999.0)

# 保存结果
with rasterio.open(os.path.join(directory, 'mean_values.tif'), 'w', **profile) as dst:
    dst.write(mean_values_template, 1)

with rasterio.open(os.path.join(directory, 'std_values.tif'), 'w', **profile) as dst:
    dst.write(rmse_values_template, 1)

with rasterio.open(os.path.join(directory, 'slope_values.tif'), 'w', **profile) as dst:
    dst.write(slope_values_template, 1)

with rasterio.open(os.path.join(directory, 'p_values.tif'), 'w', **profile) as dst:
    dst.write(p_values_template, 1)



