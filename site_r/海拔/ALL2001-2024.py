import rasterio
import numpy as np
import pandas as pd
from rasterio.windows import Window

# 定义文件路径模板
sos_template = r"D:\MODIS43A4_2024\SOS2\masked2_masked_all_SoS_DOY_{year}_masked_tibet.tif"
eos_template = r"D:\MODIS43A4_2024\EOS2\masked2_masked_all_EoS_DOY_{year}_masked_tibet.tif"
los_template = r"D:\MODIS43A4_2024\LOS\LOS_{year}_masked_tibet.tif"
DEM_PATH = r"D:\数据\DEM\resampled_dem.tif"

years = range(2001, 2025)  # 年份范围


def get_nodata_value(src, default_nodata=-9999):
    """获取栅格数据的无效值"""
    nodata = src.nodata
    if nodata is None:
        return default_nodata
    return nodata


def safe_sample_raster(year, data_type, raster_path, dem_src, output_dir="D:\\海拔\\1\\"):
    """
    安全采样栅格数据，确保排除无效值
    """
    with rasterio.open(raster_path) as src:
        # 读取整个图像的数据
        data = src.read(1)

        # 获取正确的nodata值
        nodata_value = get_nodata_value(src)

        print(f"Year {year}, {data_type}: NoData value is {nodata_value}")
        print(f"Data range: min={data.min()}, max={data.max()}")
        print(f"NoData pixels count: {(data == nodata_value).sum()}")

        # 确保两个栅格具有相同的尺寸
        if (data.shape[0], data.shape[1]) != (dem_src.height, dem_src.width):
            raise ValueError(f"The dimensions of the {data_type} image and DEM do not match for the year {year}.")

        # 获取有效值的位置（排除nodata值）
        valid_mask = (data != nodata_value) & (~np.isnan(data))
        valid_positions = np.argwhere(valid_mask)

        print(f"Valid pixels count: {len(valid_positions)}")

        if len(valid_positions) == 0:
            print(f"Warning: No valid pixels found for {data_type} {year}")
            return

        # 如果有效像素不足10000个，则全部使用
        sample_size = min(10000, len(valid_positions))
        if len(valid_positions) < 10000:
            print(f"Warning: Only {len(valid_positions)} valid pixels available for sampling (requested 10000)")

        # 随机选择样本
        selected_indices = np.random.choice(len(valid_positions), size=sample_size, replace=False)
        samples = valid_positions[selected_indices]

        # 创建空列表以保存样本数据
        data_samples = []

        # 对每个采样位置进行迭代
        for row, col in samples:
            window = Window(col, row, 1, 1)

            # 读取当前类型和DEM的值
            value = src.read(1, window=window)[0][0]
            dem_value = dem_src.read(1, window=window)[0][0]

            # 再次验证值不是nodata值
            if value != nodata_value and not np.isnan(value):
                # 将行列号转换为经纬度
                lon, lat = src.xy(row, col)

                # 添加到数据列表
                data_samples.append({
                    'latitude': float(lat),
                    'longitude': float(lon),
                    data_type: float(value),
                    'DEM': float(dem_value)
                })

        print(f"Successfully sampled {len(data_samples)} points for {data_type} {year}")

        if len(data_samples) > 0:
            # 将数据转换为DataFrame
            df = pd.DataFrame(data_samples)

            # 导出为CSV文件
            output_path = fr"{output_dir}{data_type.lower()}_{year}_data.csv"
            df.to_csv(output_path, index=False)

            print(f"{data_type} {year} 数据已成功导出到 {output_path}")
            print(f"Output stats - Min: {df[data_type].min():.2f}, Max: {df[data_type].max():.2f}")
        else:
            print(f"Warning: No valid samples found for {data_type} {year}")


# 打开DEM文件
with rasterio.open(DEM_PATH) as dem_src:
    for year in years:
        print(f"\nProcessing year {year}...")

        # 构建每种类型数据的文件路径
        sos_path = sos_template.format(year=year)
        eos_path = eos_template.format(year=year)
        los_path = los_template.format(year=year)

        # 文件类型与路径对应字典
        file_paths = {
            'SOS': sos_path,
            'EOS': eos_path,
            'LOS': los_path  # 修正了POS -> LOS
        }

        for data_type, path in file_paths.items():
            print(f"Processing {data_type} for year {year}")
            try:
                safe_sample_raster(year, data_type, path, dem_src)
            except FileNotFoundError:
                print(f"Warning: File not found for {data_type} {year}: {path}")
            except Exception as e:
                print(f"Error processing {data_type} {year}: {str(e)}")

print("\nAll processing completed!")
