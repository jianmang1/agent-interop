import rasterio
import numpy as np
import pandas as pd
from rasterio.windows import Window

# 定义文件路径
file_paths = {
    'Oth_LOS': r"D:\MODIS43A4_2024\LOS\remainder_mean_values.tif"
}
DEM_PATH = r"D:\数据\DEM\resampled_dem_除青藏高原.tif"


# 打开DEM文件
with rasterio.open(DEM_PATH) as dem_src:
    # 对每种类型的数据进行操作
    for data_type, path in file_paths.items():
        with rasterio.open(path) as src:
            # 读取整个图像的数据和配置
            data = src.read(1)
            height, width = data.shape

            # 确保两个栅格具有相同的尺寸
            if (height, width) != (dem_src.height, dem_src.width):
                raise ValueError(f"The dimensions of the {data_type} image and DEM do not match.")

            # 获取所有有效值的位置
            valid_positions = np.argwhere(data != src.nodata)

            # 随机选择5000个有效位置
            samples = valid_positions[np.random.choice(valid_positions.shape[0], size=10000, replace=False)]

            # 创建空列表以保存样本数据
            data_samples = []

            # 对每个采样位置进行迭代
            for row, col in samples:
                window = Window(col, row, 1, 1)

                # 读取当前类型和DEM的值
                value = src.read(1, window=window)[0][0]
                dem_value = dem_src.read(1, window=window)[0][0]

                # 添加到数据列表
                data_samples.append(
                    {'row': int(row), 'col': int(col), data_type: float(value), 'DEM': float(dem_value)})

            # 将数据转换为DataFrame
            df = pd.DataFrame(data_samples)

            # 导出为CSV文件
            output_path = fr"D:\海拔\2\{data_type.lower()}_data.csv"
            df.to_csv(output_path, index=False)

            print(f"{data_type} 数据已成功导出到 {output_path}")