import rasterio
import numpy as np

def count_pixels_above_zero(file_path):
    with rasterio.open(file_path) as src:
        # 读取栅格数据
        image = src.read(1)  # 假设我们只处理第一个波段
        # 计算值大于0的像素数量
        above_zero_count = np.count_nonzero(image > 0)
    return above_zero_count

# 文件路径
los_file_path = r"D:\MODIS43A4_2024\LOS\LOS_2024.tif"
sos_file_path = r"D:\MODIS43A4_2024\SOS\mask_applied_masked_all_SOS_DOY_2023.tif"
eos_file_path = r"D:\MODIS43A4_2024\EOS\mask_applied_masked_all_EOS_DOY_2023.tif"
pos_file_path = r"D:\MODIS43A4_2024\POS\mask_applied_masked_all_PoS_DOY_2024.tif"

# 统计大于0的像元数量
los_valid_pixels = count_pixels_above_zero(los_file_path)
sos_valid_pixels = count_pixels_above_zero(sos_file_path)
eos_valid_pixels = count_pixels_above_zero(eos_file_path)
pos_valid_pixels = count_pixels_above_zero(pos_file_path)

print(f"LOS file has {los_valid_pixels} pixels with values greater than 0.")
print(f"SOS file has {sos_valid_pixels} pixels with values greater than 0.")
print(f"EOS file has {eos_valid_pixels} pixels with values greater than 0.")
print(f"POS file has {pos_valid_pixels} pixels with values greater than 0.")