from osgeo import gdal, ogr
import os
import pandas as pd
def clip_raster_to_shapefile(raster_path, shapefile_path, output_path):
    # 打开栅格数据集
    raster = gdal.Open(raster_path)
    # 获取矢量数据集
    shapefile = ogr.Open(shapefile_path)
    layer = shapefile.GetLayer()
    # 裁剪栅格
    gdal.Warp(output_path, raster, cutlineDSName=shapefile_path, cropToCutline=True, dstNodata=-9999)
    return output_path
def count_pixels(raster_path, nodata_value=-9999):
    dataset = gdal.Open(raster_path)
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()
    total_pixels = data.size
    valid_pixels = (data != nodata_value).sum()
    invalid_pixels = total_pixels - valid_pixels
    return total_pixels, valid_pixels, invalid_pixels
# 文件路径设置
input_folder = r'F:\个人\SOS\wd'
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
        clipped_image = clip_raster_to_shapefile(input_path, shapefile_path, output_path)
        # 计算像素数量
        total_pixels, valid_pixels, invalid_pixels = count_pixels(clipped_image)
        # 计算比例
        valid_ratio = valid_pixels / total_pixels * 100
        # 输出结果
        print(f"File: {file}, Total Pixels: {total_pixels}, Valid Pixels: {valid_pixels}, Invalid Pixels: {invalid_pixels}, Valid Ratio: {valid_ratio:.2f}%")

results = []
for file in os.listdir(output_folder):
    if file.endswith('.tif'):
        input_path = os.path.join(output_folder, file)
        total_pixels, valid_pixels, invalid_pixels = count_pixels(input_path)
        valid_ratio = valid_pixels / total_pixels * 100
        results.append([file, total_pixels, valid_pixels, invalid_pixels, f"{valid_ratio:.2f}%"])

df = pd.DataFrame(results, columns=['File Name', 'Total Pixels', 'Valid Pixels', 'Invalid Pixels', 'Valid Ratio'])
df.to_excel('output_summary.xlsx', index=False)