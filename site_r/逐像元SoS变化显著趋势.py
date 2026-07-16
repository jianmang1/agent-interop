import os
import rasterio
import numpy as np
from scipy.stats import linregress

# 定义文件路径
directory = r'D:\MODIS43A4_2024\SOS2_aligned'
years = list(range(2001, 2025))  # 年份列表

# 创建一个文件路径列表，匹配文件名模式为 all_SoS_value_<year>_masked.tif
files_direct = [os.path.join(directory, f'masked2_masked_all_SoS_DOY_{year}_aligned.tif') for year in years if
                os.path.exists(os.path.join(directory, f'masked2_masked_all_SoS_DOY_{year}_aligned.tif'))]
print(files_direct)

# 检查文件数量是否正确
if len(files_direct) != len(years):
    raise ValueError("文件数量与年份数量不匹配")

# 初始化一个空列表存储数据
data = []

for file in files_direct:
    with rasterio.open(file) as src:
        data.append(src.read(1))

# 将列表转换为numpy数组以便操作
data_array = np.array(data)

# 初始化输出数组
height, width = data_array.shape[1], data_array.shape[2]
mean_values = np.full((height, width), np.nan, dtype=np.float32)
rmse_values = np.full((height, width), np.nan, dtype=np.float32)
slope_values = np.full((height, width), np.nan, dtype=np.float32)
p_values = np.full((height, width), np.nan, dtype=np.float32)

# 向量化计算，提高运算速度
years_array = np.array(years)

# 获取有效的像素位置掩码
valid_mask = ~np.isnan(data_array)
n_valid = np.sum(valid_mask, axis=0)  # 每个像素位置的有效年份数量

# 计算平均值
valid_data_sum = np.nansum(data_array, axis=0)
valid_count = np.sum(~np.isnan(data_array), axis=0)
mean_values = np.divide(valid_data_sum, valid_count, out=np.full_like(valid_data_sum, np.nan), where=valid_count > 0)

# 计算RMSE
squared_diff = np.where(np.isnan(data_array), 0, (data_array - mean_values) ** 2)
rmse_values = np.sqrt(np.divide(np.nansum(squared_diff, axis=0), valid_count, out=np.full_like(squared_diff[0], np.nan),
                                where=valid_count > 0))


# 计算线性回归（仅对有效点数量大于1的像素）
# 使用向量化方式计算斜率和p值
def calculate_slope_pvalue_batch(data_array, years_array, valid_mask):
    height, width = data_array.shape[1], data_array.shape[2]
    slopes = np.full((height, width), np.nan, dtype=np.float32)
    p_values = np.full((height, width), np.nan, dtype=np.float32)

    # 获取有效点数量大于1的位置
    valid_positions = n_valid > 1

    if np.any(valid_positions):
        # 获取有效点位置的坐标
        valid_rows, valid_cols = np.where(valid_positions)

        # 批量处理有效位置
        for row, col in zip(valid_rows, valid_cols):
            pixel_values = data_array[:, row, col]
            valid_mask_pixel = ~np.isnan(pixel_values)

            if np.sum(valid_mask_pixel) > 1:
                valid_years = years_array[valid_mask_pixel]
                valid_pixel_values = pixel_values[valid_mask_pixel]

                if len(valid_years) > 1:
                    slope, intercept, r_value, p_value, std_err = linregress(valid_years, valid_pixel_values)
                    slopes[row, col] = slope
                    p_values[row, col] = p_value

    return slopes, p_values


# 计算斜率和p值
slope_values, p_values = calculate_slope_pvalue_batch(data_array, years_array, valid_mask)

# 保存结果
# 使用第一个文件的信息创建输出文件
with rasterio.open(files_direct[0]) as src:
    profile = src.profile

profile.update(dtype=rasterio.float32)

# 保存平均值
with rasterio.open(os.path.join(directory, 'mean_values.tif'), 'w', **profile) as dst:
    dst.write(mean_values, 1)



print("处理完成，结果已保存到对应文件")



