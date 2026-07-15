import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
import pandas as pd
import os


def resample_to_template(source_path, template_path):
    """
    将源栅格重采样到模板栅格的网格、投影和分辨率上。
    返回重采样后的 numpy 数组。
    """
    with rasterio.open(template_path) as template:
        target_crs = template.crs
        target_transform = template.transform
        target_width = template.width
        target_height = template.height
        target_dtype = template.dtypes[0]

    with rasterio.open(source_path) as source:
        # 创建目标数组
        dest = np.zeros((target_height, target_width), dtype=source.dtypes[0])

        # 执行重投影
        reproject(
            source=rasterio.band(source, 1),
            destination=dest,
            src_transform=source.transform,
            src_crs=source.crs,
            dst_transform=target_transform,
            dst_crs=target_crs,
            resampling=Resampling.nearest,  # 分类数据必须用最近邻
            src_nodata=source.nodata,
            dst_nodata=-9999
        )
        return dest


def get_mean_config_for_year(year):
    """
    根据年份返回对应的物候期数据配置
    """
    return [
        (rf'D:\MODIS43A4_2024\SOS2\masked2_masked_all_SoS_DOY_{year}_masked_tibet.tif', 'sos'),
        (rf'D:\MODIS43A4_2024\POS2\masked2_masked_all_PoS_DOY_{year}_masked_tibet.tif', 'pos'),
        (rf'D:\MODIS43A4_2024\EOS2\masked2_masked_all_EoS_DOY_{year}_masked_tibet.tif', 'eos'),
    ]


def process_year(year):
    source_raster_path = rf'F:\转变\masked_CLCD\masked_CLCD_v01_{year}_FINAL.tif'

    mean_config = get_mean_config_for_year(year)

    def process_data():
        results = {}

        # 使用第一个mean文件作为模板进行重采样
        template_path = mean_config[0][0]

        # 检查模板文件是否存在
        if not os.path.exists(template_path):
            print(f"警告: 物候期数据文件不存在: {template_path}")
            return None

        print(f"正在将 {year} 年分类数据重采样到物候期栅格网格...")
        src_array = resample_to_template(source_raster_path, template_path)
        src_array[src_array < 0] = -9999
        src_shape = src_array.shape

        prev_year = year - 1
        prev_raster_path = rf'F:\转变\masked_CLCD\masked_CLCD_v01_{prev_year}_FINAL.tif'
        if not os.path.exists(prev_raster_path):
            print(f"警告: 缺少上一年数据: {prev_raster_path}")
            return None

        print(f"正在将 {prev_year} 年分类数据重采样到物候期栅格网格...")
        src_prev_array = resample_to_template(prev_raster_path, template_path)
        src_prev_array[src_prev_array < 0] = -9999

        if src_shape != src_prev_array.shape:
            raise ValueError(f"栅格尺寸不一致 当前年: {src_shape} vs 上一年: {src_prev_array.shape}")

        valid_center_prev = (src_array == 3) & (src_prev_array == 4)
        valid_rows, valid_cols = np.where(valid_center_prev)

        for mean_path, prefix in mean_config:
            # 检查物候期文件是否存在
            if not os.path.exists(mean_path):
                print(f"警告: 物候期数据文件不存在: {mean_path}")
                continue

            print(f"正在处理 {prefix} 数据... 年份: {year}")
            with rasterio.open(mean_path) as mean_src:
                if src_shape != mean_src.shape:
                    raise ValueError(f"栅格尺寸不一致 源: {src_shape} vs 目标: {mean_src.shape}")

                mean_array = mean_src.read(1)
                mean_array[mean_array < 0] = -9999

                valid_mask = valid_center_prev & (mean_array != -9999)
                valid_rows_final, valid_cols_final = np.where(valid_mask)

                for row, col in zip(valid_rows_final, valid_cols_final):
                    min_row = max(0, row - 1)
                    max_row = min(src_array.shape[0] - 1, row + 1)
                    min_col = max(0, col - 1)
                    max_col = min(src_array.shape[1] - 1, col + 1)

                    window_current = src_array[min_row:max_row + 1, min_col:max_col + 1]
                    n3_current = np.count_nonzero(window_current == 3)
                    n4_current = np.count_nonzero(window_current == 4)
                    si_current = n3_current / (n3_current + n4_current) if (n3_current + n4_current) > 0 else 0

                    window_prev = src_prev_array[min_row:max_row + 1, min_col:max_col + 1]
                    n3_prev = np.count_nonzero(window_prev == 3)
                    n4_prev = np.count_nonzero(window_prev == 4)
                    si_prev = n3_prev / (n3_prev + n4_prev) if (n3_prev + n4_prev) > 0 else 0
                    scr = ((si_current - si_prev) / si_prev) * 100 if si_prev != 0 else 0

                    mean_window = mean_array[min_row:max_row + 1, min_col:max_col + 1]
                    value = mean_array[row, col]

                    def calc_stats(value_class):
                        # 排除 mean_array 中为 -9999 和 0 的像元
                        mask = (window_current == value_class) & ((mean_window != -9999) & (mean_window != 0))
                        values = mean_window[mask]
                        if len(values) == 0:
                            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                        mean_val = np.mean(values)
                        var_val = np.var(values)
                        std_val = np.std(values)
                        median_val = np.median(values)
                        q25_val = np.percentile(values, 25)
                        q75_val = np.percentile(values, 75)
                        return mean_val, var_val, std_val, median_val, q25_val, q75_val

                    sos3_mean, sos3_var, sos3_std, sos3_median, sos3_q25, sos3_q75 = calc_stats(3)
                    sos4_mean, sos4_var, sos4_std, sos4_median, sos4_q25, sos4_q75 = calc_stats(4)

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
                            f'{prefix}_3_std': sos3_std,
                            f'{prefix}_3_median': sos3_median,
                            f'{prefix}_3_q25': sos3_q25,
                            f'{prefix}_3_q75': sos3_q75,
                            f'{prefix}_4_mean': sos4_mean,
                            f'{prefix}_4_var': sos4_var,
                            f'{prefix}_4_std': sos4_std,
                            f'{prefix}_4_median': sos4_median,
                            f'{prefix}_4_q25': sos4_q25,
                            f'{prefix}_4_q75': sos4_q75,
                        }
                    else:
                        results[key].update({
                            f'{prefix}_value': value,
                            f'{prefix}_3_mean': sos3_mean,
                            f'{prefix}_3_var': sos3_var,
                            f'{prefix}_3_std': sos3_std,
                            f'{prefix}_3_median': sos3_median,
                            f'{prefix}_3_q25': sos3_q25,
                            f'{prefix}_3_q75': sos3_q75,
                            f'{prefix}_4_mean': sos4_mean,
                            f'{prefix}_4_var': sos4_var,
                            f'{prefix}_4_std': sos4_std,
                            f'{prefix}_4_median': sos4_median,
                            f'{prefix}_4_q25': sos4_q25,
                            f'{prefix}_4_q75': sos4_q75,
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
        print(f"\n处理年份: {year}")
        df = process_year(year)
        if df is not None:
            all_data.append(df)
        else:
            print(f"年份 {year} 处理失败或无数据")

    final_df = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    output_path = r'D:\MODIS43A4_2024\all_output2.csv'
    if not final_df.empty:
        final_df.to_csv(output_path, index=False)
        print(f"所有数据已保存至: {output_path}")
        print(f"总共处理了 {len(final_df)} 条记录")
    else:
        print("未找到数据记录")
