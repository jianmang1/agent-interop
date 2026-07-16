import os
import rasterio
from rasterio.features import geometry_mask
import geopandas as gpd
import numpy as np


def mask_tibet_region(input_raster_path, output_raster_path, tibet_geojson_path):
    """
    使用西藏自治区边界对输入栅格进行掩膜处理，
    将西藏区域内的像元设为NaN，保留其他区域
    """
    # 读取西藏边界矢量文件
    tibet_gdf = gpd.read_file(tibet_geojson_path)

    # 打开输入栅格文件
    with rasterio.open(input_raster_path) as src:
        # 读取栅格数据
        data = src.read()  # (bands, height, width)

        # 获取栅格的空间信息
        transform = src.transform
        height = src.height
        width = src.width

        # 确保矢量数据与栅格具有相同坐标系
        if tibet_gdf.crs != src.crs:
            tibet_gdf = tibet_gdf.to_crs(src.crs)

        # 创建掩膜：西藏区域内为True，区域外为False
        tibet_mask = geometry_mask(
            tibet_gdf.geometry,
            transform=transform,
            out_shape=(height, width),
            invert=True  # invert=True使几何体内部为True
        )

        # 将数据转换为float32以支持NaN
        if data.dtype != np.float32:
            processed_data = data.astype(np.float32)
        else:
            processed_data = data.copy()

        # 将西藏区域内的像元设为NaN
        if len(processed_data.shape) == 3:  # 多波段
            for i in range(processed_data.shape[0]):
                processed_data[i, tibet_mask] = np.nan
        else:  # 单波段
            processed_data[tibet_mask] = np.nan

        # 更新输出配置
        profile = src.profile.copy()
        profile.update({
            'dtype': 'float32',
            'nodata': np.nan
        })

        # 写入输出文件
        with rasterio.open(output_raster_path, 'w', **profile) as dst:
            dst.write(processed_data)


def main():
    # 定义文件路径
    input_raster = r"E:\Desktop\mai\LOS\mean_values.tif"
    output_raster = r"E:\Desktop\mai\LOS\mean_values_1.tif"
    tibet_boundary = r"E:\Desktop\mai\西藏\西藏自治区_省.geojson"

    print("开始处理栅格文件...")
    print(f"输入文件: {input_raster}")
    print(f"输出文件: {output_raster}")
    print(f"西藏边界文件: {tibet_boundary}")

    # 检查输入文件是否存在
    if not os.path.exists(input_raster):
        print(f"错误: 输入栅格文件不存在 - {input_raster}")
        return

    if not os.path.exists(tibet_boundary):
        print(f"错误: 西藏边界文件不存在 - {tibet_boundary}")
        return

    try:
        # 执行掩膜处理
        mask_tibet_region(input_raster, output_raster, tibet_boundary)
        print("处理完成！")
        print(f"输出文件已保存至: {output_raster}")
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")


if __name__ == "__main__":
    main()
