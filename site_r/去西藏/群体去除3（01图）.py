import os
import rasterio
from rasterio.features import geometry_mask
import geopandas as gpd
import numpy as np


def mask_tibet_region(input_raster_path, output_raster_path, tibet_geojson_path):
    """
    使用西藏自治区边界对输入栅格进行掩膜处理，
    将西藏区域内的像元设为原图的背景值（nodata值），保留其他区域
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

        # 获取原始的nodata值
        original_nodata = src.nodata

        # 如果原始文件没有nodata值，使用默认值
        if original_nodata is None:
            # 根据数据类型设置合理的默认nodata值
            dtype_name = str(src.dtypes[0])
            if 'int8' in dtype_name:
                original_nodata = -128
            elif 'uint8' in dtype_name:
                original_nodata = 255
            elif 'int16' in dtype_name:
                original_nodata = -32768
            elif 'uint16' in dtype_name:
                original_nodata = 65535
            else:
                original_nodata = -9999  # 默认值

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

        # 将西藏区域内的像元设为原始nodata值
        processed_data = data.copy()

        if len(processed_data.shape) == 3:  # 多波段
            for i in range(processed_data.shape[0]):
                processed_data[i, tibet_mask] = original_nodata
        else:  # 单波段
            processed_data[tibet_mask] = original_nodata

        # 更新输出配置，保持原始数据类型和nodata值
        profile = src.profile.copy()
        profile.update({
            'nodata': original_nodata
        })

        # 写入输出文件
        with rasterio.open(output_raster_path, 'w', **profile) as dst:
            dst.write(processed_data)


def main():
    # 定义输入目录和输出目录
    input_directory = r"D:\MOD12Q2\vs\classai\plant"
    tibet_boundary = r"D:\MODIS43A4_2024\西藏\西藏自治区_省.geojson"

    # 生成要处理的文件列表
    files_to_process = []
    for year in range(1, 8):
        filename = f'{year}.tif'
        files_to_process.append(filename)

    print("开始批量处理栅格文件...")
    print(f"输入目录: {input_directory}")
    print(f"西藏边界文件: {tibet_boundary}")
    print(f"待处理文件数量: {len(files_to_process)}")

    # 检查西藏边界文件是否存在
    if not os.path.exists(tibet_boundary):
        print(f"错误: 西藏边界文件不存在 - {tibet_boundary}")
        return

    processed_count = 0
    error_count = 0

    for filename in files_to_process:
        input_path = os.path.join(input_directory, filename)

        # 检查输入文件是否存在
        if not os.path.exists(input_path):
            print(f"跳过（文件不存在）: {filename}")
            error_count += 1
            continue

        # 构建输出文件路径
        name_part, ext = os.path.splitext(filename)
        output_filename = f"{name_part}_masked_tibet{ext}"
        output_path = os.path.join(input_directory, output_filename)

        print(f"正在处理: {filename}")

        try:
            # 执行掩膜处理
            mask_tibet_region(input_path, output_path, tibet_boundary)
            print(f"完成: {output_filename}")
            processed_count += 1
        except Exception as e:
            print(f"处理失败 {filename}: {str(e)}")
            error_count += 1

    print("\n批量处理完成！")
    print(f"成功处理: {processed_count} 个文件")
    print(f"处理失败: {error_count} 个文件")
    print(f"输出文件已保存至: {input_directory}")


if __name__ == "__main__":
    main()
