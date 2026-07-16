import os
from osgeo import gdal, ogr, osr

# 定义配置列表    (r'D:\MODIS43A4_value\SOS\masked2_masked_all_SoS_value_{}.tif', 'SOS'),
#     (r'D:\MODIS43A4_Value\POS\masked2_masked_all_PoS_value_{}.tif', 'POS'),
#     (r'D:\MODIS43A4_value\EOS\masked2_masked_all_EoS_value_{}.tif', 'EOS'),
#     (r'D:\MODIS43A4_value\LOS\masked2_masked_all_AoS_value_{}.tif', 'AOS')
mean_config = [
    (r'D:\MODIS43A4_value\SOS\masked2_masked_all_SoS_value_{}.tif', 'SOS'),
    (r'D:\MODIS43A4_Value\POS\masked2_masked_all_PoS_value_{}.tif', 'POS'),
    (r'D:\MODIS43A4_value\EOS\masked2_masked_all_EoS_value_{}.tif', 'EOS'),
    (r'D:\MODIS43A4_value\AOS\masked2_masked_all_AoS_value_{}.tif', 'AOS'),
    (r'D:\MODIS43A4_2024\ROG\ROG_{}.tif', 'ROG'),
    (r'D:\MODIS43A4_2024\ROS\ROS_{}.tif', 'ROS')
]


def process_file(file_path):
    # 打开数据集
    dataset = gdal.Open(file_path, gdal.GA_Update)
    band = dataset.GetRasterBand(1)

    # 读取栅格数据
    data = band.ReadAsArray()

    # 替换像元值
    data[data == 0] = -9999

    # 写回数据
    band.WriteArray(data)

    # 清理
    del dataset


for year in range(2000, 2025):
    for file_pattern, _ in mean_config:
        file_path = file_pattern.format(year)
        if os.path.exists(file_path):
            print(f"Processing {file_path}")
            process_file(file_path)
        else:
            print(f"File not found: {file_path}")



