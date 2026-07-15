import os
import rasterio
from rasterio.plot import reshape_as_raster
import numpy as np
from rasterio.transform import from_origin

# 定义模板路径
sos_template = r"D:\MODIS43A4_2024\SOS\500m(unmask0)\masked2_masked_all_SoS_DOY_{year}.tif"
eos_template = r"D:\MODIS43A4_2024\EOS\500M\masked2_masked_all_EoS_DOY_{year}.tif"
pos_template = r"D:\MODIS43A4_2024\POS\unmask0\masked2_masked_all_PoS_DOY_{year}.tif"

# 年份范围
years = range(2001, 2025)

# 输出目录
output_dir = r"D:\MODIS43A4_2024\MULTIBAND"
os.makedirs(output_dir, exist_ok=True)

# 遍历每个年份
for year in years:
    # 替换模板中的 {year} 占位符
    sos_path = sos_template.format(year=year)
    eos_path = eos_template.format(year=year)
    pos_path = pos_template.format(year=year)

    # 检查文件是否存在
    if not (os.path.exists(sos_path) and os.path.exists(eos_path) and os.path.exists(pos_path)):
        print(f"文件缺失：{year}")
        continue

    # 打开三个单波段图像
    with rasterio.open(sos_path) as sos_src, \
            rasterio.open(eos_path) as eos_src, \
            rasterio.open(pos_path) as pos_src:

        # 读取数据为 NumPy 数组
        sos_data = sos_src.read(1)  # SOS 波段
        eos_data = eos_src.read(1)  # EOS 波段
        pos_data = pos_src.read(1)  # POS 波段

        # 合并为多波段数组 (bands, height, width)
        multiband_data = np.stack([sos_data, pos_data, eos_data], axis=0)

        # 获取元数据（从 SOS 文件中复制）
        out_meta = sos_src.meta

        # 更新元数据以反映多波段
        out_meta.update({"count": 3})  # 设置波段数为 3

        # 输出文件路径
        output_path = os.path.join(output_dir, f"multiband_{year}.tif")

        # 写入新的多波段 TIFF 文件
        with rasterio.open(output_path, "w", **out_meta) as dst:
            dst.write(multiband_data)

        print(f"已生成：{output_path}")