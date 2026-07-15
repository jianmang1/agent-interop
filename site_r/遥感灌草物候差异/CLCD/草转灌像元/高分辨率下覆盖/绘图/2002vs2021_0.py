import rasterio
import numpy as np
import pandas as pd

# 定义路径列表
mean_config_2001 = [
    (rf'D:\MODIS43A4_2024\SOS\500m(unmask0)\masked2_masked_all_SoS_DOY_2001.tif', 'SOS'),
    (rf'D:\MODIS43A4_2024\POS\\unmask0\masked2_masked_all_PoS_DOY_2001.tif', 'POS'),
    (rf'D:\MODIS43A4_2024\EOS\500M\masked2_masked_all_EoS_DOY_2001.tif', 'EOS'),
    (rf'D:\MODIS43A4_2024\LOS\LOS_2001.tif', 'LOS'),
    (rf'D:\MODIS43A4_2024\GUP\POS-SOS_2001.tif', 'GUP'),
    (rf'D:\MODIS43A4_2024\GDP\EOS-POS_2001.tif', 'GDP'),
]

mean_config_2021 = [
    (rf'D:\MODIS43A4_2024\SOS\500m(unmask0)\masked2_masked_all_SoS_DOY_2021.tif', 'SOS'),
    (rf'D:\MODIS43A4_2024\POS\\unmask0\masked2_masked_all_PoS_DOY_2021.tif', 'POS'),
    (rf'D:\MODIS43A4_2024\EOS\500M\masked2_masked_all_EoS_DOY_2021.tif', 'EOS'),
    (rf'D:\MODIS43A4_2024\LOS\LOS_2021.tif', 'LOS'),
    (rf'D:\MODIS43A4_2024\GUP\POS-SOS_2021.tif', 'GUP'),
    (rf'D:\MODIS43A4_2024\GDP\EOS-POS_2021.tif', 'GDP'),
]

# 获取2001和2021年的GR和SR文件路径
gr_2001 = r'D:\转变\masked_CLCD\masked_CLCD_v01_2002_SOS_GR.tif'
sr_2001 = r'D:\转变\masked_CLCD\masked_CLCD_v01_2002_SOS_SR.tif'
gr_2021 = r'D:\转变\masked_CLCD\masked_CLCD_v01_2021_SOS_GR.tif'
sr_2021 = r'D:\转变\masked_CLCD\masked_CLCD_v01_2021_SOS_SR.tif'

# 读取特定的TIFF文件
def read_tiff(file_path):
    with rasterio.open(file_path) as src:
        data = src.read(1)
        return data

# 计算差值并提取符合条件的像素点
def process_years(mean_config_year1, mean_config_year2, gr_file_year1, sr_file_year1, gr_file_year2, sr_file_year2):
    # 读取数据
    gr_data_year1 = read_tiff(gr_file_year1)
    sr_data_year1 = read_tiff(sr_file_year1)
    gr_data_year2 = read_tiff(gr_file_year2)
    sr_data_year2 = read_tiff(sr_file_year2)

    # 计算差值
    gr_diff = gr_data_year2 - gr_data_year1
    sr_diff = sr_data_year2 - sr_data_year1

    # 找出符合条件的像素点
    condition = (gr_diff < 0) & (sr_diff > 0)

    # 提取符合条件的像素点的坐标和对应的值
    rows, cols = np.where(condition)
    data_list = []
    for row, col in zip(rows, cols):
        data_dict = {
            'Row': row,
            'Column': col,
            'GR_Difference': gr_diff[row, col],
            'SR_Difference': sr_diff[row, col]
        }
        # 添加其他年份的数据
        for file_path, label in mean_config_year2:
            data = read_tiff(file_path)
            data_dict[label] = data[row, col]
        data_list.append(data_dict)

    return data_list

# 处理2002到2021年的数据
data_list_2002_2021 = process_years(mean_config_2001, mean_config_2021, gr_2001, sr_2001, gr_2021, sr_2021)

# 将数据保存到DataFrame
df = pd.DataFrame(data_list_2002_2021)

# 保存到Excel文件
output_excel = r'D:\转变\pixel_differences.xlsx'
df.to_excel(output_excel, index=False)

print(f"Data has been saved to {output_excel}")



