import os
from osgeo import gdal, ogr

# 设置工作环境
input_raster_dir = r'D:\MODIS43A4_2024\EOS\500M'
output_raster_dir = r'D:\MODIS43A4_2024\EOS\500M\clipped'  # 确保此文件夹存在
mask_shapefile = r'D:\数据\AI\Global-AI_ET0_v3_annual\mask_less_than_6500.shp'

# 创建输出文件夹（如果不存在）
if not os.path.exists(output_raster_dir):
    os.makedirs(output_raster_dir)

# 获取所有的栅格文件
raster_files = [f for f in os.listdir(input_raster_dir) if f.endswith('.tif') and '2000' <= f[-8:-4] <= '2025']


# 定义裁剪函数
def clip_raster_with_shapefile(raster_path, shapefile_path, output_path):
    # 打开矢量文件并获取其边界框
    mask_ds = ogr.Open(shapefile_path)
    mask_lyr = mask_ds.GetLayer()
    mask_extent = mask_lyr.GetExtent()

    # 执行裁剪操作
    gdal.Warp(output_path, raster_path, cutlineDSName=shapefile_path, cropToCutline=True, dstNodata=-9999)


# 对每个栅格文件执行裁剪
for raster_file in raster_files:
    input_path = os.path.join(input_raster_dir, raster_file)
    output_filename = 'clipped_' + raster_file
    output_path = os.path.join(output_raster_dir, output_filename)

    print(f'正在裁剪 {raster_file}...')
    clip_raster_with_shapefile(input_path, mask_shapefile, output_path)
    print(f'{raster_file} 已裁剪完成。')

print('所有文件裁剪完毕。')