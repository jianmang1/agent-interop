import os
import rasterio
import numpy as np

# 定义文件夹路径
gos_folder = r'D:\MODIS43A4_2024\GOS'
los_folder = r'D:\MODIS43A4_2024\LOS'
output_folder = r'D:\MODIS43A4_2024\GOSTOLOS'

# 确保输出文件夹存在
os.makedirs(output_folder, exist_ok=True)

# 获取文件列表
years = range(2024, 2025)
for year in years:
    gos_file = os.path.join(gos_folder, f'GOS_{year}.tif')
    los_file = os.path.join(los_folder, f'LOS_{year}.tif')
    output_file = os.path.join(output_folder, f'GTL_{year}.tif')

    # 检查文件是否存在
    if not (os.path.exists(gos_file) and os.path.exists(los_file)):
        print(f"Files for year {year} do not exist.")
        continue

    # 打开栅格文件
    with rasterio.open(gos_file) as src_gos, rasterio.open(los_file) as src_los:
        # 读取栅格数据
        gos_data = src_gos.read(1).astype('float32')
        los_data = src_los.read(1).astype('float32')

        # 创建掩膜，排除无效值 -9999 和 0
        mask = ((gos_data != -9999) & (gos_data != 0) & (los_data != -9999) & (los_data != 0) & (los_data != 0))

        # 初始化结果数组，默认值设置为无效值 -9999.0
        result = np.full_like(gos_data, -9999.0, dtype='float32')

        # 在有效点上执行除法运算
        result[mask] = gos_data[mask] / los_data[mask]

        # 复制元数据
        meta = src_gos.meta.copy()
        meta.update(dtype=rasterio.float32, nodata=-9999)  # 设置nodata值为-9999

        # 保存结果
        with rasterio.open(output_file, 'w', **meta) as dst:
            dst.write(result, 1)

    print(f"Processed and saved {output_file}")