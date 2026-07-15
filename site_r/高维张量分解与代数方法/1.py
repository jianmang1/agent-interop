import rasterio
import numpy as np
import tensorly as tl
from tqdm import tqdm  # 进度条

# 初始化空张量（按需调整分块大小）
block_size = 512  # 分块大小
H, W, B, T = None, None, 3, 24  # 待确定的空间尺寸

# 获取第一年的元数据以确定空间尺寸
with rasterio.open("D:/MODIS43A4_2024/MULTIBAND/multiband_2001.tif") as src:
    H, W = src.height, src.width

# 预分配张量（使用float32减少内存）
X = np.memmap('temp.dat', dtype=np.float32, mode='w+', shape=(H, W, B, T))

# 逐年份分块加载
for t in tqdm(range(T)):
    year = 2001 + t
    with rasterio.open(f"D:/MODIS43A4_2024/MULTIBAND/multiband_{year}.tif") as src:
        # 分块读取
        for i in range(0, H, block_size):
            for j in range(0, W, block_size):
                window = rasterio.windows.Window(j, i, block_size, block_size)
                data = src.read(window=window).astype(np.float32)  # (B, h, w)
                X[i:i+block_size, j:j+block_size, :, t] = data.transpose(1, 2, 0)

# 释放临时文件
del X