import rasterio
import numpy as np

# 文件路径
tif_path = r"D:\MODIS43A4_2024\EOS2\slope_values.tif"

# 读取 GeoTIFF 文件
with rasterio.open(tif_path) as src:
    data = src.read(1)  # 读取第一个波段（假设slope是单波段）

# 掩膜掉 NoData 值和 0 值（根据需求，0 也被视为无效）
nodata = src.nodata
if nodata is not None:
    valid_mask = (data != nodata) & (data != 0)
else:
    # 如果没有设置 nodata，只过滤 0 和非数值
    valid_mask = (data != 0) & np.isfinite(data)

# 提取所有有效像元
valid_data = data[valid_mask]

# 统计值小于 0 的像元数量
in_range = (valid_data > 0)
count_in_range = np.sum(in_range)
total_valid_pixels = valid_data.size

# 计算比例
ratio = count_in_range / total_valid_pixels if total_valid_pixels > 0 else 0

# 输出结果
print(f"Total valid pixels (excluding 0 and NoData): {total_valid_pixels}")
print(f"Pixels with negative slope values: {count_in_range}")
print(f"Proportion: {ratio:.4f} ({ratio * 100:.2f}%)")



