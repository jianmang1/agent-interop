import rasterio
import numpy as np
import pandas as pd

# 输入文件路径
source_raster_path = r'F:\个人\CLASS\新建文件夹\中科院_mode_resampled_clipped_FINAL.tif'
mean_raster_path = r'D:\MODIS43A4_2024\SOS\mean_values.tif'
output_excel_path = r'D:\MODIS43A4_2024\SOS\output.xlsx'  # 修改为实际输出路径

# 读取源栅格数据
with rasterio.open(source_raster_path) as src:
    src_array = src.read(1)
    src_height, src_width = src_array.shape

# 读取mean栅格数据
with rasterio.open(mean_raster_path) as mean_src:
    mean_array = mean_src.read(1)
    if mean_array.shape != (src_height, src_width):
        raise ValueError("两个栅格尺寸不一致，请检查输入文件")

# 获取所有值为22的像元坐标
rows, cols = np.where(src_array == 22)

data = []

# 处理每个目标像元
for row, col in zip(rows, cols):
    # 计算邻域范围
    min_row = max(0, row - 1)
    max_row = min(src_height - 1, row + 1)
    min_col = max(0, col - 1)
    max_col = min(src_width - 1, col + 1)

    # 统计邻域像元
    n31, n32, n33 = 0, 0, 0
    cells_31, cells_32, cells_33 = [], [], []

    for i in range(min_row, max_row + 1):
        for j in range(min_col, max_col + 1):
            val = src_array[i, j]
            if val == 31:
                n31 += 1
                cells_31.append((i, j))
            elif val == 32:
                n32 += 1
                cells_32.append((i, j))
            elif val == 33:
                n33 += 1
                cells_33.append((i, j))

    # 筛选有效数据
    if (n31 + n32 + n33) == 0:
        continue

    # 获取sos值
    sos22 = mean_array[row, col]

    # 计算邻域均值
    sos31 = np.mean([mean_array[i, j] for i, j in cells_31]) if cells_31 else 0.0
    sos32 = np.mean([mean_array[i, j] for i, j in cells_32]) if cells_32 else 0.0
    sos33 = np.mean([mean_array[i, j] for i, j in cells_33]) if cells_33 else 0.0

    # 添加记录
    data.append({
        'n31': n31,
        'n32': n32,
        'n33': n33,
        'sos22': sos22,
        'sos31': sos31,
        'sos32': sos32,
        'sos33': sos33
    })

# 创建DataFrame并导出
if data:
    df = pd.DataFrame(data)
    df.to_excel(output_excel_path, index=False)
    print(f'数据已导出至：{output_excel_path}')
else:
    print('未找到符合条件的像元')