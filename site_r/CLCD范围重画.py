import os
from osgeo import gdal


def clip_clcd_to_reference_range():
    """
    将指定年份的CLCD影像批量裁剪至参考文件的空间范围，输出到原目录
    扩展边界像元设为-9999
    """
    # 设置输入路径
    input_folder = r"F:\转变\masked_CLCD"
    reference_file = r"D:\MODIS43A4_2024\masked_without_tibet\SOS2\mean_values.tif"

    # 明确指定要处理的年份范围
    years = list(range(2001, 2023))  # 2001到2022
    clcd_files = []

    for year in years:
        filename = f"masked_CLCD_v01_{year}.tif"
        filepath = os.path.join(input_folder, filename)
        if os.path.exists(filepath):
            clcd_files.append(filepath)
        else:
            print(f"警告: 文件不存在 - {filename}")

    if not clcd_files:
        print(f"未找到任何指定的CLCD文件")
        return

    # 获取参考文件的空间范围
    ref_ds = gdal.Open(reference_file)
    if ref_ds is None:
        print(f"无法打开参考文件: {reference_file}")
        return

    ref_geotransform = ref_ds.GetGeoTransform()
    ref_projection = ref_ds.GetProjection()

    # 计算参考文件的边界坐标
    ref_x_min = ref_geotransform[0]
    ref_y_max = ref_geotransform[3]
    ref_x_max = ref_geotransform[0] + ref_geotransform[1] * ref_ds.RasterXSize
    ref_y_min = ref_geotransform[3] + ref_geotransform[5] * ref_ds.RasterYSize

    ref_ds = None  # 关闭数据集

    print(f"参考文件空间范围:")
    print(f"X范围: {ref_x_min} 到 {ref_x_max}")
    print(f"Y范围: {ref_y_min} 到 {ref_y_max}")

    print(f"找到 {len(clcd_files)} 个CLCD文件")

    # 批量裁剪
    for clcd_file in clcd_files:
        print(f"\n正在处理: {os.path.basename(clcd_file)}")

        # 生成输出文件名
        base_name = os.path.splitext(os.path.basename(clcd_file))[0]
        output_filename = os.path.join(
            input_folder,
            f"{base_name}_FINAL.tif"
        )

        try:
            # 获取原始影像的信息用于保持一致性
            ds = gdal.Open(clcd_file)
            if ds is None:
                print(f"  跳过无法打开的文件: {clcd_file}")
                continue

            # 获取原始影像的空间信息
            original_projection = ds.GetProjection()
            original_geotransform = ds.GetGeoTransform()
            original_datatype = ds.GetRasterBand(1).DataType
            ds = None  # 关闭数据集

            # 使用gdal.Warp进行裁剪，扩展边界像元设为-9999
            warp_options = gdal.WarpOptions(
                outputBounds=[ref_x_min, ref_y_min, ref_x_max, ref_y_max],
                dstSRS=original_projection,
                cropToCutline=True,
                targetAlignedPixels=True,
                xRes=abs(original_geotransform[1]),
                yRes=abs(original_geotransform[5]),
                srcNodata=-9999,
                dstNodata=-9999
            )

            gdal.Warp(output_filename, clcd_file, options=warp_options)

            print(f"  已保存: {output_filename}")

        except Exception as e:
            print(f"  处理失败: {str(e)}")

    print(f"\n批量裁剪完成！输出文件保存在: {input_folder}")


def main():
    """
    主函数
    """
    print("开始批量裁剪CLCD影像...")
    clip_clcd_to_reference_range()
    print("任务完成！")


if __name__ == "__main__":
    main()
