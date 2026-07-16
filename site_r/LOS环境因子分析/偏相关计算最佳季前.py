# -*- coding: utf-8 -*-
import os
import numpy as np
import pandas as pd
import glob
from scipy.signal import detrend
import pingouin as pg
from osgeo import gdal

# 启用 GDAL 异常（可选，消除警告）
gdal.UseExceptions()

# ================== 配置路径 ==================
CLIMATE_ROOT = r"I:\TerraClimate\preseason_extreme_index"
PHENO_PATH_PATTERN = r"I:\SOS1\resampled_masked2_masked_all_SoS_DOY_{}_resampled.tif"
OUTPUT_ROOT = r"E:\output\SOS_climate_pcorr"

CLIMATE_VARS = ['ppt', 'srad','soil', 'tmax', 'tmin', 'vpd']
YEARS = list(range(2001, 2025))  # 24 years
N_YEARS = len(YEARS)

# ================== 辅助函数 ==================

def read_pheno_stack(years, pattern):
    stack = []
    for y in years:
        f = pattern.format(y)
        if not os.path.exists(f):
            raise FileNotFoundError(f"Missing SOS file for year {y}: {f}")
        ds = gdal.Open(f)
        arr = ds.GetRasterBand(1).ReadAsArray().astype(np.float32)
        arr = np.where((arr <= 0) | np.isnan(arr), -1000.0, arr)
        stack.append(arr)
    return np.stack(stack, axis=0), ds  # 返回数据 + 最后一个ds作为参考

def read_climate_stack(var, month, years, ref_shape):
    stack = []
    for y in years:
        f = os.path.join(CLIMATE_ROOT, var, f"preseason_{month}", f"{y}_{var}.tif")
        if not os.path.exists(f):
            raise FileNotFoundError(f"Missing climate file: {f}")
        ds = gdal.Open(f)
        arr = ds.GetRasterBand(1).ReadAsArray().astype(np.float32)
        if arr.shape != ref_shape:
            raise ValueError(f"Shape mismatch in {f}: got {arr.shape}, expected {ref_shape}")
        arr = np.where(np.isnan(arr), -1000.0, arr)
        stack.append(arr)
    return np.stack(stack, axis=0)

def detrend_3d(data_3d, fill_value=-1000.0):
    out = np.full_like(data_3d, fill_value)
    t, h, w = data_3d.shape
    for i in range(h):
        for j in range(w):
            series = data_3d[:, i, j]
            if np.all(series == fill_value):
                continue
            valid_mask = (series != fill_value)
            if not np.any(valid_mask):
                continue
            try:
                # 只对有效值线性去趋势
                valid_series = series[valid_mask].astype(np.float64)
                detrended_valid = detrend(valid_series, type='linear')
                # 填回原位置
                out_series = np.full_like(series, fill_value)
                out_series[valid_mask] = detrended_valid
                out[:, i, j] = out_series
            except Exception as e:
                pass  # 保持 fill_value
    return out

def save_tif(data, ref_ds, out_path):
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(out_path, data.shape[1], data.shape[0], 1, gdal.GDT_Float32)
    out_ds.SetProjection(ref_ds.GetProjection())
    out_ds.SetGeoTransform(ref_ds.GetGeoTransform())
    out_ds.GetRasterBand(1).WriteArray(data)
    out_ds.FlushCache()
    out_ds = None

# ================== 主流程：整幅图处理 ==================

print("=== Processing full raster ===")

# 1. 读取 SOS 时间序列并获取参考影像信息
SOS_3d, ref_ds = read_pheno_stack(YEARS, PHENO_PATH_PATTERN)
print(f"Loaded SOS stack: {SOS_3d.shape}")

# 2. 创建有效像元掩膜（任意一年非 -1000 即视为有效）
mask = (SOS_3d[0] != -1000.0)

# 3. 对 SOS 去趋势
print("Detrending SOS...")
detrended_SOS = detrend_3d(SOS_3d)
del SOS_3d

# 4. 按 preseason 月份循环
for month in [4,5,6]:
    print(f"\nProcessing preseason month {month}...")

    # 读取所有气候变量的时间序列
    climate_data = {}
    for var in CLIMATE_VARS:
        print(f"  Loading {var}...")
        climate_data[var] = read_climate_stack(var, month, YEARS, mask.shape)

    # 对每个气候变量去趋势
    detrended_climate = {}
    for var in CLIMATE_VARS:
        print(f"  Detrending {var}...")
        detrended_climate[var] = detrend_3d(climate_data[var])
        del climate_data[var]

    # 初始化输出相关系数图
    h, w = mask.shape
    corr_maps = {var: np.full((h, w), np.nan, dtype=np.float32) for var in CLIMATE_VARS}

    # 准备 DataFrame 模板
    df_template = pd.DataFrame(
        np.full((N_YEARS, len(CLIMATE_VARS) + 1), np.nan),
        columns=['SOS'] + CLIMATE_VARS
    )

    # 像素级偏相关计算
    print("Computing partial correlations...")
    for i in range(h):
        for j in range(w):
            if not mask[i, j]:
                continue

            df = df_template.copy()
            df['SOS'] = detrended_SOS[:, i, j]

            skip = False
            for var in CLIMATE_VARS:
                series = detrended_climate[var][:, i, j]
                if np.all(series == -1000.0):
                    skip = True
                    break
                df[var] = series
            if skip:
                continue

            for target_var in CLIMATE_VARS:
                covars = [v for v in CLIMATE_VARS if v != target_var]
                try:
                    res = pg.partial_corr(data=df, x='SOS', y=target_var, covar=covars, method='spearman')
                    r_val = res['r'].iloc[0]
                    if not np.isnan(r_val):
                        corr_maps[target_var][i, j] = r_val
                except Exception as e:
                    continue

        if i % 100 == 0:
            print(f"  Row {i}/{h} processed")

    # 保存结果
    out_dir = os.path.join(OUTPUT_ROOT, f"preseason_{month}")
    os.makedirs(out_dir, exist_ok=True)

    for var in CLIMATE_VARS:
        out_path = os.path.join(out_dir, f"SOS_{var}_pcorr.tif")
        save_tif(corr_maps[var], ref_ds, out_path)
        print(f"Saved: {out_path}")

    del detrended_climate, corr_maps

# 清理
ref_ds = None

print("\n✅ All done!")