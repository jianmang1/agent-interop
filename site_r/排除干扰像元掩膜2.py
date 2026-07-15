import os
import rasterio
import numpy as np

# 定义输入输出路径
input_amplitude_dir = r'D:\MODIS43A4_amplitude\POS\MODIS43A4_amplitude掩膜'
input_sos_dir = r'D:\MODIS43A4_amplitude\POS'
output_sos_dir = r'D:\MODIS43A4_amplitude\POS\MODIS43A4_amplitude掩膜2'

# 确保输出目录存在
if not os.path.exists(output_sos_dir):
    os.makedirs(output_sos_dir)

# 遍历年份2001-2023
for year in range(2001, 2024):
    # 构建文件名
    amplitude_filename = f'POS_掩膜_{year}.tif'
    sos_filename = f'all_PoS_value_{year}.tif'
    output_sos_filename = f'POS_掩膜2_{year}_masked.tif'

    # 构建完整路径
    amplitude_path = os.path.join(input_amplitude_dir, amplitude_filename)
    sos_path = os.path.join(input_sos_dir, sos_filename)
    output_sos_path = os.path.join(output_sos_dir, output_sos_filename)

    # 打开振幅值和SoS值栅格文件
    with rasterio.open(amplitude_path) as amplitude_src:
        with rasterio.open(sos_path) as sos_src:
            # 读取数据
            amplitude_data = amplitude_src.read(1)
            sos_data = sos_src.read(1)

            # 创建掩膜，振幅值小于0.1的像元为True
            mask = amplitude_data < 0.1

            # 将掩膜应用于SoS值数据，使用-9999作为填充值
            fill_value = -9999  # 你可以根据需要更改这个值
            masked_sos_data = np.where(mask, fill_value, sos_data)

            # 写入新的SoS值文件
            profile = sos_src.profile
            profile.update(nodata=fill_value)  # 更新nodata值以匹配填充值
            with rasterio.open(output_sos_path, 'w', **profile) as dst:
                dst.write(masked_sos_data, 1)

    print(f"Processed {year} data.")

print("All processing completed.")