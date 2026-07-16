import os
from osgeo import gdal, gdal_array

# 设置输入和输出文件夹路径
input_folder = r'F:\个人\SOS\MODIS43A4_amplitude_value'
output_folder = r'F:\个人\SOS\MODIS43A4_amplitude掩膜2'
pos_folder = r'F:\MODIS43A4_Value\POS'

# 确保输出文件夹存在
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 遍历年份
for year in range(2001, 2024):  # 从2001年到2023年
    input_file = os.path.join(input_folder, f'all_amplitude_value_{year}.tif')
    pos_file = os.path.join(pos_folder, f'all_PoS_value_{year}.tif')
    output_file = os.path.join(output_folder, f'all_掩膜_{year}.tif')

    # 打开栅格数据集
    ds = gdal.Open(input_file)
    if ds is None:
        print(f"无法打开文件: {input_file}")
        continue

    pos_ds = gdal.Open(pos_file)
    if pos_ds is None:
        print(f"无法打开文件: {pos_file}")
        continue

    # 读取第一个波段的数据
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()

    pos_band = pos_ds.GetRasterBand(1)
    pos_data = pos_band.ReadAsArray()

    # 创建掩膜，将小于0.1的值设为NaN，并且对于POS数据小于0.0398234293013338的也设为NaN
    mask_amplitude = data < 0.00311288
    mask_pos = pos_data < 0.0398234293013338
    combined_mask = mask_amplitude | mask_pos  # 结合两个条件

    data[combined_mask] = float('nan')  # 或者使用其他方式表示无效值

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
    del out_ds, ds, pos_ds

print("处理完成")