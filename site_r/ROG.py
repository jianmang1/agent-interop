import os
import rasterio
import numpy as np

# 定义路径和年份范围
sos_doy_dir = r'D:\MODIS43A4_2024\SOS2'           # SOS DOY 文件路径
pos_doy_dir = r'D:\MODIS43A4_2024\POS2'           # POS DOY 文件路径
sos_val_dir = r'D:\MODIS43A4_Value\SOS'           # SOS Value 文件路径
pos_val_dir = r'D:\MODIS43A4_Value\POS'           # POS Value 文件路径

years = range(2001, 2025)

# 构建文件路径列表
sos_doy_files = [os.path.join(sos_doy_dir, f'masked2_masked_all_SoS_DOY_{year}.tif') for year in years]
pos_doy_files = [os.path.join(pos_doy_dir, f'masked2_masked_all_PoS_DOY_{year}.tif') for year in years]
sos_val_files = [os.path.join(sos_val_dir, f'masked2_masked_all_SoS_value_{year}.tif') for year in years]
pos_val_files = [os.path.join(pos_val_dir, f'masked2_masked_all_PoS_value_{year}.tif') for year in years]

# 创建输出目录
output_dir = r'D:\MODIS43A4_2024\ROG'
os.makedirs(output_dir, exist_ok=True)

# 遍历每一年
for year, (sos_doy_file, pos_doy_file, sos_val_file, pos_val_file) in enumerate(zip(sos_doy_files, pos_doy_files, sos_val_files, pos_val_files), start=2001):
    try:
        # 打开所有四个文件
        with rasterio.open(sos_doy_file) as src_sos_doy, \
             rasterio.open(pos_doy_file) as src_pos_doy, \
             rasterio.open(sos_val_file) as src_sos_val, \
             rasterio.open(pos_val_file) as src_pos_val:

            # 读取数据（假设都是单波段）
            sos_doy = src_sos_doy.read(1).astype('float32')
            pos_doy = src_pos_doy.read(1).astype('float32')
            sos_val = src_sos_val.read(1).astype('float32')
            pos_val = src_pos_val.read(1).astype('float32')

            # 获取元数据（使用任意一个源，如 SOS DOY）
            out_meta = src_sos_doy.meta.copy()
            out_meta.update(dtype='float32')

            # 创建有效掩膜：所有四个变量均不为 -9999 且不为 0（视具体情况而定）
            valid_mask = (
                (sos_doy != -9999) & (sos_doy > 0) &
                (pos_doy != -9999) & (pos_doy > 0) &
                (sos_val != -9999) &
                (pos_val != -9999)
            )

            # 初始化 AOG 结果数组
            aog_data = np.full_like(sos_doy, -9999.0, dtype='float32')

            # 计算时间差和绿度差
            doy_diff = pos_doy[valid_mask] - sos_doy[valid_mask]
            val_diff = pos_val[valid_mask] - sos_val[valid_mask]

            # 避免除以零或负值
            positive_doy_diff = doy_diff > 0

            # 只在时间差大于 0 的情况下计算 AOG
            aog_valid_mask = valid_mask.copy()
            aog_valid_mask[valid_mask] &= positive_doy_diff

            # 执行计算
            aog_data[aog_valid_mask] = val_diff[positive_doy_diff] / doy_diff[positive_doy_diff]

            # 保存结果
            output_file = os.path.join(output_dir, f'ROG_{year}.tif')
            with rasterio.open(output_file, 'w', **out_meta) as dst:
                dst.write(aog_data, 1)

        print(f"成功生成 {year} 年的 AOG 文件: {output_file}")

    except Exception as e:
        print(f"处理 {year} 年的数据时出错: {e}")