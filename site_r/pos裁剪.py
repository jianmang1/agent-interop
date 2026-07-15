import os
from osgeo import gdal, ogr
import re


def clip_raster_with_shapefile(shp_path, input_folder, output_folder):
    """
    使用shapefile裁剪一系列栅格文件（仅限2001-2023年）

    参数:
    shp_path: shapefile路径
    input_folder: 输入栅格文件夹路径
    output_folder: 输出文件夹路径
    """

    # 创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 打开shapefile
    shapefile = ogr.Open(shp_path)
    if shapefile is None:
        print(f"无法打开shapefile: {shp_path}")
        return

    layer = shapefile.GetLayer()

    # 获取所有符合条件的tif文件（仅匹配2001-2023年）
    all_files = os.listdir(input_folder)

    # 使用正则表达式精确匹配年份格式
    year_pattern = re.compile(r'masked2_masked_all_PoS_value_(20[0-2][1-9]|20[0-2][0-3])\.tif$')

    valid_files = []
    for file in all_files:
        match = year_pattern.search(file)
        if match:
            valid_files.append(file)

    # 按照年份排序
    valid_files.sort(key=lambda x: int(re.search(r'_(20\d{2})\.tif$', x).group(1)))

    print(f"找到 {len(valid_files)} 个符合年份要求的栅格文件:")
    for file in valid_files:
        print(f"  - {file}")

    for filename in valid_files:
        try:
            # 提取年份信息
            year_match = re.search(r'_(20\d{2})\.tif$', filename)
            if not year_match:
                continue
            year = year_match.group(1)

            print(f"正在处理: {filename}")

            # 构建完整路径
            input_file = os.path.join(input_folder, filename)
            output_file = os.path.join(output_folder, f"clipped_{filename}")

            # 检查输出文件是否已存在
            if os.path.exists(output_file):
                print(f"  跳过（已存在）: {output_file}")
                continue

            # 使用GDAL进行裁剪
            gdal.Warp(
                output_file,
                input_file,
                cutlineDSName=shp_path,
                cropToCutline=True,
                dstNodata=0  # 设置裁剪区域外的像素值
            )

            print(f"完成裁剪: {output_file}")

        except Exception as e:
            print(f"处理 {filename} 时出错: {str(e)}")

    print("\n所有文件处理完成！")


# 使用示例
if __name__ == "__main__":
    # 设置路径
    shapefile_path = r"E:\Desktop\POS\甘肃省边界_620000_Shapefile_(poi86.com)\620000.shp"
    input_folder = r"D:\MODIS43A4_Value\POS"
    output_folder = r"E:\Desktop\POS\vpos"

    # 调用函数
    clip_raster_with_shapefile(shapefile_path, input_folder, output_folder)