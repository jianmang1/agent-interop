import os
import rasterio
import numpy as np

# 定义路径
mask_path = r'F:\转变\masked_CLCD\masked_CLCD_v01_2020_FINAL.tif'
output_dir = r'D:\MOD12Q2\vs\classai\plant'

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)

# 打开mask文件
with rasterio.open(mask_path) as mask_src:
    mask_data = mask_src.read(1)
    mask_nodata = mask_src.nodata  # 获取原图的nodata值

    # 创建输出文件的元数据
    out_meta = mask_src.meta.copy()
    out_meta.update({
        'driver': 'GTiff',
        'dtype': rasterio.uint8,  # 设置数据类型为uint8
        'nodata': 255  # 设置nodata值为255
    })

    # 识别原图中的-9999值并将其作为nodata处理
    # 将mask_data中的-9999值也标记为nodata
    processed_mask_data = mask_data.astype(np.float32)
    processed_mask_data[processed_mask_data == -9999] = np.nan

    # 定义四个区域的条件（根据像元值1,2,3,4分类）
    region_masks = [
        (processed_mask_data == 1),
        (processed_mask_data == 2),
        (processed_mask_data == 3),
        (processed_mask_data == 4),
        (processed_mask_data == 7)

    ]

    # 分别保存每个区域的掩膜
    region_names = ['1', '2', '3', '4', '7']
    for i, mask_cond in enumerate(region_masks):
        region_data = np.where(mask_cond, 1, 0).astype(np.uint8)
        # 将nan值（原图中的nodata和-9999）设置为输出nodata值
        region_data[np.isnan(processed_mask_data)] = out_meta['nodata']

        output_file = os.path.join(output_dir, f'{region_names[i]}.tif')
        with rasterio.open(output_file, 'w', **out_meta) as dest:
            dest.write(region_data, 1)

print("Region masks have been saved to", output_dir)



