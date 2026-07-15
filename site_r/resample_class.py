import os
import numpy as np
from scipy import stats
import rasterio
from rasterio.enums import Resampling
from concurrent.futures import ThreadPoolExecutor

def mode_resample(input_raster, template_raster, output_raster, chunk_size=256):
    # 打开模板影像以获取其属性
    with rasterio.open(template_raster) as src_template:
        template_profile = src_template.profile.copy()
        template_transform = src_template.transform
        template_width = src_template.width
        template_height = src_template.height
        template_crs = src_template.crs

    # 打开输入影像
    with rasterio.open(input_raster) as src_input:
        input_data = src_input.read(1)  # 假设为单波段影像
        input_nodata = src_input.nodata

        # 定义一个空数组用于存储重采样后的数据
        resampled_data = np.full((template_height, template_width), input_nodata, dtype=input_data.dtype)

        # 计算每个输出像元对应的输入像元窗口大小
        scale_x = src_input.width / template_width
        scale_y = src_input.height / template_height

        def process_chunk(chunk_i, chunk_j):
            for i in range(chunk_i, min(chunk_i + chunk_size, template_height)):
                for j in range(chunk_j, min(chunk_j + chunk_size, template_width)):
                    # 定义窗口范围
                    window_x_start = int(j * scale_x)
                    window_x_end = int((j + 1) * scale_x)
                    window_y_start = int(i * scale_y)
                    window_y_end = int((i + 1) * scale_y)

                    # 确保窗口不超出原始影像边界
                    window_x_start = max(0, window_x_start)
                    window_x_end = min(src_input.width, window_x_end)
                    window_y_start = max(0, window_y_start)
                    window_y_end = min(src_input.height, window_y_end)

                    if window_x_start >= window_x_end or window_y_start >= window_y_end:
                        continue

                    # 提取窗口内的数据
                    window_data = input_data[window_y_start:window_y_end, window_x_start:window_x_end]

                    # 忽略无效值（例如：-9999）
                    valid_window_data = window_data[window_data != input_nodata]

                    if valid_window_data.size == 0:
                        resampled_data[i, j] = input_nodata  # 或者其他你定义的无效值
                    else:
                        # 计算众数
                        mode_result = stats.mode(valid_window_data, axis=None)
                        if mode_result.count.size > 0:
                            resampled_data[i, j] = mode_result.mode.item()  # 使用 .item() 方法将 numpy 标量转换为 Python 标量
                        else:
                            resampled_data[i, j] = input_nodata

        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = []
            for i in range(0, template_height, chunk_size):
                for j in range(0, template_width, chunk_size):
                    futures.append(executor.submit(process_chunk, i, j))
            for future in futures:
                future.result()  # 等待所有任务完成

        # 更新输出影像的元数据
        template_profile.update(
            driver='GTiff',
            height=template_height,
            width=template_width,
            transform=template_transform,
            crs=template_crs
        )

        # 写入重采样后的数据到新的GeoTIFF文件
        with rasterio.open(output_raster, 'w', **template_profile) as dst:
            dst.write(resampled_data, 1)

    print("基于众数的重采样完成")

# 定义输入输出路径
input_raster = r'D:\MODIS43A4_2024\output_modified.tif'
template_raster = r'D:\MOD12Q2\MCD12Q2_SOS_masked\SOS_MCD12Q2_2001_masked.tif'
output_raster = r'D:\MOD12Q2\output_modified.tif'

# 执行重采样
mode_resample(input_raster, template_raster, output_raster)