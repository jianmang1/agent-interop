import os
import numpy as np
from osgeo import gdal

# 设置工作目录和文件路径
os.chdir(r'D:\MODIS43A4_amplitude\SOS500\MODIS43A4_amplitude掩膜')
output_dir = r'D:\MODIS43A4_amplitude\SOS500\MODIS43A4_amplitude掩膜'  # 确保此目录存在或修改为你需要的输出目录
mask_file_path = r'D:\数据\AI\Global-AI_ET0_v3_annual\mask_less_than_6500.tif'

# 获取文件列表
file_list = [f for f in os.listdir() if f.startswith('SOS_掩膜_') and f.endswith('.tif')]
file_list.sort()

# 打开第一个文件以获取元数据（假设所有文件具有相同的分辨率和边界）
first_file = file_list[0]
dataset = gdal.Open(first_file)
band = dataset.GetRasterBand(1)

# 读取第一个文件的数据作为模板
template_array = band.ReadAsArray()
no_data_value = band.GetNoDataValue()  # 获取无效值

# 初始化掩膜数组为1，确保数据类型能容纳NaN或无效值
mask = np.ones_like(template_array, dtype=np.float32)  # 使用float32类型

# 遍历所有文件
for file in file_list:
    dataset = gdal.Open(file)
    band = dataset.GetRasterBand(1)
    array = band.ReadAsArray().astype(np.float32)  # 确保读入的数据类型一致

    # 更新掩膜：如果任何一个文件在该位置有无效值（NaN或no_data_value），则将掩膜对应位置设为无效值
    mask[np.isnan(array) | (array == no_data_value)] = no_data_value

# 保存中间结果combined_mask.tif
combined_mask_file = os.path.join(output_dir, 'combined_mask.tif')
driver = gdal.GetDriverByName('GTiff')
out_dataset = driver.Create(combined_mask_file, dataset.RasterXSize, dataset.RasterYSize, 1, gdal.GDT_Float32)
out_band = out_dataset.GetRasterBand(1)
out_band.WriteArray(mask)
out_band.SetNoDataValue(no_data_value)
out_dataset.SetGeoTransform(dataset.GetGeoTransform())
out_dataset.SetProjection(dataset.GetProjection())
del out_dataset, dataset

# 加载combined_mask.tif
combined_dataset = gdal.Open(combined_mask_file)
combined_band = combined_dataset.GetRasterBand(1)
combined_array = combined_band.ReadAsArray().astype(np.float32)

# 加载mask_less_than_6500.tif作为掩膜
mask_dataset = gdal.Open(mask_file_path)
mask_band = mask_dataset.GetRasterBand(1)
mask_array = mask_band.ReadAsArray()

# 应用掩膜到combined_mask.tif
masked_array = np.where(mask_array == 0, no_data_value, combined_array)

# 保存最终结果
final_output_file = os.path.join(output_dir, 'final_masked_combined_mask.tif')
final_dataset = driver.Create(final_output_file, combined_dataset.RasterXSize, combined_dataset.RasterYSize, 1, gdal.GDT_Float32)
final_band = final_dataset.GetRasterBand(1)
final_band.WriteArray(masked_array)
final_band.SetNoDataValue(no_data_value)
final_dataset.SetGeoTransform(combined_dataset.GetGeoTransform())
final_dataset.SetProjection(combined_dataset.GetProjection())

# 清理
del final_dataset, combined_dataset, mask_dataset

print("处理完成")