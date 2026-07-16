import rasterio
from rasterio.transform import Affine
from rasterio.enums import Resampling

# 设置输入输出路径
input_raster = r'D:\数据\AI\Global-AI_ET0_v3_annual\output_cropped.tif'
output_raster = r'D:\数据\AI\Global-AI_ET0_v3_annual\mask_less_than_6500.tif'
reference_raster = r'D:\MODIS43A4_2024\EOS\500M\all_EoS_DOY_2000.tif'

default_nodata = 0

# 打开输入栅格文件和参考栅格文件
with rasterio.open(input_raster) as src, rasterio.open(reference_raster) as ref:
    # 读取栅格数据和相关属性
    image = src.read(1)
    profile = src.profile

    # 获取参考栅格的元数据
    ref_profile = ref.profile
    ref_transform = ref.profile['transform']
    ref_width = ref.profile['width']
    ref_height = ref.profile['height']
    ref_crs = ref.profile['crs']

    # 如果源文件没有nodata值，则使用默认值
    nodata_value = default_nodata if src.nodata is None else src.nodata

    # 重新采样图像到参考栅格的分辨率
    data_resampled = src.read(
        1,
        out_shape=(ref_height, ref_width),
        resampling=Resampling.bilinear,
    )

    # 创建掩膜：选择值小于6500的像元
    mask = data_resampled < 6500
    masked_image = data_resampled.copy()
    masked_image[~mask] = nodata_value

    # 更新profile以匹配新文件的要求
    profile.update({
        'dtype': masked_image.dtype,
        'height': ref_height,
        'width': ref_width,
        'transform': ref_transform,
        'crs': ref_crs,
        'compress': 'lzw',
        'nodata': nodata_value
    })

    # 保存为新的TIF文件
    with rasterio.open(output_raster, 'w', **profile) as dst:
        dst.write(masked_image, 1)

print("New TIF file has been created successfully.")