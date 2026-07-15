import rasterio
import numpy as np

# 文件路径
tif_path = r"D:\MODIS43A4_2024\EOS2\slope_values.tif"

# 读取 GeoTIFF 文件
with rasterio.open(tif_path) as src:
    data = src.read(1)  # 读取第一个波段（假设SOS是单波段）

# 掩膜掉 NoData 值（非常重要！）
nodata = src.nodata
if nodata is not None:
    valid_mask = data != nodata
else:
    # 如果没有设置 nodata，可考虑用 NaN 或其他方式判断
    valid_mask = np.isfinite(data)  # 排除 NaN/Inf

# 提取所有有效像元
valid_data = data[valid_mask]

# 统计值在 [70, 130] 范围内的像元数量 in_range = (valid_data >= 240) & (valid_data <= 280)
in_range = (valid_data < 0)
count_in_range = np.sum(in_range)
total_valid_pixels = valid_data.size

# 计算比例
ratio = count_in_range / total_valid_pixels if total_valid_pixels > 0 else 0

# 输出结果
print(f"Total valid pixels: {total_valid_pixels}")
print(f"Pixels with SOS between 70 and 130: {count_in_range}")
print(f"Proportion: {ratio:.4f} ({ratio * 100:.2f}%)")