from osgeo import gdal, ogr, osr
import os


def apply_mask(input_raster, mask_raster, output_raster):
    # 打开输入影像和掩膜影像
    input_ds = gdal.Open(input_raster)
    mask_ds = gdal.Open(mask_raster)

    # 获取输入影像的波段
    input_band = input_ds.GetRasterBand(1)
    mask_band = mask_ds.GetRasterBand(1)

    # 创建输出文件
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(output_raster,
                           input_ds.RasterXSize,
                           input_ds.RasterYSize,
                           1,
                           input_band.DataType)

    # 设置输出文件的地理变换和投影
    out_ds.SetGeoTransform(input_ds.GetGeoTransform())
    out_ds.SetProjection(input_ds.GetProjection())

    # 获取输出波段
    out_band = out_ds.GetRasterBand(1)

    # 读取掩膜数据
    mask_data = mask_band.ReadAsArray()

    # 读取输入影像数据
    input_data = input_band.ReadAsArray()

    # 应用掩膜
    masked_data = input_data.copy()
    masked_data[mask_data == 0] = -9999  # 假设 0 是掩膜中的非值区域，-9999是无效值

    # 将掩膜后的数据写入输出文件
    out_band.WriteArray(masked_data)

    # 设置无效值
    out_band.SetNoDataValue(-9999)

    # 清理
    out_band.FlushCache()
    out_ds = None
    input_ds = None
    mask_ds = None


# 定义路径
mask_path = r'F:\MODIS43A4_DOY\resampled_output_masked.tif'
sos_dir = r'F:\MODIS43A4_DOY\SOS2'

# 需要掩膜的文件列表
files_to_mask = [
    'masked_mean_values.tif',
    'masked_rmse_values.tif',
    'masked_slope_values.tif',
    'masked_p_values.tif'
]

# 遍历文件列表并应用掩膜
for file_name in files_to_mask:
    input_path = os.path.join(sos_dir, file_name)
    output_path = os.path.join(sos_dir, f'mask_applied_{file_name}')
    apply_mask(input_path, mask_path, output_path)

print("掩膜应用完成。")