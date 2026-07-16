import os
from osgeo import gdal, gdalconst

# 定义输入路径
mask_path = r"F:\个人\less6500.tif"
clcd_folder = r"F:\个人\CLASS\新建文件夹"
output_folder = r"F:\个人\CLASS\新建文件夹"

# 确保输出文件夹存在
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 打开掩膜文件并获取相关信息
mask_ds = gdal.Open(mask_path)
mask_band = mask_ds.GetRasterBand(1)
xsize_mask = mask_ds.RasterXSize
ysize_mask = mask_ds.RasterYSize
geotransform_mask = mask_ds.GetGeoTransform()
projection_mask = mask_ds.GetProjection()

# 读取掩膜数据数组
mask_array = mask_band.ReadAsArray()

# 定义分块大小
chunk_size = 1000  # 可根据实际情况调整

clcd_file = os.path.join(clcd_folder, f"中科院_mode_resampled_clipped.tif")
# 打开当前年份的地表覆盖产品文件
clcd_ds = gdal.Open(clcd_file)

clcd_band = clcd_ds.GetRasterBand(1)

# 获取地表覆盖产品的信息
xsize_clcd = clcd_ds.RasterXSize
ysize_clcd = clcd_ds.RasterYSize
geotransform_clcd = clcd_ds.GetGeoTransform()
projection_clcd = clcd_ds.GetProjection()

# 创建临时重采样文件
temp_resampled_file = os.path.join(output_folder, f"temp_中科院_mode_resampled_clipped1.tif")
driver = gdal.GetDriverByName("GTiff")
resampled_ds = driver.Create(temp_resampled_file, xsize_mask, ysize_mask, 1, gdal.GDT_Int16)
resampled_ds.SetGeoTransform(geotransform_mask)
resampled_ds.SetProjection(projection_mask)
resampled_band = resampled_ds.GetRasterBand(1)

# 使用近邻插值法进行重采样
gdal.ReprojectImage(clcd_ds, resampled_ds, projection_clcd, projection_mask, gdalconst.GRA_NearestNeighbour)

# 关闭原始数据集
clcd_ds = None

# 关闭重采样后的数据集
resampled_ds = None

# 重新打开重采样后的数据集
resampled_ds = gdal.Open(temp_resampled_file)
if resampled_ds is None:
    print(f"无法打开临时重采样文件: {temp_resampled_file}")

resampled_band = resampled_ds.GetRasterBand(1)

# 创建输出文件
output_file = os.path.join(output_folder, f"中科院_mode_resampled_clipped1.tif")
out_ds = driver.Create(output_file, xsize_mask, ysize_mask, 1, gdal.GDT_Int16)
out_ds.SetGeoTransform(geotransform_mask)
out_ds.SetProjection(projection_mask)
out_band = out_ds.GetRasterBand(1)

# 分块处理
for yoff in range(0, ysize_mask, chunk_size):
    ysize_chunk = min(chunk_size, ysize_mask - yoff)
    for xoff in range(0, xsize_mask, chunk_size):
        xsize_chunk = min(chunk_size, xsize_mask - xoff)

        # 读取重采样后的地表覆盖产品数据块
        clcd_chunk = resampled_band.ReadAsArray(xoff, yoff, xsize_chunk, ysize_chunk)

        # 应用掩膜
        masked_chunk = clcd_chunk.copy()
        masked_chunk[mask_array[yoff:yoff + ysize_chunk, xoff:xoff + xsize_chunk] == 0] = -9999

        # 写入输出文件
        out_band.WriteArray(masked_chunk, xoff, yoff)

# 刷新缓存并关闭输出数据集
out_band.FlushCache()
out_ds = None

# 关闭重采样后的数据集
resampled_ds = None

# 删除临时重采样文件
try:
    os.remove(temp_resampled_file)
except PermissionError as e:
    print(f"无法删除临时文件 {temp_resampled_file}: {e}")

print(f"处理完成: {output_file}")
print("所有文件处理完毕。")



