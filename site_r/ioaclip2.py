import os
import rasterio
from rasterio.features import shapes
import fiona
from shapely.geometry import shape, mapping
from fiona.crs import from_epsg

# 设置输入输出路径
input_raster = r'D:\数据\AI\Global-AI_ET0_v3_annual\output_cropped.tif'
output_shapefile = r'D:\数据\AI\Global-AI_ET0_v3_annual\mask_less_than_2000.shp'

# 打开栅格文件
with rasterio.open(input_raster) as src:
    image = src.read(1)  # 假设是单波段图像
    mask = image < 2000  # 创建掩膜

    # 矢量化掩膜
    results = (
        {'properties': {'raster_val': v}, 'geometry': s}
        for i, (s, v) in enumerate(shapes(image, mask=mask, transform=src.transform))
    )

    # 保存为Shapefile
    with fiona.open(
        output_shapefile,
        'w',
        driver='ESRI Shapefile',
        crs=from_epsg(src.crs.to_epsg()),  # 确保使用正确的EPSG代码
        schema={'properties': [('raster_val', 'int')], 'geometry': 'Polygon'}
    ) as dst:
        for feat in results:
            dst.write(feat)

print("Shapefile has been created successfully.")