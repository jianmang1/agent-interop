import os
import rasterio
from rasterio.enums import Resampling

# 输入和输出路径定义
input_dir = r"D:\MODIS43A4_2024\EOS"
output_dir = r"D:\MODIS43A4_2024\EOS\resample"
reference_tif = r"D:\MODIS43A4_2024\EOS\500M\all_EoS_DOY_2001.tif"

# 打开参考tif以获取其形状和变换参数
with rasterio.open(reference_tif) as ref_src:
    ref_shape = ref_src.shape  # (height, width)
    ref_transform = ref_src.transform
    ref_crs = ref_src.crs

# 遍历输入目录下的所有tif文件
for year in range(2001, 2025):
    input_tif = os.path.join(input_dir, f'all_EoS_DOY_{year}.tif')
    if not os.path.exists(input_tif):
        print(f"File {input_tif} does not exist.")
        continue

    with rasterio.open(input_tif) as src:
        data = src.read(
            out_shape=ref_shape,
            resampling=Resampling.bilinear
        )

        # 复制空间属性
        meta = src.meta.copy()
        meta.update({
            "height": ref_shape[0],
            "width": ref_shape[1],
            "transform": ref_transform,
            "crs": ref_crs
        })

        # 写入新的文件
        output_tif = os.path.join(output_dir, os.path.basename(input_tif))
        os.makedirs(os.path.dirname(output_tif), exist_ok=True)
        with rasterio.open(output_tif, 'w', **meta) as dst:
            dst.write(data)

print("处理完成")