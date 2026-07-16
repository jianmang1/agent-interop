import pandas as pd
import rasterio
from rasterio.transform import rowcol
import os

# 1. 读取 CSV 文件
csv_path = r"F:\pythonforR\LOS\3.csv"
df = pd.read_csv(csv_path)

# 确保列名正确（注意空格和大小写）
required_cols = ['Site_Latitude(Degrees)', 'Site_Longitude(Degrees)', 'YEAR']
if not all(col in df.columns for col in required_cols):
    raise ValueError(f"CSV 缺少必要列: {required_cols}")

# 2. 初始化结果列
df['Pixel_Value'] = None

# 3. 遍历每一行
for idx, row in df.iterrows():
    lon = row['Site_Latitude(Degrees)']
    lat = row['Site_Longitude(Degrees)']
    year = int(row['YEAR'])

    # 构建 GeoTIFF 路径（注意你写的文件名是 LOS_{YEAR}.tif.tif，可能多了一个 .tif？）
    tif_path = rf"D:\MODIS43A4_2024\LOS\LOS_{year}.tif"

    # 检查文件是否存在
    if not os.path.exists(tif_path):
        print(f"警告：文件不存在 {tif_path}")
        continue

    try:
        with rasterio.open(tif_path) as src:
            # 将经纬度转为行列号（注意：rasterio 使用 (x, y) 即 (lon, lat)）
            row_idx, col_idx = src.index(lon, lat)

            # 检查是否在图像范围内
            if 0 <= row_idx < src.height and 0 <= col_idx < src.width:
                # 读取第一个波段的值（MODIS 通常是单波段或你需要指定波段）
                value = src.read(1)[row_idx, col_idx]
                df.at[idx, 'Pixel_Value'] = float(value) if value != src.nodata else None
            else:
                df.at[idx, 'Pixel_Value'] = None
                print(f"坐标超出范围: ({lat}, {lon}) in {tif_path}")

    except Exception as e:
        print(f"读取文件出错 {tif_path}: {e}")
        df.at[idx, 'Pixel_Value'] = None

# 4. 保存结果（可选）
output_csv = r"F:\pythonforR\LOS\3_with_pixel_values.csv"
df.to_csv(output_csv, index=False)
print(f"结果已保存到: {output_csv}")