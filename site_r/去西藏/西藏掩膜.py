import geopandas as gpd
from rasterio.features import geometry_mask
from rasterio.transform import from_bounds
import rasterio
import numpy as np


def geojson_to_tif(geojson_path, output_tif_path, resolution=0.01):
    """
    将GeoJSON文件转换为TIFF文件

    参数:
    geojson_path: GeoJSON文件路径
    output_tif_path: 输出TIFF文件路径
    resolution: 分辨率（经纬度单位）
    """

    # 读取GeoJSON文件
    gdf = gpd.read_file(geojson_path)

    # 获取边界框
    minx, miny, maxx, maxy = gdf.total_bounds

    # 计算图像尺寸
    width = int((maxx - minx) / resolution)
    height = int((maxy - miny) / resolution)

    # 创建仿射变换矩阵
    transform = from_bounds(minx, miny, maxx, maxy, width, height)

    # 创建二进制掩膜 - 移除fill参数，使用shapes参数
    mask = geometry_mask(
        gdf.geometry,
        out_shape=(height, width),
        transform=transform,
        invert=True
    )

    # 写入TIFF文件
    with rasterio.open(
            output_tif_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=rasterio.uint8,
            crs=gdf.crs,
            transform=transform,
    ) as dst:
        dst.write(mask.astype(rasterio.uint8), 1)


# 使用示例
if __name__ == "__main__":
    input_path = r"D:\MODIS43A4_2024\西藏\西藏自治区_省.geojson"
    output_path = r"D:\MODIS43A4_2024\西藏\西藏自治区_省.tif"

    try:
        geojson_to_tif(input_path, output_path)
        print(f"成功将 {input_path} 转换为 {output_path}")
    except Exception as e:
        print(f"转换过程中出现错误: {e}")
        print("请检查:")
        print("1. 文件路径是否正确")
        print("2. GeoJSON文件是否存在")
        print("3. 输出目录是否有写入权限")
        print("4. 是否已安装geopandas和rasterio库")
        print("5. GeoJSON文件格式是否正确")