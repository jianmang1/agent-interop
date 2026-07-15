from osgeo import gdal

def resample_raster(input_raster, reference_raster, output_raster):
    # 打开参考影像以获取地理变换参数和投影信息
    ref_ds = gdal.Open(reference_raster, gdal.GA_ReadOnly)
    ref_proj = ref_ds.GetProjection()
    ref_trans = ref_ds.GetGeoTransform()
    band = ref_ds.GetRasterBand(1)
    x_size = band.XSize
    y_size = band.YSize
    ref_ds = None  # 关闭参考影像

    # 打开输入影像
    input_ds = gdal.Open(input_raster, gdal.GA_ReadOnly)
    input_band = input_ds.GetRasterBand(1)

    # 创建输出文件
    driver = gdal.GetDriverByName('GTiff')
    output_ds = driver.Create(output_raster, x_size, y_size, 1, input_band.DataType)
    output_ds.SetGeoTransform(ref_trans)
    output_ds.SetProjection(ref_proj)

    # 执行重采样
    gdal.ReprojectImage(input_ds, output_ds, input_ds.GetProjection(), ref_proj, gdal.GRA_Bilinear)

    # 清理
    input_ds = None
    output_ds = None

# 使用示例
input_path = r'D:\MODIS43A4_2024\output_modified.tif'
reference_path = r'D:\MODIS43A4_2024\SOS\500m(unmask0)\all_SoS_DOY_2001.tif'
output_path = r'D:\MODIS43A4_2024\output_resampled.tif'

resample_raster(input_path, reference_path, output_path)