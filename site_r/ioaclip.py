import rasterio
from rasterio.mask import mask
import geopandas as gpd
import os

# 定义输入和输出路径
input_raster = r"D:\数据\AI\Global-AI_ET0_v3_annual\ai_v3_yr.tif"
output_raster = r"D:\数据\AI\Global-AI_ET0_v3_annual\output_cropped.tif"
shapefile_path = r"D:\数据\边界\中华人民共和国\中华人民共和国.shp"

# 读取形状文件
gdf = gpd.read_file(shapefile_path)

# 确保矢量数据的坐标系与栅格数据一致
with rasterio.open(input_raster) as src:
    # 如果需要转换坐标系，可以使用gdf.to_crs(src.crs)
    if not gdf.crs.equals(src.crs):
        print("警告：矢量数据和栅格数据的坐标系不一致。")
        gdf = gdf.to_crs(src.crs)

    # 获取掩膜几何
    shapes = [feature["geometry"] for feature in gdf.iterfeatures()]

    # 裁剪栅格
    out_image, out_transform = mask(src, shapes, crop=True)

    # 更新元数据
    out_meta = src.meta.copy()
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})

# 写入新的栅格文件
with rasterio.open(output_raster, "w", **out_meta) as dest:
    dest.write(out_image)

print(f"栅格文件已成功裁剪并保存至: {output_raster}")