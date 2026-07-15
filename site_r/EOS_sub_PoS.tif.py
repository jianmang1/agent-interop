import os
from osgeo import gdal, osr

# 定义EOS和SOS的文件夹路径
eos_folder = r'D:\MODIS43A4_2024\EOS'
sos_folder = r'D:\MODIS43A4_2024\SOS'
output_folder = r'D:\MODIS43A4_2024\LOS'  # 输出结果的文件夹

# 确保输出文件夹存在
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 获取所有年份
years = range(2001, 2024)  # 从2001到2023

for year in years:
    # 构建文件路径
    eos_file = os.path.join(eos_folder, f'mask_applied_masked_all_EOS_DOY_{year}.tif')
    sos_file = os.path.join(sos_folder, f'mask_applied_masked_all_SOS_DOY_{year}.tif')
    output_file = os.path.join(output_folder, f'mask_applied_masked_all_LOS_DOY__{year}.tif')

    # 打开EOS和SOS的栅格数据集
    eos_ds = gdal.Open(eos_file)
    sos_ds = gdal.Open(sos_file)

    if eos_ds is None or sos_ds is None:
        print(f"无法打开文件 {eos_file} 或 {sos_file}")
        continue

    # 获取波段
    eos_band = eos_ds.GetRasterBand(1)
    sos_band = sos_ds.GetRasterBand(1)

    # 读取数据
    eos_data = eos_band.ReadAsArray()
    sos_data = sos_band.ReadAsArray()

    # 进行减法运算
    difference_data = eos_data - sos_data

    # 创建输出文件
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(output_file, eos_ds.RasterXSize, eos_ds.RasterYSize, 1, gdal.GDT_Float32)
    out_band = out_ds.GetRasterBand(1)

    # 写入数据
    out_band.WriteArray(difference_data)

    # 设置地理转换参数和投影信息
    out_ds.SetGeoTransform(eos_ds.GetGeoTransform())
    out_ds.SetProjection(eos_ds.GetProjection())

    # 清理资源
    out_band.FlushCache()
    del out_ds, eos_ds, sos_ds

print("所有文件处理完毕")