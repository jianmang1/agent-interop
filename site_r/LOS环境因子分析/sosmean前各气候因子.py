# -*- coding: utf-8 -*-
import numpy as np
import os
import datetime
import concurrent.futures
from functools import partial
import gc
import shutil

# ========== 设置 GDAL 缓存和临时目录（必须在 import gdal 前） ==========
os.environ['GDAL_CACHEMAX'] = '20480'  # 2GB 内存缓存
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
sos_path = r'I:\SOS1\resampled_mean_values.tif'
base_dir = r'I:\TerraClimate'
out_base = r'I:\TerraClimate\preseason_extreme_index'

variables = {
    'ppt': ('pre_tif_clipped', False),
    'srad': ('rad_tif_clipped', False), # False 表示平均
    'soil': ('sm_tif_clipped', False),
    'tmax': ('tmax_tif_clipped', False),
    'tmin': ('tmin_tif_clipped', False),
    'vpd':  ('vpd_tif_clipped', False)
}

years = list(range(1999, 2025))  # 1999–2024
months = list(range(1, 13))

# 构建时间索引映射
time_index_map = {(y, m): idx for idx, (y, m) in enumerate((y, m) for y in years for m in months)}

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

# ========== 任务函数：处理单个年份、单个变量、单个 preseason ==========
def process_year_task(args):
    var_name, folder_name, is_sum, pre_len, target_year = args
    print(f"    进程 {os.getpid()} 开始处理 {var_name} {target_year} preseason_{pre_len}...")

    # 在子进程中重新读取 SOS 数据（避免传递大数组）
    sos_ds = gdal.Open(sos_path)
    sos_array = sos_ds.ReadAsArray().astype(np.float32)
    ny, nx = sos_array.shape
    sos_proj = sos_ds.GetProjection()
    sos_geo = sos_ds.GetGeoTransform()
    sos_ds = None  # 关闭句柄

    # 定义变量文件夹路径
    var_folder = os.path.join(base_dir, folder_name)

    # 生成有效掩膜，只处理非 NaN 且大于 0 的区域
    valid_mask = (~np.isnan(sos_array)) & (sos_array > 0)
    valid_indices = np.where(valid_mask)
    valid_y_coords, valid_x_coords = valid_indices

    if len(valid_y_coords) == 0:
        print(f"      没有有效像元，跳过 {target_year}")
        return

    # 创建结果数组
    result = np.full((ny, nx), np.nan, dtype=np.float32)

    # 1. 计算每个有效像元的起止月份
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

    # 2. 找出所有需要的月份组合
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

    # 3. 批量加载所有需要的月份数据
    print(f"      加载 {len(needed_months_set)} 个月份数据...")
    monthly_data = []
    for y, m in sorted(needed_months_set):
        fname = os.path.join(var_folder, f'TerraClimate_{var_name}_{y}{m:02d}.tif')
        if not os.path.exists(fname):
            print(f"        警告：缺失文件 {fname}，用 NaN 填充")
            dummy = np.full((ny, nx), np.nan, dtype=np.float32)
            monthly_data.append(dummy)
            continue
        ds = gdal.Open(fname)
        band = ds.GetRasterBand(1).ReadAsArray().astype(np.float32)
        band = np.where((band <= 0) | np.isnan(band), np.nan, band)
        monthly_data.append(band)
        ds = None

    # 堆叠为 (n_months, ny, nx)
    data_3d = np.stack(monthly_data, axis=0)
    month_to_idx = {ym: idx for idx, ym in enumerate(sorted(needed_months_set))}

    # 4. 向量化处理每个有效像元
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
            result[i, j] = val

    # 5. 保存结果
    output_dir = os.path.join(out_base, var_name, f'preseason_{pre_len}')
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f'{target_year}_{var_name}.tif')

    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(out_path, nx, ny, 1, gdal.GDT_Float32)
    out_ds.SetProjection(sos_proj)
    out_ds.SetGeoTransform(sos_geo)
    out_ds.GetRasterBand(1).WriteArray(result)
    out_ds.FlushCache()
    out_ds = None

    # 释放内存
    del sos_array, result, data_3d, monthly_data
    gc.collect()

    print(f"    ✅ {var_name} {target_year} preseason_{pre_len} 完成")

# ========== 主逻辑 ==========
def main():
    print("正在读取 SOS 数据...")
    sos_ds = gdal.Open(sos_path)
    sos_array = sos_ds.ReadAsArray().astype(np.float32)
    ny, nx = sos_array.shape
    sos_proj = sos_ds.GetProjection()
    sos_geo = sos_ds.GetGeoTransform()
    print(f"SOS 数据尺寸: {nx} x {ny}")

    # 构建所有任务参数列表
    tasks = []
    for var_name, (folder_name, is_sum) in variables.items():
        for pre_len in range(1, 7):
            for target_year in years:
                tasks.append((var_name, folder_name, is_sum, pre_len, target_year))

    # 使用多进程执行任务
    max_workers = min(8, os.cpu_count())  # 限制进程数，避免内存爆炸
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

    print("\n🎉 全部完成！")

if __name__ == "__main__":
    main()



