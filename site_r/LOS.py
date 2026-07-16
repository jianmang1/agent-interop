import os
import rasterio
import numpy as np

# 定义路径和年份范围
sos_dir = r'D:\MODIS43A4_2024\SOS2'
eos_dir = r'D:\MODIS43A4_2024\EOS2'
years = range(2001, 2025)

# 构建文件路径列表
sos_files = [os.path.join(sos_dir, f'masked2_masked_all_SoS_DOY_{year}.tif') for year in years]
eos_files = [os.path.join(eos_dir, f'masked2_masked_all_EoS_DOY_{year}.tif') for year in years]

# 创建输出目录
output_dir = r'D:\MODIS43A4_2024\LOS'
os.makedirs(output_dir, exist_ok=True)

# 遍历每一对 SOS 和 EOS 文件
for year, (sos_file, eos_file) in zip(years, zip(sos_files, eos_files)):
    try:
        # 打开 SOS 和 EOS 文件
        with rasterio.open(sos_file) as sos_src, rasterio.open(eos_file) as eos_src:
            # 读取数据
            sos_data = sos_src.read(1).astype('float32')
            eos_data = eos_src.read(1).astype('float32')

            # 创建掩膜，排除无效值 -9999 和 0
            mask = ((sos_data != -9999) & (sos_data != 0) & (eos_data != -9999) & (eos_data != 0))

            # 计算 LOS（EOS - SOS）
            # 计算 LOS（EOS - SOS）
            los_data = np.full_like(sos_data, -9999.0, dtype='float32')  # 初始化为无效值
            los_data[mask] = eos_data[mask] - sos_data[mask]
            los_data[los_data <= 0] = -9999.0

            # 使用 SOS 文件的元数据作为模板
            out_meta = sos_src.meta.copy()
            out_meta.update(dtype=rasterio.float32)  # 更新为 float32 类型以支持无效值

            # 保存结果到新的 TIFF 文件
            output_file = os.path.join(output_dir, f'LOS_{year}.tif')
            with rasterio.open(output_file, 'w', **out_meta) as dst:
                dst.write(los_data, 1)

        print(f"成功生成 {year} 年的 LOS 文件: {output_file}")

    except Exception as e:
        print(f"处理 {year} 年的数据时出错: {e}")