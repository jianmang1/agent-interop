import os
from pathlib import Path
import rasterio
import numpy as np

# 定义路径
RASTER_DIR = Path(r'D:\MOD12Q2\vs')
DIFF_DIR = Path(r'D:\MOD12Q2\dif')

# 确保输出目录存在
os.makedirs(DIFF_DIR, exist_ok=True)

# 定义要可视化的栅格文件名及其对应的差异文件名
RASTER_PAIRS = {
    ('masked2_SOS_MCD12Q2_2023_masked_tibet.tif', 'masked2_masked_all_SoS_DOY_2023_masked_tibet.tif'): DIFF_DIR / "difsos2.tif",
    ('masked2_EOS_MCD12Q2_2023_masked_tibet.tif', 'masked2_masked_all_EoS_DOY_2023_masked_tibet.tif'): DIFF_DIR / "difeos2.tif",
    ('masked2_LOS_MCD12Q2_2023_masked_tibet.tif', 'masked2_masked_all_LoS_DOY_2023_masked_tibet.tif'): DIFF_DIR / "diflos2.tif",
}

def calculate_difference_and_save(file1_path, file2_path, output_path):
    with rasterio.open(file1_path) as src1:
        data1 = src1.read(1).astype('float32')
        transform = src1.transform
        crs = src1.crs
        nodata = src1.nodata

    with rasterio.open(file2_path) as src2:
        data2 = src2.read(1).astype('float32')

    # 设置无效值为 NaN
    invalid_values = [-9999,1,365, 0]
    for value in invalid_values:
        data1[data1 == value] = np.nan
        data2[data2 == value] = np.nan

    # 计算差异并取绝对值
    difference = (data2 - data1)

    # 创建输出文件的元数据
    meta = src1.meta.copy()
    meta.update({
        'dtype': 'float32',
        'nodata': np.nan,
        'count': 1,
    })

    # 写入差异数据到新文件
    with rasterio.open(output_path, 'w', **meta) as dst:
        dst.write(difference.astype('float32'), 1)

# 主循环
for (file1, file2), output_file in RASTER_PAIRS.items():
    file1_path = RASTER_DIR / file1
    file2_path = RASTER_DIR / file2
    calculate_difference_and_save(file1_path, file2_path, output_file)



