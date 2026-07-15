import os
import rasterio
import numpy as np

# 定义路径和年份范围
pos_doy_dir = r'D:\MODIS43A4_2024\POS2'           # POS DOY 文件路径
eos_doy_dir = r'D:\MODIS43A4_2024\EOS2'           # EOS DOY 文件路径
pos_val_dir = r'D:\MODIS43A4_Value\POS'           # POS Value 文件路径
eos_val_dir = r'D:\MODIS43A4_Value\EOS'           # EOS Value 文件路径

years = range(2001, 2025)

# 构建文件路径列表
pos_doy_files = [os.path.join(pos_doy_dir, f'masked2_masked_all_PoS_DOY_{year}.tif') for year in years]
eos_doy_files = [os.path.join(eos_doy_dir, f'masked2_masked_all_EoS_DOY_{year}.tif') for year in years]
pos_val_files = [os.path.join(pos_val_dir, f'masked2_masked_all_PoS_Value_{year}.tif') for year in years]
eos_val_files = [os.path.join(eos_val_dir, f'masked2_masked_all_EoS_Value_{year}.tif') for year in years]

# 创建输出目录
output_dir = r'D:\MODIS43A4_2024\ROS'
os.makedirs(output_dir, exist_ok=True)

# 遍历每一年
for year, (pos_doy_file, eos_doy_file, pos_val_file, eos_val_file) in enumerate(zip(pos_doy_files, eos_doy_files, pos_val_files, eos_val_files), start=2001):
    try:
        # 打开所有四个文件
        with rasterio.open(pos_doy_file) as src_pos_doy, \
             rasterio.open(eos_doy_file) as src_eos_doy, \
             rasterio.open(pos_val_file) as src_pos_val, \
             rasterio.open(eos_val_file) as src_eos_val:

            # 读取数据（假设都是单波段）
            pos_doy = src_pos_doy.read(1).astype('float32')
            eos_doy = src_eos_doy.read(1).astype('float32')
            pos_val = src_pos_val.read(1).astype('float32')
            eos_val = src_eos_val.read(1).astype('float32')

            # 获取元数据（使用任意一个源，如 POS DOY）
            out_meta = src_pos_doy.meta.copy()
            out_meta.update(dtype='float32')

            # 创建有效掩膜：所有变量不为 -9999，且 DOY > 0
            valid_mask = (
                (pos_doy != -9999) & (pos_doy > 0) &
                (eos_doy != -9999) & (eos_doy > 0) &
                (pos_val != -9999) &
                (eos_val != -9999)
            )

            # 初始化 ROS 结果数组
            ros_data = np.full_like(pos_doy, -9999.0, dtype='float32')

            # 计算时间差和绿度差
            doy_diff = eos_doy[valid_mask] - pos_doy[valid_mask]  # 应该为正（EOS 在 POS 之后）
            val_diff = pos_val[valid_mask]-eos_val[valid_mask]  # 正

            # 只考虑时间差为正的情况（合理的时间顺序）
            positive_doy_diff = doy_diff > 0

            # 合并掩膜
            ros_valid_mask = valid_mask.copy()
            ros_valid_mask[valid_mask] &= positive_doy_diff

            # 计算 ROS
            ros_data[ros_valid_mask] = val_diff[positive_doy_diff] / doy_diff[positive_doy_diff]

            # 保存结果
            output_file = os.path.join(output_dir, f'ROS_{year}.tif')
            with rasterio.open(output_file, 'w', **out_meta) as dst:
                dst.write(ros_data, 1)

        print(f"成功生成 {year} 年的 ROS 文件: {output_file}")

    except Exception as e:
        print(f"处理 {year} 年的数据时出错: {e}")