import os
import rasterio
import numpy as np

# 定义路径
mask_path = r'F:\MODIS43A4_DOY\output_masked_resampled.tif'
output_dir = r'D:\MOD12Q2\vs\classai'

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)

# 打开mask文件
with rasterio.open(mask_path) as mask_src:
    mask_data = mask_src.read(1)
    mask_nodata = mask_src.nodata

    # 创建输出文件的元数据
    out_meta = mask_src.meta.copy()
    out_meta.update({
        'driver': 'GTiff',
        'dtype': rasterio.uint8,  # 设置数据类型为uint8
        'nodata': 255  # 设置nodata值为255
    })

    # 处理nodata值
    resampled_mask_data = np.where(mask_data == mask_nodata, np.nan, mask_data).astype(np.float32)

    # 定义四个区域的条件
    region_masks = [
        (resampled_mask_data < 500),
        ((resampled_mask_data >= 500) & (resampled_mask_data < 2000)),
        ((resampled_mask_data >= 2000) & (resampled_mask_data < 5000)),
        ((resampled_mask_data >= 5000) & (resampled_mask_data < 6500))
    ]

    # 分别保存每个区域的掩膜
    region_names = ['lt_500', 'gte_500_lte_2000', 'gte_2000_lte_5000', 'gte_5000_lt_6500']
    for i, mask_cond in enumerate(region_masks):
        region_data = np.where(mask_cond, 1, 0).astype(np.uint8)
        region_data[np.isnan(resampled_mask_data)] = out_meta['nodata']

        output_file = os.path.join(output_dir, f'region_{region_names[i]}.tif')
        with rasterio.open(output_file, 'w', **out_meta) as dest:
            dest.write(region_data, 1)

print("Region masks have been saved to", output_dir)



