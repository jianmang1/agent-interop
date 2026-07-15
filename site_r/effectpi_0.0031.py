import os
import rasterio
import pandas as pd
from rasterio.enums import Resampling

# 定义路径和文件名格式
base_path = r'D:\MODIS43A4_amplitude\SOS'
file_pattern = 'mask_applied_SOS_amplitude_value_{year}.tif'
start_year = 2001
end_year = 2023

# 创建一个空的DataFrame来存储结果
results_df = pd.DataFrame(columns=['Year', 'Ratio'])

# 遍历年份，读取并处理每个文件
for year in range(start_year, end_year + 1):
    file_name = file_pattern.format(year=year)
    file_path = os.path.join(base_path, file_name)

    if not os.path.exists(file_path):
        print(f"File for year {year} does not exist: {file_path}")
        continue

    # 打开GeoTIFF文件
    with rasterio.open(file_path) as src:
        # 读取数据
        data = src.read(1, masked=True)  # 假设是单波段图像

        # 计算小于0.0031的像元数量
        count_less_than_threshold = (data < 0.0031).sum()

        # 计算总像元数量（不包括nodata）
        total_count = data.count()

        # 计算比例
        ratio = count_less_than_threshold / total_count if total_count > 0 else 0

        # 将结果添加到DataFrame
        new_row = pd.DataFrame({'Year': [year], 'Ratio': [ratio]})
        results_df = pd.concat([results_df, new_row], ignore_index=True)

# 导出结果到CSV文件
output_csv_path = os.path.join(base_path, 'pixel_ratio_results.csv')
results_df.to_csv(output_csv_path, index=False)

print(f"Results have been saved to {output_csv_path}")