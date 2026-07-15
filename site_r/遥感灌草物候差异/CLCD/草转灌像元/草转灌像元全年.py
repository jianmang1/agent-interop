import rasterio
import numpy as np
import pandas as pd
import os


def process_year(year, converted_cells, transyear_dict):
    source_raster_path = rf'F:\转变\masked_CLCD\masked_CLCD_v01_{year}_FINAL.tif'

    mean_config = [
        (r'D:\MODIS43A4_2024\SOS2\masked2_masked_all_SoS_DOY_2023_masked_tibet.tif', 'sos'),
        (r'D:\MODIS43A4_2024\POS2\\masked2_masked_all_PoS_DOY_2023_masked_tibet.tif', 'pos'),
        (r'D:\MODIS43A4_2024\EOS2\masked2_masked_all_EoS_DOY_2023_masked_tibet.tif', 'eos'),
    ]

    def process_data():
        results = {}

        with rasterio.open(source_raster_path) as src:
            src_array = src.read(1)
            src_array[src_array < 0] = -9999
            src_crs = src.crs
            src_shape = src_array.shape

        # 如果不是 2001 年，则读取上一年数据
        if year > 2001:
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

            # 找出当年的“4转3”像元并记录转变年份
            valid_center_prev = (src_array == 3) & (src_prev_array == 4)
            new_converted = np.column_stack(np.where(valid_center_prev)).tolist()
            for row, col in new_converted:
                if (row, col) not in converted_cells:
                    converted_cells.add((row, col))
                    transyear_dict[(row, col)] = year  # 记录转变年份

        # 处理物候数据
        for mean_path, prefix in mean_config:
            print(f"正在处理 {prefix} 数据... 年份: {year}")
            with rasterio.open(mean_path) as mean_src:
                if src_shape != mean_src.shape:
                    raise ValueError(f"栅格尺寸不一致 源: {src_shape} vs 目标: {mean_src.shape}")
                if src_crs != mean_src.crs:
                    raise ValueError(f"CRS不一致 源: {src_crs} vs 目标: {mean_src.crs}")

                mean_array = mean_src.read(1)
                mean_array[mean_array < 0] = -9999

                # 处理所有已转换像元
                for (row, col) in converted_cells:
                    min_row = max(0, row - 1)
                    max_row = min(src_array.shape[0] - 1, row + 1)
                    min_col = max(0, col - 1)
                    max_col = min(src_array.shape[1] - 1, col + 1)

                    window_current = src_array[min_row:max_row+1, min_col:max_col+1]
                    n3_current = np.count_nonzero(window_current == 3)
                    n4_current = np.count_nonzero(window_current == 4)
                    si_current = n3_current / (n3_current + n4_current) if (n3_current + n4_current) > 0 else 0

                    # 如果不是 2001 年，则计算上一年的 SI
                    if year > 2001:
                        window_prev = src_prev_array[min_row:max_row+1, min_col:max_col+1]
                        n3_prev = np.count_nonzero(window_prev == 3)
                        n4_prev = np.count_nonzero(window_prev == 4)
                        si_prev = n3_prev / (n3_prev + n4_prev) if (n3_prev + n4_prev) > 0 else 0
                        scr = ((si_current - si_prev) / si_prev) * 100 if si_prev != 0 else 0
                    else:
                        si_prev = 0
                        scr = 0

                    mean_window = mean_array[min_row:max_row+1, min_col:max_col+1]
                    value = mean_array[row, col]

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
                            'transyear': transyear_dict.get(key, 0),  # 转变年份
                        }
                    results[key][f'{prefix}_{year}'] = value
                    results[key][f'{prefix}_3_mean_{year}'] = sos3_mean
                    results[key][f'{prefix}_3_var_{year}'] = sos3_var
                    results[key][f'{prefix}_4_mean_{year}'] = sos4_mean
                    results[key][f'{prefix}_4_var_{year}'] = sos4_var
                    results[key][f'si_current_{year}'] = si_current
                    results[key][f'si_prev_{year}'] = si_prev
                    results[key][f'scr_{year}'] = scr

        return results

    if year >= 2001:
        print(f"开始数据分析... 年份: {year}")
        return process_data()
    else:
        return None


if __name__ == "__main__":
    converted_cells = set()
    transyear_dict = {}
    all_results = {}

    for year in range(2001, 2022):
        yearly_results = process_year(year, converted_cells, transyear_dict)
        if yearly_results:
            for key, data in yearly_results.items():
                if key not in all_results:
                    all_results[key] = data
                else:
                    all_results[key].update(data)

    if all_results:
        df = pd.DataFrame.from_dict(all_results, orient='index')

        # 从索引直接提取 row 和 col
        df['row'] = df.index.map(lambda x: x[0])
        df['col'] = df.index.map(lambda x: x[1])

        # 删除原始索引
        df.reset_index(drop=True, inplace=True)

        output_path = r'D:\MODIS43A4_2024\wide_format_output.csv'
        df.to_csv(output_path, index=False)
        print(f"所有数据已保存至: {output_path}")
    else:
        print("警告：没有数据可供处理")