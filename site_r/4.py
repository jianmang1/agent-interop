import os
import rasterio
import numpy as np
from scipy.stats import linregress

# 定义文件路径
directory = r'F:\MODIS43A4_DOY\LOS'
years = list(range(2001, 2024))  # 年份列表
# 创建一个文件路径列表，匹配文件名模式为 all_SoS_value_<year>_masked.tif
files = [os.path.join(directory, f) for f in os.listdir(directory) if
         any(f == f'difference_{year}.tif' for year in years)]
files_direct = [os.path.join(directory, f'difference_{year}.tif') for year in years if os.path.exists(os.path.join(directory, f'difference_{year}.tif'))]

# 检查文件数量是否正确
if len(files) != len(years):
    raise ValueError("文件数量与年份数量不匹配")

# 初始化一个空列表存储数据
data = []

for file in files:
    with rasterio.open(file) as src:
        data.append(src.read(1))

# 将列表转换为numpy数组以便操作
data_array = np.array(data)

# 初始化输出数组
mean_values = np.zeros_like(data_array[0], dtype=np.float32)
rmse_values = np.zeros_like(data_array[0], dtype=np.float32)
slope_values = np.zeros_like(data_array[0], dtype=np.float32)
p_values = np.zeros_like(data_array[0], dtype=np.float32)

# 遍历每个像素点
for i in range(data_array.shape[1]):
    for j in range(data_array.shape[2]):
        pixel_values = data_array[:, i, j]

        # 创建一个布尔掩码，表示哪些位置的数据是有效的（即不是NaN）
        valid_mask = ~np.isnan(pixel_values)

        # 确保 years 和 pixel_values 的有效部分长度一致
        valid_years = np.array(years)[valid_mask]
        valid_pixel_values = pixel_values[valid_mask]

        if len(valid_years) > 1:  # 至少有两个有效点才能计算线性回归
            slope, intercept, r_value, p_value, std_err = linregress(valid_years, valid_pixel_values)
            slope_values[i, j] = slope
            p_values[i, j] = p_value

        # 计算平均值和 RMSE
        if len(valid_pixel_values) > 0:
            mean_values[i, j] = np.mean(valid_pixel_values)
            rmse_values[i, j] = np.sqrt(np.mean((valid_pixel_values - mean_values[i, j]) ** 2))
        else:
            mean_values[i, j] = np.nan
            rmse_values[i, j] = np.nan

# 保存结果
# 使用第一个文件的信息创建输出文件
with rasterio.open(files[0]) as src:
    profile = src.profile

profile.update(dtype=rasterio.float32)

# 保存平均值
with rasterio.open(os.path.join(directory, 'mean_values.tif'), 'w', **profile) as dst:
    dst.write(mean_values, 1)

# 保存RMSE
with rasterio.open(os.path.join(directory, 'rmse_values.tif'), 'w', **profile) as dst:
    dst.write(rmse_values, 1)

# 保存斜率
with rasterio.open(os.path.join(directory, 'slope_values.tif'), 'w', **profile) as dst:
    dst.write(slope_values, 1)

# 保存P值
with rasterio.open(os.path.join(directory, 'p_values.tif'), 'w', **profile) as dst:
    dst.write(p_values, 1)