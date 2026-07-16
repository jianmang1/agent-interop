import rasterio
import numpy as np
import pandas as pd
import os


def process_year(year):
    # 原始栅格路径（直接使用未重采样的数据）
    source_raster_path = rf'F:\转变\masked_CLCD\masked_CLCD_v01_{year}_FINAL.tif'

    # 需要分析的栅格配置
    mean_config = [
        (rf'D:\MODIS43A4_2024\SOS\500m(unmask0)\masked2_masked_all_SoS_DOY_{year}.tif', 'SOS'),
        (rf'D:\MODIS43A4_2024\POS\\unmask0\masked2_masked_all_PoS_DOY_{year}.tif', 'POS'),
        (rf'D:\MODIS43A4_2024\EOS\500M\masked2_masked_all_EoS_DOY_{year}.tif', 'EOS'),
        (rf'D:\MODIS43A4_2024\LOS\LOS_{year}.tif', 'LOS'),
        (rf'D:\MODIS43A4_2024\GUP\POS-SOS_{year}.tif', 'GUP'),
        (rf'D:\MODIS43A4_2024\GDP\EOS-POS_{year}.tif', 'GDP'),
    ]

    def process_data():
        results = {}

        # 读取当前年和上一年的原始栅格
        with rasterio.open(source_raster_path) as src:
            src_array = src.read(1)
            src_array[src_array < 0] = -9999
            src_crs = src.crs
            src_shape = src_array.shape

        # 上一年的栅格路径（直接使用原始数据）
        prev_year = year - 1
        prev_raster_path = rf'F:\转变\masked_CLCD\masked_CLCD_v01_{prev_year}_FINAL.tif'
        if not os.path.exists(prev_raster_path):
            raise FileNotFoundError(f"缺少上一年数据: {prev_raster_path}")

        with rasterio.open(prev_raster_path) as src_prev:
            src_prev_array = src_prev.read(1)
            src_prev_array[src_prev_array < 0] = -9999

        # 检查空间一致性
        if src_shape != src_prev_array.shape:
            raise ValueError(f"栅格尺寸不一致 当前年: {src_shape} vs 上一年: {src_prev_array.shape}")
        if src_crs != src_prev.crs:
            raise ValueError(f"CRS不一致 当前年: {src_crs} vs 上一年: {src_prev.crs}")

        # 筛选当前年中心为3且上一年为4的像元
        valid_center_prev = (src_array == 3) & (src_prev_array == 4)
        valid_rows, valid_cols = np.where(valid_center_prev)

        for mean_path, prefix in mean_config:
            print(f"正在处理 {prefix} 数据... 年份: {year}")
            with rasterio.open(mean_path) as mean_src:
                if src_shape != mean_src.shape:
                    raise ValueError(f"栅格尺寸不一致 源: {src_shape} vs 目标: {mean_src.shape}")
                if src_crs != mean_src.crs:
                    raise ValueError(f"CRS不一致 源: {src_crs} vs 目标: {mean_src.crs}")

                mean_array = mean_src.read(1)
                mean_array[mean_array < 0] = -9999

                # 筛选有效数据
                valid_mask = valid_center_prev & (mean_array != -9999)
                valid_rows_final, valid_cols_final = np.where(valid_mask)

                for row, col in zip(valid_rows_final, valid_cols_final):
                    min_row = max(0, row - 1)
                    max_row = min(src_array.shape[0] - 1, row + 1)
                    min_col = max(0, col - 1)
                    max_col = min(src_array.shape[1] - 1, col + 1)

                    # 当前年 3x3 窗口
                    window_current = src_array[min_row:max_row+1, min_col:max_col+1]
                    n3_current = np.count_nonzero(window_current == 3)
                    n4_current = np.count_nonzero(window_current == 4)
                    si_current = n3_current / (n3_current + n4_current) if (n3_current + n4_current) > 0 else 0

                    # 上一年 3x3 窗口
                    window_prev = src_prev_array[min_row:max_row+1, min_col:max_col+1]
                    n3_prev = np.count_nonzero(window_prev == 3)
                    n4_prev = np.count_nonzero(window_prev == 4)
                    si_prev = n3_prev / (n3_prev + n4_prev) if (n3_prev + n4_prev) > 0 else 0
                    scr = ((si_current - si_prev) / si_prev) * 100 if si_prev != 0 else 0

                    # 当前栅格 3x3 窗口
                    mean_window = mean_array[min_row:max_row+1, min_col:max_col+1]
                    value = mean_array[row, col]

                    # 计算 3 和 4 的均值与方差
                    def calc_stats(value_class):
                        mask = (window_current == value_class) & (mean_window != -9999)
                        values = mean_window[mask]
                        if len(values) == 0:
                            return 0.0, 0.0
                        mean_val = np.mean(values)
                        var_val = np.var(values)
                        return mean_val, var_val

                    sos3_mean, sos3_var = calc_stats(3)
                    sos4_mean, sos4_var = calc_stats(4)

                    key = (row, col)
                    if key not in results:
                        results[key] = {
                            'n4': n4_current,
                            'si_current': si_current,
                            'si_prev': si_prev,
                            'scr': scr,
                            f'{prefix}_value': value,
                            f'{prefix}_3_mean': sos3_mean,
                            f'{prefix}_3_var': sos3_var,
                            f'{prefix}_4_mean': sos4_mean,
                            f'{prefix}_4_var': sos4_var,
                            'year': year
                        }
                    else:
                        results[key].update({
                            f'{prefix}_value': value,
                            f'{prefix}_3_mean': sos3_mean,
                            f'{prefix}_3_var': sos3_var,
                            f'{prefix}_4_mean': sos4_mean,
                            f'{prefix}_4_var': sos4_var,
                        })

        if results:
            df = pd.DataFrame.from_dict(results, orient='index')
            df.index.names = ['row', 'col']
            df.reset_index(inplace=True)

            # 拆分中心与邻域数据
            columns_center = ['year', 'row', 'col', 'n4', 'si_current', 'si_prev', 'scr'] + \
                             [col for col in df.columns if col.endswith('_value')]
            columns_neighbor = ['year', 'row', 'col', 'n4', 'si_current', 'si_prev', 'scr'] + \
                               [col for col in df.columns if '_3_mean' in col or '_4_mean' in col]

            df_center = df[columns_center]
            df_neighbor = df[columns_neighbor]
            return df_center, df_neighbor
        else:
            return None, None

    if year >= 2002:  # 2001年没有上一年数据
        print(f"开始数据分析... 年份: {year}")
        return process_data()
    else:
        return None, None


# 主程序逻辑
if __name__ == "__main__":
    all_center_data = []
    all_neighbor_data = []

    # 直接处理所有年份
    for year in range(2002, 2022):  # 从2002年开始（需要上一年数据）
        df_center, df_neighbor = process_year(year)
        if df_center is not None:
            all_center_data.append(df_center)
        if df_neighbor is not None:
            all_neighbor_data.append(df_neighbor)

    # 合并并保存结果
    final_center_df = pd.concat(all_center_data, ignore_index=True) if all_center_data else pd.DataFrame()
    final_neighbor_df = pd.concat(all_neighbor_data, ignore_index=True) if all_neighbor_data else pd.DataFrame()

    center_output_path = r'D:\MODIS43A4_2024\center_output_all_years1.xlsx'
    neighbor_output_path = r'D:\MODIS43A4_2024\neighbor_output_all_years1.xlsx'

    if not final_center_df.empty:
        final_center_df.to_excel(center_output_path, index=False)
        print(f"中心数据已保存至: {center_output_path}")
    else:
        print("未找到中心数据记录")

    if not final_neighbor_df.empty:
        final_neighbor_df.to_excel(neighbor_output_path, index=False)
        print(f"邻域数据已保存至: {neighbor_output_path}")
    else:
        print("未找到邻域数据记录")