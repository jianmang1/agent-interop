import geopandas as gpd
from rasterio.mask import mask
import rasterio
from rasterio.io import MemoryFile
import numpy as np
import os
from shapely.geometry import mapping
from rasterio.features import geometry_mask


def clip_and_extract_remainder(shp_path, tif_path, clipped_output_path, remainder_output_path):
    """
    使用shapefile裁剪tif文件，并同时输出裁剪部分和剩余部分

    参数:
    shp_path: shapefile文件路径
    tif_path: 待裁剪的tif文件路径
    clipped_output_path: 输出裁剪部分文件的路径
    remainder_output_path: 输出剩余部分文件的路径
    """
    try:
        # 读取shapefile
        print("正在读取shapefile...")
        gdf = gpd.read_file(shp_path)

        # 读取tif文件
        print("正在读取tif文件...")
        with rasterio.open(tif_path) as src:
            # 获取tif的坐标参考系统
            crs = src.crs
            print(f"原始tif的坐标系统: {crs}")

            # 检查shapefile和tif的坐标系统是否一致
            if gdf.crs != crs:
                print(f"坐标系统不一致，正在转换shapefile的坐标系统...")
                gdf = gdf.to_crs(crs)

            # 将几何体转换为GeoJSON格式用于裁剪
            geometries = gdf.geometry
            print(f"找到 {len(geometries)} 个几何体")

            # 读取原始tif数据
            with rasterio.open(tif_path) as src:
                # 1. 裁剪出感兴趣区域
                print("正在进行感兴趣区域裁剪...")
                clipped_image, clipped_transform = mask(
                    dataset=src,
                    shapes=geometries,
                    crop=True,  # 裁剪到最小边界框
                    nodata=src.nodata if src.nodata is not None else 0
                )

                # 获取原始元数据
                clipped_meta = src.meta.copy()

                # 更新裁剪部分元数据
                clipped_meta.update({
                    "driver": "GTiff",
                    "height": clipped_image.shape[1],
                    "width": clipped_image.shape[2],
                    "transform": clipped_transform
                })

                # 2. 计算剩余部分 - 创建反向掩膜
                print("正在计算剩余区域...")

                # 读取完整影像
                full_image = src.read()
                full_transform = src.transform
                full_meta = src.meta.copy()

                # 创建反向掩膜（剩余部分）
                # 首先创建原始掩膜
                mask_img = geometry_mask(
                    geometries,
                    out_shape=(src.height, src.width),
                    transform=src.transform,
                    invert=True  # True表示在几何体内部为True
                )

                # 创建反向掩膜（在几何体外部为True）
                inverse_mask = ~mask_img

                # 应用反向掩膜到影像数据
                remainder_image = full_image.copy()
                if src.nodata is not None:
                    # 将感兴趣区域设为nodata值
                    for band_idx in range(remainder_image.shape[0]):
                        remainder_image[band_idx, inverse_mask] = src.nodata
                else:
                    # 如果没有nodata值，将感兴趣区域设为0
                    for band_idx in range(remainder_image.shape[0]):
                        remainder_image[band_idx, inverse_mask] = 0

                # 保存裁剪后的感兴趣区域
                print("正在保存裁剪结果...")
                with rasterio.open(clipped_output_path, "w", **clipped_meta) as dest:
                    dest.write(clipped_image)

                # 保存剩余部分
                print("正在保存剩余区域结果...")
                with rasterio.open(remainder_output_path, "w", **full_meta) as dest:
                    dest.write(remainder_image)

                print(f"裁剪完成！")
                print(f"感兴趣区域已保存至: {clipped_output_path}")
                print(f"剩余区域已保存至: {remainder_output_path}")
                print(f"裁剪后感兴趣区域尺寸: {clipped_image.shape}")
                print(f"剩余区域尺寸: {remainder_image.shape}")

                # 输出一些统计信息
                clipped_valid_data = clipped_image[
                    clipped_image != src.nodata] if src.nodata is not None else clipped_image
                remainder_valid_data = remainder_image[remainder_image != src.nodata] if src.nodata is not None else \
                remainder_image[remainder_image != 0]

                if clipped_valid_data.size > 0:
                    print(f"感兴趣区域有效数据范围: {clipped_valid_data.min():.2f} ~ {clipped_valid_data.max():.2f}")
                    print(f"感兴趣区域有效数据平均值: {clipped_valid_data.mean():.2f}")

                if remainder_valid_data.size > 0:
                    print(f"剩余区域有效数据范围: {remainder_valid_data.min():.2f} ~ {remainder_valid_data.max():.2f}")
                    print(f"剩余区域有效数据平均值: {remainder_valid_data.mean():.2f}")

    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        raise


def clip_and_extract_remainder_optimized(shp_path, tif_path, clipped_output_path, remainder_output_path):
    """
    使用shapefile裁剪tif文件，并同时输出裁剪部分和剩余部分（优化版本）

    参数:
    shp_path: shapefile文件路径
    tif_path: 待裁剪的tif文件路径
    clipped_output_path: 输出裁剪部分文件的路径
    remainder_output_path: 输出剩余部分文件的路径
    """
    try:
        # 读取shapefile
        print("正在读取shapefile...")
        gdf = gpd.read_file(shp_path)

        # 读取tif文件
        print("正在读取tif文件...")
        with rasterio.open(tif_path) as src:
            # 获取tif的坐标参考系统
            crs = src.crs
            print(f"原始tif的坐标系统: {crs}")

            # 检查shapefile和tif的坐标系统是否一致
            if gdf.crs != crs:
                print(f"坐标系统不一致，正在转换shapefile的坐标系统...")
                gdf = gdf.to_crs(crs)

            # 将几何体转换为GeoJSON格式用于裁剪
            geometries = gdf.geometry
            print(f"找到 {len(geometries)} 个几何体")

            # 读取原始tif数据
            with rasterio.open(tif_path) as src:
                # 1. 裁剪出感兴趣区域
                print("正在进行感兴趣区域裁剪...")
                clipped_image, clipped_transform = mask(
                    dataset=src,
                    shapes=geometries,
                    crop=True,  # 裁剪到最小边界框
                    nodata=src.nodata if src.nodata is not None else 0
                )

                # 获取原始元数据
                clipped_meta = src.meta.copy()

                # 更新裁剪部分元数据
                clipped_meta.update({
                    "driver": "GTiff",
                    "height": clipped_image.shape[1],
                    "width": clipped_image.shape[2],
                    "transform": clipped_transform
                })

                # 保存裁剪后的感兴趣区域
                print("正在保存感兴趣区域结果...")
                with rasterio.open(clipped_output_path, "w", **clipped_meta) as dest:
                    dest.write(clipped_image)

                # 2. 计算剩余部分
                print("正在计算并保存剩余区域...")

                # 重新读取完整的tif数据
                with rasterio.open(tif_path) as src_full:
                    full_image = src_full.read()  # (bands, height, width)

                    # 创建一个与原始影像同样大小的掩膜
                    mask_img = geometry_mask(
                        geometries,
                        out_shape=(src_full.height, src_full.width),
                        transform=src_full.transform,
                        invert=True  # True表示在几何体内部为True
                    )

                    # 创建反向掩膜（在几何体外部为True的部分设为感兴趣区域，内部为剩余区域）
                    inverse_mask = ~mask_img  # 在几何体内部为False，外部为True

                    # 创建剩余区域影像 - 将感兴趣区域设为nodata值
                    remainder_image = full_image.copy()

                    # 对每个波段应用掩膜
                    for band_idx in range(remainder_image.shape[0]):
                        remainder_image[band_idx, mask_img] = src_full.nodata if src_full.nodata is not None else 0

                # 保存剩余部分
                print("正在保存剩余区域结果...")
                with rasterio.open(remainder_output_path, "w", **src.meta) as dest:
                    dest.write(remainder_image)

                print(f"裁剪完成！")
                print(f"感兴趣区域已保存至: {clipped_output_path}")
                print(f"剩余区域已保存至: {remainder_output_path}")
                print(f"感兴趣区域尺寸: {clipped_image.shape}")
                print(f"原始影像尺寸: {src.width}x{src.height}")

                # 输出一些统计信息
                clipped_valid_data = clipped_image[
                    clipped_image != src.nodata] if src.nodata is not None else clipped_image
                if clipped_valid_data.size > 0:
                    print(f"感兴趣区域有效数据范围: {clipped_valid_data.min():.2f} ~ {clipped_valid_data.max():.2f}")
                    print(f"感兴趣区域有效数据平均值: {clipped_valid_data.mean():.2f}")

                remainder_valid_data = remainder_image[remainder_image != src.nodata] if src.nodata is not None else \
                remainder_image[remainder_image != 0]
                if remainder_valid_data.size > 0:
                    print(f"剩余区域有效数据范围: {remainder_valid_data.min():.2f} ~ {remainder_valid_data.max():.2f}")
                    print(f"剩余区域有效数据平均值: {remainder_valid_data.mean():.2f}")

    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        raise


# 使用示例
if __name__ == "__main__":
    # 输入文件路径
    shp_path = r"D:\青藏高原边界\青藏高原1_100万行政边界数据（2017）\青藏高原1_100万行政边界数据（2017）\Admin Boundaries poly Tibet\City_Tibet.shp"
    tif_path = r"D:\数据\DEM\resampled_dem.tif"

    # 输出文件路径
    clipped_output_path = r"D:\数据\DEM\resampled_dem_青藏高原.tif"
    remainder_output_path = r"D:\数据\DEM\resampled_dem_除青藏高原.tif"

    # 确保输出目录存在
    for output_path in [clipped_output_path, remainder_output_path]:
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    # 执行裁剪并提取剩余部分
    clip_and_extract_remainder_optimized(shp_path, tif_path, clipped_output_path, remainder_output_path)



