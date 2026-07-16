import os
import numpy as np
from osgeo import gdal
from scipy.stats import norm, lognorm, gamma
import matplotlib.pyplot as plt

import matplotlib.pyplot as plt
from scipy.stats import norm, lognorm, gamma
# 定义函数读取栅格数据
def read_raster(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ds = gdal.Open(file_path)
    if ds is None:
        raise RuntimeError(f"Failed to open file: {file_path}")

    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    return data, ds.RasterXSize, ds.RasterYSize

# 读取重采样的土地利用数据
resampled_land_file = r'F:\个人\CLASS\新建文件夹\中科院_mode_resampled_clipped.tif'
print(f"Reading resampled land use data from: {resampled_land_file}")
resampled_land_data, x_size, y_size = read_raster(resampled_land_file)

# 找到特定值的像元位置
values_to_extract = [21, 22, 23, 24, 31, 32, 33, 61, 62, 63, 64, 65,66,67]

# 定义块大小
chunk_size = 1000  # 根据你的内存情况调整这个值

# 初始化存储结果的字典
results = {value: {} for value in values_to_extract}

# 循环读取EVI数据
for year in range(2001, 2024):
    evi_file = f'F:\MODIS43A4_DOY\SOS\mask_applied_masked_all_SoS_value_{year}.tif'
    print(f"Reading EVI data for year {year} from: {evi_file}")

    try:
        evi_data, _, _ = read_raster(evi_file)
    except Exception as e:
        print(f"Error reading EVI data for year {year}: {e}")
        continue  # 跳过无法读取的年份

    # 分块处理
    for y in range(0, y_size, chunk_size):
        for x in range(0, x_size, chunk_size):
            end_y = min(y + chunk_size, y_size)
            end_x = min(x + chunk_size, x_size)

            # 提取当前块的数据
            land_chunk = resampled_land_data[y:end_y, x:end_x]
            evi_chunk = evi_data[y:end_y, x:end_x]

            # 确保两个块的形状一致
            if land_chunk.shape != evi_chunk.shape:
                raise ValueError(f"Shapes do not match: land_chunk {land_chunk.shape}, evi_chunk {evi_chunk.shape}")

            # 对于每个土地利用类型，应用掩码提取特定像元的EVI值，并排除无效值 -9999
            for value in values_to_extract:
                mask_chunk = (land_chunk == value) & (evi_chunk != -9999)
                evi_values = evi_chunk[mask_chunk].flatten()

                if len(evi_values) > 0:
                    # 过滤掉 NaN 和无穷大值
                    evi_values = np.array(evi_values)
                    evi_values = evi_values[np.isfinite(evi_values)]

                    if len(evi_values) > 0:
                        # 计算统计量
                        mean_evi = np.mean(evi_values)
                        std_evi = np.std(evi_values)
                        min_evi = np.min(evi_values)
                        q1_evi = np.percentile(evi_values, 25)
                        median_evi = np.median(evi_values)
                        q3_evi = np.percentile(evi_values, 75)
                        max_evi = np.max(evi_values)

                        # 存储结果
                        if year not in results[value]:
                            results[value][year] = {
                                'mean': mean_evi,
                                'std': std_evi,
                                'min': min_evi,
                                'q1': q1_evi,
                                'median': median_evi,
                                'q3': q3_evi,
                                'max': max_evi,
                                'values': evi_values.tolist()
                            }
                        else:
                            results[value][year]['mean'] = mean_evi
                            results[value][year]['std'] = std_evi
                            results[value][year]['min'] = min_evi
                            results[value][year]['q1'] = q1_evi
                            results[value][year]['median'] = median_evi
                            results[value][year]['q3'] = q3_evi
                            results[value][year]['max'] = max_evi
                            results[value][year]['values'].extend(evi_values.tolist())


# 假设 results 已经通过上述代码填充好了
value =22
output_dir = 'F:\\MODIS43A4_DOY\\SOS\\EVI_Distribution_Plots22'
os.makedirs(output_dir, exist_ok=True)

# 遍历2001年至2023年
for year in range(2001, 2024):
    # 获取指定年份Value_21的EVI值
    if year not in results[value]:
        print(f"No EVI values found for Value_{value} in {year}.")
        continue  # 跳过没有数据的年份

    evi_values = results[value][year]['values']

    # 如果没有EVI值，则无法继续
    if not evi_values:
        print(f"No EVI values found for Value_{value} in {year}.")
        continue

    # 将列表转换为numpy数组
    evi_values = np.array(evi_values)

    # 拟合正态分布
    mu, std = norm.fit(evi_values)
    # 拟合对数正态分布
    shape, loc, scale = lognorm.fit(evi_values, floc=0)
    # 拟合伽玛分布
    a, loc, scale = gamma.fit(evi_values, floc=0)

    # 绘制直方图
    plt.figure(figsize=(10, 6))
    plt.hist(evi_values, bins=50, density=True, alpha=0.6, color='g')

    # 绘制拟合的分布曲线
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    p_norm = norm.pdf(x, mu, std)
    p_lognorm = lognorm.pdf(x, shape, loc, scale)
    p_gamma = gamma.pdf(x, a, loc, scale)

    plt.plot(x, p_norm, 'k', linewidth=2, label="Norm Fit")
    plt.plot(x, p_lognorm, 'r--', linewidth=2, label="LogNorm Fit")
    plt.plot(x, p_gamma, 'b-.', linewidth=2, label="Gamma Fit")

    # 添加标题和标签
    plt.title(f'Probability Distribution of EVI for Value_{value} in {year}')
    plt.xlabel('EVI')
    plt.ylabel('Density')
    plt.legend()

    # 保存图表
    output_file = os.path.join(output_dir, f'EVI_Dist_Value_{value}_{year}.png')
    plt.savefig(output_file)
    print(f"Saved plot for Value_{value} in {year} to: {output_file}")

    # 关闭当前图表以释放内存
    plt.close()

print("All plots have been generated and saved.")