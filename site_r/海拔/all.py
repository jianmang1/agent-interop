import rasterio
import numpy as np
import pandas as pd
from rasterio.windows import Window

# 定义文件路径
file_paths = {
    'SOS': r"D:\MODIS43A4_2024\masked_without_tibet\SOS2\mean_values.tif",
    'LOS': r"D:\MODIS43A4_2024\masked_without_tibet\LOS\mean_values.tif",
    'EOS': r"D:\MODIS43A4_2024\masked_without_tibet\EOS2\mean_values.tif"
}
DEM_PATH = r"D:\数据\DEM\resampled_dem.tif"


def get_nodata_value(src, default_nodata=-9999):
    """获取栅格数据的无效值"""
    nodata = src.nodata
    if nodata is None:
        return default_nodata
    return nodata


def safe_sample_mean_raster(data_type, raster_path, dem_src, output_dir="D:\\海拔\\1\\"):
    """
    安全采样均值栅格数据，确保排除无效值
    """
    with rasterio.open(raster_path) as src:
        # 读取整个图像的数据
        data = src.read(1)

        # 获取正确的nodata值
        nodata_value = get_nodata_value(src)

        print(f"{data_type}: NoData value is {nodata_value}")
        print(f"Data range: min={data.min():.2f}, max={data.max():.2f}")
        print(f"NoData pixels count: {(data == nodata_value).sum()}")

        # 确保两个栅格具有相同的尺寸
        if (data.shape[0], data.shape[1]) != (dem_src.height, dem_src.width):
            raise ValueError(f"The dimensions of the {data_type} image and DEM do not match.")

        # 获取有效值的位置（排除nodata值和NaN值）
        valid_mask = (data != nodata_value) & (~np.isnan(data))
        valid_positions = np.argwhere(valid_mask)

        print(f"Valid pixels count: {len(valid_positions)}")

        if len(valid_positions) == 0:
            print(f"Warning: No valid pixels found for {data_type}")
            return

        # 如果有效像素不足10000个，则全部使用（或调整为实际数量）
        sample_size = min(10000, len(valid_positions))
        if len(valid_positions) < 10000:
            print(f"Warning: Only {len(valid_positions)} valid pixels available for sampling (requested 10000)")
            sample_size = len(valid_positions)

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

            # 再次验证值不是nodata值且不是NaN
            if value != nodata_value and not np.isnan(value) and dem_value != dem_src.nodata and not np.isnan(
                    dem_value):
                # 添加到数据列表
                data_samples.append({
                    'row': int(row),
                    'col': int(col),
                    data_type: float(value),
                    'DEM': float(dem_value)
                })

        print(f"Successfully sampled {len(data_samples)} points for {data_type}")

        if len(data_samples) > 0:
            # 将数据转换为DataFrame
            df = pd.DataFrame(data_samples)

            # 导出为CSV文件
            output_path = fr"{output_dir}{data_type.lower()}_data.csv"
            df.to_csv(output_path, index=False)

            print(f"{data_type} 数据已成功导出到 {output_path}")
            print(f"Output stats - Min: {df[data_type].min():.2f}, Max: {df[data_type].max():.2f}")

            # 额外检查是否有异常值
            potential_outliers = df[(df[data_type] == nodata_value) | (df[data_type].isna())]
            if not potential_outliers.empty:
                print(f"Warning: Found {len(potential_outliers)} potentially invalid values in output")
        else:
            print(f"Warning: No valid samples found for {data_type}")


# 打开DEM文件
with rasterio.open(DEM_PATH) as dem_src:
    # 对每种类型的数据进行操作
    for data_type, path in file_paths.items():
        print(f"\nProcessing {data_type}...")
        try:
            safe_sample_mean_raster(data_type, path, dem_src)
        except FileNotFoundError:
            print(f"Warning: File not found for {data_type}: {path}")
        except Exception as e:
            print(f"Error processing {data_type}: {str(e)}")

print("\nAll processing completed!")
