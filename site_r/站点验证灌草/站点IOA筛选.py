import pandas as pd
import rasterio
from rasterio.transform import rowcol

# 1. 读取站点位置CSV文件
sites_csv_path = r"F:\站点\中国地面\1963-2012\站点位置.csv"
sites_df = pd.read_csv(sites_csv_path, encoding='gbk')
# 确保CSV文件包含"纬度"和"经度"列
if "纬度" not in sites_df.columns or "经度" not in sites_df.columns:
    raise ValueError("CSV文件必须包含'纬度'和'经度'列")

# 2. 读取栅格数据
raster_path = r"D:\MODIS43A4_2024\SOS\500m(unmask0)\mean_values.tif"
with rasterio.open(raster_path) as src:
    # 获取栅格的仿射变换矩阵和像元数据
    transform = src.transform
    raster_data = src.read(1)  # 假设是单波段栅格

    # 3. 提取每个站点的像元值
    pixel_values = []
    for _, row in sites_df.iterrows():
        lon, lat = row["经度"], row["纬度"]

        # 将经纬度转换为栅格行列号
        row_index, col_index = rowcol(transform, lon, lat)

        # 确保行列号是整数
        row_index = int(row_index)
        col_index = int(col_index)

        # 检查行列号是否在栅格范围内
        if 0 <= row_index < raster_data.shape[0] and 0 <= col_index < raster_data.shape[1]:
            pixel_value = raster_data[row_index, col_index]
        else:
            pixel_value = None  # 如果不在范围内，记录为None

        pixel_values.append(pixel_value)
# 4. 将像元值添加到站点DataFrame中
sites_df["SOS"] = pixel_values

# 5. 保存结果到新的CSV文件
output_csv_path = r"F:\站点\中国地面\sitesos.csv"
sites_df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")

print(f"结果已保存到 {output_csv_path}")
