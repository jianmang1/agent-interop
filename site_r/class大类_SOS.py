import os
import numpy as np
from osgeo import gdal
from scipy.stats import linregress
import pandas as pd

# 启用GDAL异常
gdal.UseExceptions()

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

# 定义值的分组
value_groups = [
    [21, 22, 23, 24],  # 第一组
    [31, 32, 33],      # 第二组
    [61, 62, 63, 64, 65, 66, 67]  # 第三组
]

# 初始化存储结果的字典
results = {f"Group_{i+1}": {} for i in range(len(value_groups))}

# 定义块大小
chunk_size = 1000  # 根据你的内存情况调整这个值

# 读取重采样的土地利用数据
resampled_land_file = r'F:\个人\CLASS\新建文件夹\中科院_mode_resampled_clipped.tif'
print(f"Reading resampled land use data from: {resampled_land_file}")
resampled_land_data, x_size, y_size = read_raster(resampled_land_file)

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

            # 对于每个土地利用类型组，应用掩码提取特定像元的EVI值，并排除无效值 -9999
            for group_idx, value_group in enumerate(value_groups):
                mask_chunk = np.isin(land_chunk, value_group) & (evi_chunk != -9999)
                evi_values = evi_chunk[mask_chunk].flatten()

                if len(evi_values) > 0:
                    # 过滤掉 NaN 和无穷大值
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
                        group_key = f"Group_{group_idx+1}"
                        if year not in results[group_key]:
                            results[group_key][year] = {
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
                            results[group_key][year]['mean'] = mean_evi
                            results[group_key][year]['std'] = std_evi
                            results[group_key][year]['min'] = min_evi
                            results[group_key][year]['q1'] = q1_evi
                            results[group_key][year]['median'] = median_evi
                            results[group_key][year]['q3'] = q3_evi
                            results[group_key][year]['max'] = max_evi
                            results[group_key][year]['values'].extend(evi_values.tolist())

# 分析趋势并输出到Excel
excel_file = 'F:\MODIS43A4_DOY\SOS\\allsos_class_results2.xlsx'
writer = pd.ExcelWriter(excel_file, engine='openpyxl')

for group_key in results:
    if results[group_key]:
        years = list(results[group_key].keys())
        means = [results[group_key][year]['mean'] for year in years]
        stds = [results[group_key][year]['std'] for year in years]
        mins = [results[group_key][year]['min'] for year in years]
        q1s = [results[group_key][year]['q1'] for year in years]
        medians = [results[group_key][year]['median'] for year in years]
        q3s = [results[group_key][year]['q3'] for year in years]
        maxs = [results[group_key][year]['max'] for year in years]

        # 使用线性回归分析趋势
        slope, intercept, r_value, p_value, std_err = linregress(years, means)

        # 创建DataFrame
        df = pd.DataFrame({
            'Year': years,
            'Mean EVI': means,
            'Std EVI': stds,
            'Min EVI': mins,
            'Q1 EVI': q1s,
            'Median EVI': medians,
            'Q3 EVI': q3s,
            'Max EVI': maxs
        })

        # 添加趋势信息
        df['Trend'] = slope
        df['Trend Std Err'] = std_err
        df['p-value'] = p_value
        df['Significant'] = df['p-value'] < 0.05

        # 写入Excel
        sheet_name = f'{group_key}'
        df.to_excel(writer, sheet_name=sheet_name, index=False)

# 保存Excel文件
writer.close()
print(f"Results exported to: {excel_file}")