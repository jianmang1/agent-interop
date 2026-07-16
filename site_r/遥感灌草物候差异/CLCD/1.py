import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
import pandas as pd
import os

def resample_raster(source_path, target_path, output_path):
    """将源栅格重采样到目标栅格的空间参考系统"""
    with rasterio.open(target_path) as target:
        target_profile = target.profile.copy()
        target_crs = target.crs
        target_transform = target.transform
        target_width = target.width
        target_height = target.height

    with rasterio.open(source_path) as source:
        dtype = source.dtypes[0]

        if dtype in ['int8', 'uint8']:
            nodata_value = 255
        elif dtype == 'int16':
            nodata_value = -32768
        elif dtype == 'uint16':
            nodata_value = 65535
        elif dtype in ['int32', 'uint32']:
            nodata_value = 4294967295
        elif dtype in ['float32', 'float64']:
            nodata_value = -9999.0
        else:
            raise ValueError(f"Unsupported data type: {dtype}")

        data = source.read(1)
        resampled_data = np.zeros((target_height, target_width), dtype=dtype)

        reproject(
            source=data,
            destination=resampled_data,
            src_transform=source.transform,
            src_crs=source.crs,
            dst_transform=target_transform,
            dst_crs=target_crs,
            resampling=Resampling.nearest
        )

        with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=target_height,
                width=target_width,
                count=1,
                dtype=dtype,
                crs=target_crs,
                transform=target_transform,
                nodata=nodata_value
        ) as dst:
            dst.write(resampled_data, 1)


def process_year(year):
    source_raster_path = rf'F:\转变\masked_CLCD\masked_CLCD_v01_{year}.tif'
    resampled_source_path = rf'F:\转变\masked_CLCD\masked_CLCD_v01_{year}_FINAL.tif'

    mean_config = [
        (rf'D:\MODIS43A4_2024\SOS\500m(unmask0)\masked2_masked_all_SoS_DOY_{year}.tif', 'SOS'),
        (rf'D:\MODIS43A4_2024\POS\\unmask0\masked2_masked_all_PoS_DOY_{year}.tif', 'POS'),
        (rf'D:\MODIS43A4_2024\EOS\500M\masked2_masked_all_EoS_DOY_{year}.tif', 'EOS'),
        (rf'D:\MODIS43A4_2024\LOS\LOS_{year}.tif', 'LOS'),
        (rf'D:\MODIS43A4_2024\GUP\POS-SOS_{year}.tif', 'GUP'),
        (rf'D:\MODIS43A4_2024\GDP\EOS-POS_{year}.tif', 'GDP'),
    ]

    # 步骤1：执行重采样
    print(f"正在重采样源栅格... 年份: {year}")
    resample_raster(source_raster_path, mean_config[0][0], resampled_source_path)
    print(f"重采样完成，保存至: {resampled_source_path}")

    # 步骤2：执行分析流程
    def process_data(mean_config):
        results = {}

        with rasterio.open(resampled_source_path) as src:
            src_array = src.read(1)
            src_array[src_array < 0] = -9999

        for mean_path, prefix in mean_config:
            print(f"正在处理 {prefix} 数据... 年份: {year}")
            with rasterio.open(mean_path) as mean_src:
                if src.shape != mean_src.shape:
                    raise ValueError(f"栅格尺寸不一致 源: {src.shape} vs 目标: {mean_src.shape}")
                if src.crs != mean_src.crs:
                    raise ValueError(f"CRS不一致 源: {src.crs} vs 目标: {mean_src.crs}")

                mean_array = mean_src.read(1)
                mean_array[mean_array < 0] = -9999

                rows, cols = np.where((src_array == 3) & (mean_array != -9999))

                for row, col in zip(rows, cols):
                    min_row = max(0, row - 1)
                    max_row = min(src.height - 1, row + 1)
                    min_col = max(0, col - 1)
                    max_col = min(src.width - 1, col + 1)

                    window = src_array[min_row:max_row + 1, min_col:max_col + 1]
                    n4 = np.count_nonzero(window == 4)

                    if n4 == 0:
                        continue

                    value = mean_array[row, col]

                    def calc_mean(value_class):
                        mask = (window == value_class) & (mean_array[min_row:max_row + 1, min_col:max_col + 1] != -9999)
                        return mean_array[min_row:max_row + 1, min_col:max_col + 1][mask].mean() if mask.any() else 0.0

                    sos4 = calc_mean(4)

                    key = (row, col)
                    if key not in results:
                        results[key] = {
                            'n4': n4,
                            f'{prefix}_value': value,
                            f'{prefix}_4': sos4,
                            'year': year
                        }
                    else:
                        results[key].update({
                            f'{prefix}_value': value,
                            f'{prefix}_4': sos4,
                        })

        if results:
            df = pd.DataFrame.from_dict(results, orient='index')
            df.index.names = ['row', 'col']
            df.reset_index(inplace=True)

            # 拆分中心与邻域数据
            columns_center = ['year', 'row', 'col', 'n4'] + [col for col in df.columns if col.endswith('_value')]
            columns_neighbor = ['year', 'row', 'col', 'n4'] + [col for col in df.columns if col.endswith('_4')]

            df_center = df[columns_center]
            df_neighbor = df[columns_neighbor]
            return df_center, df_neighbor
        else:
            return None, None

    print(f"开始数据分析... 年份: {year}")
    return process_data(mean_config)


# 主程序逻辑
if __name__ == "__main__":
    # 初始化两个 DataFrame 列表
    all_center_data = []
    all_neighbor_data = []

    # 循环处理年份
    for year in range(2001, 2022):
        df_center, df_neighbor = process_year(year)
        if df_center is not None:
            all_center_data.append(df_center)
        if df_neighbor is not None:
            all_neighbor_data.append(df_neighbor)

    # 合并所有年份的数据
    final_center_df = pd.concat(all_center_data, ignore_index=True) if all_center_data else pd.DataFrame()
    final_neighbor_df = pd.concat(all_neighbor_data, ignore_index=True) if all_neighbor_data else pd.DataFrame()

    # 保存为两个文件
    center_output_path = r'D:\MODIS43A4_2024\center_output_all_years.xlsx'
    neighbor_output_path = r'D:\MODIS43A4_2024\neighbor_output_all_years.xlsx'

    if not final_center_df.empty:
        final_center_df.to_excel(center_output_path, index=False)
        print(f"所有年份的中心数据已保存至: {center_output_path}")
    else:
        print("未找到中心数据记录")

    if not final_neighbor_df.empty:
        final_neighbor_df.to_excel(neighbor_output_path, index=False)
        print(f"所有年份的邻域数据已保存至: {neighbor_output_path}")
    else:
        print("未找到邻域数据记录")