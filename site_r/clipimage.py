from osgeo import gdal, ogr
import os


def clip_raster_to_shapefile(raster_path, shapefile_path, output_path):
    # 打开栅格数据集
    raster = gdal.Open(raster_path)
    if raster is None:
        print(f"无法打开栅格文件: {raster_path}")
        return

    # 获取矢量数据集
    shapefile = ogr.Open(shapefile_path)
    if shapefile is None:
        print(f"无法打开矢量文件: {shapefile_path}")
        return
    layer = shapefile.GetLayer()
    if layer is None or layer.GetFeatureCount() == 0:
        print(f"矢量文件没有图层或图层为空: {shapefile_path}")
        return

    # 裁剪栅格
    try:
        gdal.Warp(output_path, raster, cutlineDSName=shapefile_path, cropToCutline=True, dstNodata=-9999)
    except Exception as e:
        print(f"裁剪过程中发生错误: {e}")


# 文件路径设置
input_folder = r'F:\个人\SOS\wd\wd_all'
output_folder = r'F:\个人\SOS\wd\clipped'
shapefile_path = r'F:\个人\ioa-20241031T012330Z-001\ioa\ioa.shp'

# 创建输出文件夹如果不存在
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 遍历文件夹中的所有.tif文件
for file in os.listdir(input_folder):
    if file.endswith('.tif'):
        input_path = os.path.join(input_folder, file)
        output_path = os.path.join(output_folder, file)
        # 裁剪图像
        clip_raster_to_shapefile(input_path, shapefile_path, output_path)