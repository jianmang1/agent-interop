# -*- coding: utf-8 -*-
import numpy as np
import os
import datetime
import concurrent.futures
from functools import partial
import gc
import shutil
import psutil
import threading
from queue import Queue

# ========== 设置 GDAL 缓存和临时目录（必须在 import gdal 前） ==========
os.environ['GDAL_CACHEMAX'] = '2048'  # 2GB 内存缓存
temp_dir = r'E:\gdal_temp'
os.environ['CPL_TMPDIR'] = temp_dir
os.environ['TMPDIR'] = temp_dir
os.environ['TEMP'] = temp_dir
os.environ['TMP'] = temp_dir
os.makedirs(temp_dir, exist_ok=True)

# 清理旧缓存（可选，谨慎使用）
if os.path.exists(temp_dir):
    for item in os.listdir(temp_dir):
        path = os.path.join(temp_dir, item)
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception as e:
            print(f"清理临时文件失败: {path}, 错误: {e}")

from osgeo import gdal

# ========== 配置 ==========
sos_path = r'D:\MODIS43A4_2024\EOS2_aligned\mean.tif'
base_dir = r'I:\TerraClimate'
out_base = r'I:\TerraClimate\preseason_extreme_index_eos'

variables = {
    'srad': ('rad_tif_clipped', False),  # False 表示平均
    'soil': ('sm_tif_clipped', False),
    'tmax': ('tmax_tif_clipped', False),
    'tmin': ('tmin_tif_clipped', False),
    'vpd': ('vpd_tif_clipped', False)
}

years = list(range(1999, 2025))  # 1999–2024
months = list(range(1, 13))

# 构建时间索引映射
time_index_map = {(y, m): idx for idx, (y, m) in enumerate((y, m) for y in years for m in months)}


# ========== 内存监控 ==========
def get_memory_usage():
    """获取当前进程内存使用情况"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB


def chunk_array(arr, chunk_size=1000):
    """将大数组分块处理"""
    for i in range(0, arr.shape[0], chunk_size):
        yield arr[i:i + chunk_size], i, min(i + chunk_size, arr.shape[0])


# ========== 辅助函数 ==========
def julian_to_year_month(jday, year):
    if np.isnan(jday) or jday < 1 or jday > 366:
        return None
    try:
        base = datetime.date(year, 1, 1)
        target = base + datetime.timedelta(days=int(jday) - 1)
        return (target.year, target.month)
    except ValueError:
        return None


def read_sos_data_chunked(chunk_size=2000):
    """分块读取SOS数据以节省内存"""
    ds = gdal.Open(sos_path)
    band = ds.GetRasterBand(1)
    ny, nx = ds.RasterYSize, ds.RasterXSize

    # 分块读取
    sos_chunks = []
    for i in range(0, ny, chunk_size):
        height = min(chunk_size, ny - i)
        chunk = band.ReadAsArray(0, i, nx, height).astype(np.float32)
        sos_chunks.append((chunk, i, height))

    ds = None
    return sos_chunks, ny, nx


def process_chunk_with_sos_chunk(sos_chunk, chunk_start_idx, chunk_height,
                                 var_folder, var_name, target_year, pre_len,
                                 is_sum, time_index_map, folder_name):
    """使用SOS数据块处理计算"""
    sos_array_chunk, start_idx, height = sos_chunk
    ny, nx = sos_array_chunk.shape

    # 生成有效掩膜
    valid_mask = (~np.isnan(sos_array_chunk)) & (sos_array_chunk > 0)
    valid_indices = np.where(valid_mask)
    valid_y_coords, valid_x_coords = valid_indices

    if len(valid_y_coords) == 0:
        return None, start_idx, height

    # 创建结果数组
    result_chunk = np.full((height, nx), np.nan, dtype=np.float32)

    # 计算每个有效像元的起止月份
    sos_jday_map = sos_array_chunk
    sos_y_map = np.full_like(sos_jday_map, fill_value=-1, dtype=np.int16)
    sos_m_map = np.full_like(sos_jday_map, fill_value=-1, dtype=np.int16)

    for i, j in zip(valid_y_coords, valid_x_coords):
        jday = sos_jday_map[i, j]
        if np.isnan(jday) or jday <= 0:
            continue
        ym = julian_to_year_month(jday, target_year)
        if ym:
            y, m = ym
            sos_y_map[i, j] = y
            sos_m_map[i, j] = m

    # 找出所有需要的月份组合
    needed_months_set = set()
    for i, j in zip(valid_y_coords, valid_x_coords):
        if sos_y_map[i, j] == -1:
            continue
        sos_y, sos_m = sos_y_map[i, j], sos_m_map[i, j]

        total_months = (sos_y * 12 + sos_m) - pre_len
        start_y = total_months // 12
        start_m = total_months % 12
        if start_m == 0:
            start_y -= 1
            start_m = 12

        y, m = start_y, start_m
        while (y, m) <= (sos_y, sos_m):
            if (y, m) in time_index_map:
                needed_months_set.add((y, m))
            m += 1
            if m > 12:
                y += 1
                m = 1
            if y > 2024:
                break

    if not needed_months_set:
        return result_chunk, start_idx, height

    # 批量加载所有需要的月份数据 - 优化内存使用
    print(f"      加载 {len(needed_months_set)} 个月份数据...")
    monthly_data = []
    for y, m in sorted(needed_months_set):
        fname = os.path.join(var_folder, f'TerraClimate_{var_name}_{y}{m:02d}.tif')
        if not os.path.exists(fname):
            print(f"        警告：缺失文件 {fname}，用 NaN 填充")
            dummy = np.full((height, nx), np.nan, dtype=np.float32)
            monthly_data.append(dummy)
            continue

        # 分块读取月度数据
        ds = gdal.Open(fname)
        band = ds.GetRasterBand(1)
        chunk_data = band.ReadAsArray(0, start_idx, nx, height).astype(np.float32)
        chunk_data = np.where((chunk_data <= 0) | np.isnan(chunk_data), np.nan, chunk_data)
        monthly_data.append(chunk_data)
        ds = None

    # 堆叠为 (n_months, height, nx)
    if len(monthly_data) > 0:
        data_3d = np.stack(monthly_data, axis=0)
        month_to_idx = {ym: idx for idx, ym in enumerate(sorted(needed_months_set))}

        # 处理每个有效像元
        for i, j in zip(valid_y_coords, valid_x_coords):
            if sos_y_map[i, j] == -1:
                continue
            sos_y, sos_m = sos_y_map[i, j], sos_m_map[i, j]

            total_months = (sos_y * 12 + sos_m) - pre_len
            start_y = total_months // 12
            start_m = total_months % 12
            if start_m == 0:
                start_y -= 1
                start_m = 12

            y, m = start_y, start_m
            needed_ym_list = []
            while (y, m) <= (sos_y, sos_m):
                if (y, m) in time_index_map:
                    needed_ym_list.append((y, m))
                m += 1
                if m > 12:
                    y += 1
                    m = 1
                if y > 2024:
                    break

            if not needed_ym_list:
                continue

            idx_list = [month_to_idx[ym] for ym in needed_ym_list if ym in month_to_idx]
            if not idx_list:
                continue

            ts = data_3d[idx_list, i, j]

            if is_sum:
                val = np.nansum(ts)
            else:
                val = np.nanmean(ts)

            if not (np.isnan(val) or np.isinf(val)):
                result_chunk[i, j] = val

        # 清理中间数据
        del data_3d, monthly_data
    else:
        print(f"      没有找到需要处理的月份，跳过 {target_year}")

    return result_chunk, start_idx, height


# ========== 任务函数：处理单个年份、单个变量、单个 preseason ==========
def process_year_task(args):
    var_name, folder_name, is_sum, pre_len, target_year = args
    print(f"    进程 {os.getpid()} 开始处理 {var_name} {target_year} preseason_{pre_len}...")

    # 获取SOS数据的基本信息
    sos_ds = gdal.Open(sos_path)
    ny, nx = sos_ds.RasterYSize, sos_ds.RasterXSize
    sos_proj = sos_ds.GetProjection()
    sos_geo = sos_ds.GetGeoTransform()
    sos_ds = None

    # 分块处理SOS数据
    chunk_size = 2000  # 调整这个值以适应可用内存
    result_full = np.full((ny, nx), np.nan, dtype=np.float32)

    # 分块读取SOS数据
    var_folder = os.path.join(base_dir, folder_name)

    # 读取整个SOS文件到内存（如果内存允许），否则分块处理
    sos_ds = gdal.Open(sos_path)
    sos_array = sos_ds.ReadAsArray().astype(np.float32)
    sos_ds = None

    # 生成有效掩膜，只处理非 NaN 且大于 0 的区域
    valid_mask = (~np.isnan(sos_array)) & (sos_array > 0)
    valid_indices = np.where(valid_mask)
    valid_y_coords, valid_x_coords = valid_indices

    if len(valid_y_coords) == 0:
        print(f"      没有有效像元，跳过 {target_year}")
        return

    # 计算每个有效像元的起止月份
    sos_jday_map = sos_array  # shape: (ny, nx)
    sos_y_map = np.full_like(sos_jday_map, fill_value=-1, dtype=np.int16)
    sos_m_map = np.full_like(sos_jday_map, fill_value=-1, dtype=np.int16)

    for i, j in zip(valid_y_coords, valid_x_coords):
        jday = sos_jday_map[i, j]
        if np.isnan(jday) or jday <= 0:
            continue
        ym = julian_to_year_month(jday, target_year)
        if ym:
            y, m = ym
            sos_y_map[i, j] = y
            sos_m_map[i, j] = m

    # 找出所有需要的月份组合
    needed_months_set = set()
    for i, j in zip(valid_y_coords, valid_x_coords):
        if sos_y_map[i, j] == -1:
            continue
        sos_y, sos_m = sos_y_map[i, j], sos_m_map[i, j]

        total_months = (sos_y * 12 + sos_m) - pre_len
        start_y = total_months // 12
        start_m = total_months % 12
        if start_m == 0:
            start_y -= 1
            start_m = 12

        y, m = start_y, start_m
        while (y, m) <= (sos_y, sos_m):
            if (y, m) in time_index_map:
                needed_months_set.add((y, m))
            m += 1
            if m > 12:
                y += 1
                m = 1
            if y > 2024:
                break

    if not needed_months_set:
        print(f"      没有找到需要处理的月份，跳过 {target_year}")
        return

    # 分块加载月度数据以节省内存
    print(f"      加载 {len(needed_months_set)} 个月份数据...")
    monthly_data_chunks = {}

    for y, m in sorted(needed_months_set):
        fname = os.path.join(var_folder, f'TerraClimate_{var_name}_{y}{m:02d}.tif')
        if not os.path.exists(fname):
            print(f"        警告：缺失文件 {fname}，用 NaN 填充")
            # 创建全NaN的虚拟数据
            dummy = np.full((ny, nx), np.nan, dtype=np.float32)
            monthly_data_chunks[(y, m)] = dummy
            continue

        # 分块读取月度数据
        ds = gdal.Open(fname)
        band = ds.GetRasterBand(1)
        full_data = band.ReadAsArray().astype(np.float32)
        full_data = np.where((full_data <= 0) | np.isnan(full_data), np.nan, full_data)
        monthly_data_chunks[(y, m)] = full_data
        ds = None

    # 处理每个有效像元
    for i, j in zip(valid_y_coords, valid_x_coords):
        if sos_y_map[i, j] == -1:
            continue
        sos_y, sos_m = sos_y_map[i, j], sos_m_map[i, j]

        total_months = (sos_y * 12 + sos_m) - pre_len
        start_y = total_months // 12
        start_m = total_months % 12
        if start_m == 0:
            start_y -= 1
            start_m = 12

        y, m = start_y, start_m
        needed_ym_list = []
        while (y, m) <= (sos_y, sos_m):
            if (y, m) in time_index_map:
                needed_ym_list.append((y, m))
            m += 1
            if m > 12:
                y += 1
                m = 1
            if y > 2024:
                break

        if not needed_ym_list:
            continue

        # 收集时间序列数据
        ts_data = []
        for ym in needed_ym_list:
            if ym in monthly_data_chunks:
                ts_data.append(monthly_data_chunks[ym][i, j])

        if len(ts_data) == 0:
            continue

        ts = np.array(ts_data)

        if is_sum:
            val = np.nansum(ts)
        else:
            # 避免空切片警告
            if np.count_nonzero(~np.isnan(ts)) > 0:
                val = np.nanmean(ts)
            else:
                val = np.nan

        if not (np.isnan(val) or np.isinf(val)):
            result_full[i, j] = val

    # 释放月度数据内存
    del monthly_data_chunks
    gc.collect()

    # 保存结果
    output_dir = os.path.join(out_base, var_name, f'preseason_{pre_len}')
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f'{target_year}_{var_name}.tif')

    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(out_path, nx, ny, 1, gdal.GDT_Float32)
    out_ds.SetProjection(sos_proj)
    out_ds.SetGeoTransform(sos_geo)
    out_ds.GetRasterBand(1).WriteArray(result_full)
    out_ds.FlushCache()
    out_ds = None

    # 释放内存
    del sos_array, result_full, sos_y_map, sos_m_map
    gc.collect()

    print(f"    ✅ {var_name} {target_year} preseason_{pre_len} 完成")


# ========== 主逻辑 ==========
def main():
    print("正在读取 SOS 数据...")
    sos_ds = gdal.Open(sos_path)
    sos_array = sos_ds.ReadAsArray().astype(np.float32)
    ny, nx = sos_ds.RasterYSize, sos_ds.RasterXSize
    sos_proj = sos_ds.GetProjection()
    sos_geo = sos_ds.GetGeoTransform()
    print(f"SOS 数据尺寸: {nx} x {ny}")
    print(f"内存使用: {get_memory_usage():.2f} MB")

    # 构建所有任务参数列表
    tasks = []
    for var_name, (folder_name, is_sum) in variables.items():
        for pre_len in range(1, 7):
            for target_year in years:
                tasks.append((var_name, folder_name, is_sum, pre_len, target_year))

    # 减少并行进程数以节省内存
    max_workers = min(4, os.cpu_count())  # 从4减少到2
    print(f"启动 {max_workers} 个进程处理 {len(tasks)} 个任务...")

    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = {executor.submit(process_year_task, task): task for task in tasks}

        # 等待所有任务完成
        for future in concurrent.futures.as_completed(futures):
            task = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"任务 {task} 出错: {e}")
                import traceback
                traceback.print_exc()

    print("\n🎉 全部完成！")


if __name__ == "__main__":
    main()



