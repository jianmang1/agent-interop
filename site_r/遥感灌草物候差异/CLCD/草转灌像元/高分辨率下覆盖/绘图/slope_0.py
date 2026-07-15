import os
import re
import numpy as np
import rasterio
from scipy.stats import linregress
from tqdm import tqdm

# 设置输入输出路径
input_folder = r"D:\转变\masked_CLCD"  # 替换为你的实际路径
output_file = r"D:\转变\masked_CLCD\slope.tif"

# 1. 使用正则表达式筛选符合格式的文件
year_pattern = re.compile(r"^masked_CLCD_v01_(\d{4})_SOS_GR\.tif$")
valid_files = []

for filename in os.listdir(input_folder):
    match = year_pattern.match(filename)
    if match:
        year = int(match.group(1))
        if 2002 <= year <= 2021:
            valid_files.append((year, filename))

# 2. 按年份排序
valid_files.sort()
tif_files = [f[1] for f in valid_files]
years = [f[0] for f in valid_files]

print(f"找到 {len(tif_files)} 个符合条件的文件，年份范围: {min(years)} - {max(years)}")

# 3. 读取第一个文件的元数据
first_file_path = os.path.join(input_folder, tif_files[0])
with rasterio.open(first_file_path) as src:
    profile = src.profile
    height, width = src.height, src.width
    transform = src.transform
    nodata = src.nodata

# 4. 初始化数据立方体
num_years = len(tif_files)
data_cube = np.zeros((num_years, height, width), dtype=np.float32)

# 5. 读取所有年份数据
for i, tif in enumerate(tqdm(tif_files, desc="Reading files")):
    file_path = os.path.join(input_folder, tif)
    with rasterio.open(file_path) as src:
        band = src.read(1).astype(np.float32)
        if nodata is not None:
            band[band == nodata] = np.nan
        data_cube[i] = band

# 6. 计算每个像素的线性回归斜率
slope_array = np.zeros((height, width), dtype=np.float32)

for y in tqdm(range(height), desc="Calculating slope"):
    for x in range(width):
        pixel_values = data_cube[:, y, x]
        valid_mask = ~np.isnan(pixel_values)
        if np.sum(valid_mask) < 2:
            slope_array[y, x] = np.nan
        else:
            time = np.array(years)[valid_mask]  # 使用实际年份作为时间变量
            values = pixel_values[valid_mask]
            slope, _, _, _, _ = linregress(time, values)
            slope_array[y, x] = slope

# 7. 保存结果为TIFF文件
profile.update(dtype=rasterio.float32, count=1, nodata=np.nan)
with rasterio.open(output_file, "w", **profile) as dst:
    dst.write(slope_array, 1)

print(f"斜率结果已保存至: {output_file}")