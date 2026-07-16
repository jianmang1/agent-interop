import rasterio
import numpy as np
import pandas as pd
import os


def process_year(year):
    source_raster_path = rf'F:\转变\masked_CLCD\masked_CLCD_v01_{year}_FINAL.tif'

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

        with rasterio.open(source_raster_path) as src:
            src_array = src.read(1)
            src_array[src_array < 0] = -9999
            src_crs = src.crs
            src_shape = src_array.shape

        prev_year = year - 1
        prev_raster_path = rf'F:\转变\masked_CLCD\masked_CLCD_v01_{prev_year}_FINAL.tif'
        if not os.path.exists(prev_raster_path):
            raise FileNotFoundError(f"缺少上一年数据: {prev_raster_path}")

        with rasterio.open(prev_raster_path) as src_prev:
            src_prev_array = src_prev.read(1)
            src_prev_array[src_prev_array < 0] = -9999

        if src_shape != src_prev_array.shape:
            raise ValueError(f"栅格尺寸不一致 当前年: {src_shape} vs 上一年: {src_prev_array.shape}")
        if src_crs != src_prev.crs:
            raise ValueError(f"CRS不一致 当前年: {src_crs} vs 上一年: {src_prev.crs}")

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

                valid_mask = valid_center_prev & (mean_array != -9999)
                valid_rows_final, valid_cols_final = np.where(valid_mask)

                for row, col in zip(valid_rows_final, valid_cols_final):
                    min_row = max(0, row - 1)
                    max_row = min(src_array.shape[0] - 1, row + 1)
                    min_col = max(0, col - 1)
                    max_col = min(src_array.shape[1] - 1, col + 1)

                    window_current = src_array[min_row:max_row+1, min_col:max_col+1]
                    n3_current = np.count_nonzero(window_current == 3)
                    n4_current = np.count_nonzero(window_current == 4)
                    si_current = n3_current / (n3_current + n4_current) if (n3_current + n4_current) > 0 else 0

                    window_prev = src_prev_array[min_row:max_row+1, min_col:max_col+1]
                    n3_prev = np.count_nonzero(window_prev == 3)
                    n4_prev = np.count_nonzero(window_prev == 4)
                    si_prev = n3_prev / (n3_prev + n4_prev) if (n3_prev + n4_prev) > 0 else 0
                    scr = (si_current - si_prev)

                    mean_window = mean_array[min_row:max_row+1, min_col:max_col+1]
                    value = mean_array[row, col]

                    def calc_stats(value_class):
                        # 排除 mean_array 中为 -9999 和 0 的像元
                        mask = (window_current == value_class) & ((mean_window != -9999) & (mean_window != 0))
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
                            'year': year,
                            'n3': n3_current,
                            'n4': n4_current,
                            'si_current': si_current,
                            'si_prev': si_prev,
                            'scr': scr,
                            f'{prefix}_value': value,
                            f'{prefix}_3_mean': sos3_mean,
                            f'{prefix}_3_var': sos3_var,
                            f'{prefix}_4_mean': sos4_mean,
                            f'{prefix}_4_var': sos4_var,
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
            return df
        else:
            return None

    if year >= 2002:
        print(f"开始数据分析... 年份: {year}")
        return process_data()
    else:
        return None


# 主程序逻辑
if __name__ == "__main__":
    all_data = []

    for year in range(2002, 2022):
        df = process_year(year)
        if df is not None:
            all_data.append(df)

    final_df = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    output_path = r'D:\MODIS43A4_2024\草转灌当年像元(绝对SCR).csv'
    if not final_df.empty:
        final_df.to_csv(output_path, index=False)
        print(f"所有数据已保存至: {output_path}")
    else:
        print("未找到数据记录")