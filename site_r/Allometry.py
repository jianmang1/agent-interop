import os
import numpy as np
from rasterio import open as rio_open
from scipy.optimize import curve_fit
from tqdm import tqdm

# 定义函数 y = ax^b
def func(x, a, b):
    return a * x ** b


# 获取文件路径列表
los_dir = r'F:\MODIS43A4_DOY\LOS'
gos_dir = r'F:\MODIS43A4_DOY\GOS'
years = range(2001, 2024)

los_files = [os.path.join(los_dir, f'difference_{year}.tif') for year in years]
gos_files = [os.path.join(gos_dir, f'difference_{year}.tif') for year in years]

# 确保文件存在
for file in los_files + gos_files:
    if not os.path.exists(file):
        raise FileNotFoundError(f"File {file} does not exist.")

# 初始化输出数组
with rio_open(los_files[0]) as src:
    profile = src.profile
    a_array = np.zeros(src.shape, dtype=np.float32)
    b_array = np.zeros(src.shape, dtype=np.float32)
    r_array = np.zeros(src.shape, dtype=np.float32)

# 遍历每个像素点进行拟合
for i in tqdm(range(profile['height']), desc='Processing rows', position=0, leave=True):
    for j in tqdm(range(profile['width']), desc=f'Row {i+1}', position=1, leave=False):
        x = []
        y = []

        # 收集 x 和 y 的值
        for los_file, gos_file in zip(los_files, gos_files):
            with rio_open(los_file) as los_src, rio_open(gos_file) as gos_src:
                x_val = los_src.read(1)[i, j]
                y_val = gos_src.read(1)[i, j]

                # 跳过无效值
                if x_val != src.nodata and y_val != src.nodata:
                    x.append(x_val)
                    y.append(y_val)

        # 如果有足够的数据点，则进行拟合
        if len(x) > 1:
            try:
                popt, _ = curve_fit(func, x, y)
                a, b = popt
                a_array[i, j] = a
                b_array[i, j] = b

                # 计算 R^2
                residuals = np.array(y) - func(np.array(x), a, b)
                ss_res = np.sum(residuals ** 2)
                ss_tot = np.sum((np.array(y) - np.mean(y)) ** 2)
                r2 = 1 - (ss_res / ss_tot)
                r_array[i, j] = r2
            except RuntimeError:
                # 拟合失败时的处理
                a_array[i, j] = np.nan
                b_array[i, j] = np.nan
                r_array[i, j] = np.nan

# 保存结果到新的 TIFF 文件
profile.update(dtype='float32', nodata=np.nan)
with rio_open('output_a.tif', 'w', **profile) as dst:
    dst.write(a_array, 1)

with rio_open('output_b.tif', 'w', **profile) as dst:
    dst.write(b_array, 1)

with rio_open('output_r.tif', 'w', **profile) as dst:
    dst.write(r_array, 1)