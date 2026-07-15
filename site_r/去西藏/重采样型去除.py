import os
import rasterio
from rasterio.features import geometry_mask
import geopandas as gpd
import numpy as np


def mask_tibet_region_chunked(input_raster_path, output_raster_path, tibet_geojson_path, chunk_size=1000):
    """
    使用西藏自治区边界对输入栅格进行掩膜处理（分块处理），
    将西藏区域内的像元设为NaN，保留其他区域
    """
    # 读取西藏边界矢量文件
    tibet_gdf = gpd.read_file(tibet_geojson_path)

    # 打开输入栅格文件
    with rasterio.open(input_raster_path) as src:
        # 确保矢量数据与栅格具有相同坐标系
        if tibet_gdf.crs != src.crs:
            tibet_gdf = tibet_gdf.to_crs(src.crs)

        # 计算整个栅格的掩膜（使用较小的内存占用方式）
        height = src.height
        width = src.width

        # 更新输出配置
        profile = src.profile.copy()
        profile.update({
            'dtype': 'float32',
            'nodata': np.nan
        })

        # 创建输出文件
        with rasterio.open(output_raster_path, 'w', **profile) as dst:
            # 分块处理
            for i in range(0, height, chunk_size):
                for j in range(0, width, chunk_size):
                    # 计算当前块的边界
                    row_end = min(i + chunk_size, height)
                    col_end = min(j + chunk_size, width)

                    # 读取当前块的数据
                    chunk_data = src.read(window=((i, row_end), (j, col_end)))

                    # 为当前块创建掩膜
                    chunk_transform = src.window_transform(((i, row_end), (j, col_end)))
                    chunk_height = row_end - i
                    chunk_width = col_end - j

                    # 创建当前块的西藏掩膜
                    chunk_tibet_mask = geometry_mask(
                        tibet_gdf.geometry,
                        transform=chunk_transform,
                        out_shape=(chunk_height, chunk_width),
                        invert=True  # invert=True使几何体内部为True
                    )

                    # 将数据转换为float32以支持NaN
                    if chunk_data.dtype != np.float32:
                        chunk_processed_data = chunk_data.astype(np.float32)
                    else:
                        chunk_processed_data = chunk_data.copy()

                    # 将西藏区域内的像元设为NaN
                    if len(chunk_processed_data.shape) == 3:  # 多波段
                        for band_idx in range(chunk_processed_data.shape[0]):
                            chunk_processed_data[band_idx, chunk_tibet_mask] = np.nan
                    else:  # 单波段
                        chunk_processed_data[chunk_tibet_mask] = np.nan

                    # 写入当前块到输出文件
                    dst.write(chunk_processed_data, window=((i, row_end), (j, col_end)))


def main():
    # 定义文件路径
    input_raster = r"D:\中科院class\3.tif"
    output_raster = r"D:\中科院class\3_masked.tif"
    tibet_boundary = r"D:\MODIS43A4_2024\西藏\西藏自治区_省.geojson"

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
        print("正在处理（分块进行，可能需要较长时间）...")
        mask_tibet_region_chunked(input_raster, output_raster, tibet_boundary)
        print("处理完成！")
        print(f"输出文件已保存至: {output_raster}")
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")


if __name__ == "__main__":
    main()
