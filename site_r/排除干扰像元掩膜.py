import os
from osgeo import gdal, gdal_array

# 设置输入和输出文件夹路径
input_folder = r'D:\MODIS43A4_amplitude\sos500'
output_folder = r'D:\MODIS43A4_amplitude\sos500\MODIS43A4_amplitude掩膜'

# 确保输出文件夹存在
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 遍历年份
for year in range(2001, 2024):  # 从2001年到2023年
    input_file = os.path.join(input_folder, f'all_ndpiforsos_pos_amplitude_{year}.tif')
    output_file = os.path.join(output_folder, f'SOS_掩膜_{year}.tif')

    # 打开栅格数据集
    ds = gdal.Open(input_file)
    if ds is None:
        print(f"无法打开文件: {input_file}")
        continue

    # 读取第一个波段的数据
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()

    # 创建掩膜，将小于0.1的值设为NaN
    mask = data < 0.00782
    data[mask] = float('nan')  # 或者使用其他方式表示无效值

    # 创建输出文件
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.CreateCopy(output_file, ds, 0)

    # 写入修改后的数据
    out_band = out_ds.GetRasterBand(1)
    out_band.WriteArray(data)

    # 设置NoData值
    out_band.SetNoDataValue(float('nan'))  # 根据需要调整

    # 清理
    out_band.FlushCache()
    del out_ds, ds

print("处理完成")