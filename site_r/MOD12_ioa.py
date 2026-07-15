import os
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject, calculate_default_transform  # 从 rasterio.warp 导入 reproject

# 定义输入和输出路径
input_dir = r'D:\\MOD12Q2\\MCD12Q2_SOS'
output_dir = r'D:\\MOD12Q2\\MCD12Q2_SOS_masked'  # 创建一个新的文件夹用于存放掩膜后的文件
mask_file = r'D:\数据\AI\Global-AI_ET0_v3_annual\mask_less_than_6500.tif'

# 如果输出目录不存在，则创建它
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 选择一个目标文件作为参考，这里我们选择2001年的SOS文件
reference_file = os.path.join(input_dir, 'SOS_MCD12Q2_2001.tif')

# 打开参考文件以获取其元数据
with rasterio.open(reference_file) as ref:
    ref_transform = ref.transform
    ref_width = ref.width
    ref_height = ref.height
    ref_crs = ref.crs

# 重采样掩膜文件
# 重采样掩膜文件，并保存重采样后的掩膜
def resample_mask_to_reference(mask_file, ref_transform, ref_width, ref_height, ref_crs):
    with rasterio.open(mask_file) as src:
        mask_data = src.read(1)
        mask_nodata = src.nodata
        mask_crs = src.crs

        # 创建一个内存中的文件来保存重采样的结果
        profile = src.profile.copy()
        profile.update(
            driver='GTiff',
            height=ref_height,
            width=ref_width,
            transform=ref_transform,
            crs=ref_crs
        )

        # 重采样掩膜数据
        destination = np.zeros((ref_height, ref_width), dtype=mask_data.dtype)
        reproject(
            source=rasterio.band(src, 1),
            destination=destination,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=ref_transform,
            dst_crs=ref_crs,
            resampling=Resampling.bilinear
        )

        # 定义输出的掩膜文件路径
        output_mask_file = os.path.join(output_dir, 'D:\\MOD12Q2\\resampled_mask.tif')

        # 使用rasterio保存重采样后的掩膜
        with rasterio.open(output_mask_file, 'w', **profile) as dst:
            dst.write(destination.astype(profile['dtype']), 1)

        return destination, mask_nodata

# 重采样并获取掩膜数据
resampled_mask, mask_nodata = resample_mask_to_reference(mask_file, ref_transform, ref_width, ref_height, ref_crs)

# 确定掩膜中有效像元的位置
valid_pixels = resampled_mask != mask_nodata  # 假设有效像元是不等于NoData值的像元

# 对每个 TIFF 文件应用掩膜
for year in range(2001, 2024):  # 假设2023年是最新的年份
    input_file = os.path.join(input_dir, f'SOS_MCD12Q2_{year}.tif')
    output_file = os.path.join(output_dir, f'SOS_MCD12Q2_{year}_masked.tif')

    with rasterio.open(input_file) as src:
        sos_data = src.read(1)  # 假设SOS图层也只有一个波段
        sos_nodata = src.nodata
        out_image = np.where(valid_pixels, sos_data, sos_nodata)  # 使用numpy.where函数根据掩膜选择像元
        out_meta = src.meta.copy()

    # 更新元数据
    out_meta.update({"driver": "GTiff"})

    # 写入掩膜后的数据到新文件
    with rasterio.open(output_file, "w", **out_meta) as dest:
        dest.write(out_image, 1)

print("掩膜操作完成")