import csv
import rasterio
import pandas as pd
from rasterio.transform import from_origin
import os

# CSV文件路径
csv_path = r'F:\deng_site\site1.csv'
# 固定的TIFF文件路径
tif_path = r'D:\MODIS43A4_amplitude\sos3(unmask0)\mean_values.tif'

# 读取CSV文件，明确指定year列为整数类型
df = pd.read_csv(csv_path, dtype={'year': int})

# 存储结果
results = []

# 打开TIFF文件
with rasterio.open(tif_path) as src:
    # 遍历每一行数据
    for index, row in df.iterrows():
        lat = row['lat']
        lon = row['lon']

        try:
            # 将经纬度转换为栅格的行列号
            x, y = lon, lat  # rasterio使用（经度，纬度）即（x, y）
            row_idx, col_idx = src.index(x, y)

            # 读取像元值
            value = src.read(1, window=((row_idx, row_idx + 1), (col_idx, col_idx + 1)))[0][0]

            # 保存结果
            results.append({
                'lat': lat,
                'lon': lon,
                'value': value
            })
        except Exception as e:
            print(f"错误: 在处理坐标 ({lat}, {lon}) 时发生异常 - {str(e)}")
            continue

# 将结果保存到新的CSV文件
output_df = pd.DataFrame(results)
output_csv = os.path.join(os.path.dirname(csv_path), 'extracted_values2.csv')
output_df.to_csv(output_csv, index=False)

print(f"处理完成，结果已保存至 {output_csv}")



