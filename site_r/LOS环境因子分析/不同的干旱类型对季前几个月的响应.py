# -*- coding: utf-8 -*-
"""
SOS气候数据最佳季前月份统计分析（仅基于分类图层）
修复版：自动重采样分类图至SOS图空间范围，修正平均值计算逻辑
"""

import os
import numpy as np
from osgeo import gdal
import pandas as pd
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
gdal.UseExceptions()


def resample_raster_to_reference(input_path, ref_ds, resample_method=gdal.GRA_NearestNeighbour):
    """
    将 input_path 栅格重采样到 ref_ds 的空间属性（投影、范围、分辨率、尺寸）
    返回重采样后的 numpy 数组（float32）
    """
    input_ds = gdal.Open(input_path)
    if input_ds is None:
        raise RuntimeError(f"无法打开输入栅格: {input_path}")

    # 获取参考数据集信息
    ref_geotrans = ref_ds.GetGeoTransform()
    ref_proj = ref_ds.GetProjection()
    ref_xsize = ref_ds.RasterXSize
    ref_ysize = ref_ds.RasterYSize

    # 创建内存目标数据集
    mem_driver = gdal.GetDriverByName('MEM')
    target_ds = mem_driver.Create('', ref_xsize, ref_ysize, 1, gdal.GDT_Float32)
    target_ds.SetGeoTransform(ref_geotrans)
    target_ds.SetProjection(ref_proj)

    # 执行重投影/重采样
    gdal.ReprojectImage(
        input_ds,
        target_ds,
        input_ds.GetProjection(),
        ref_proj,
        resample_method
    )

    # 读取结果并清理
    result = target_ds.ReadAsArray()
    input_ds = None
    target_ds = None
    return result


# =============== 配置路径 ===============
sos_best_month_path = r'I:\output\SOS_climate_pcorr\best_month_complete\best_month_complete.tif'
class_dir = r'I:\AI'  # 分类文件所在目录 (1.tif ~ 4.tif)
output_dir = r'I:\output\SOS_climate_pcorr\best_month_complete'

# =============== 读取SOS最佳季前月份数据 ===============
print("正在读取SOS最佳季前月份数据...")
sos_ds = gdal.Open(sos_best_month_path)
if sos_ds is None:
    raise FileNotFoundError(f"无法打开SOS文件: {sos_best_month_path}")
sos_best_month = sos_ds.ReadAsArray().astype(np.float32)
print(f"SOS数据形状: {sos_best_month.shape}")

# =============== 读取并合并分类数据（重采样后） ===============
print("正在读取并重采样分类数据 (1.tif ~ 4.tif) 到SOS图范围...")
cluster_res = np.full_like(sos_best_month, np.nan, dtype=np.float32)

for class_num in range(1, 5):  # C1 → 0, C2 → 1, C3 → 2, C4 → 3
    class_path = os.path.join(class_dir, f'{class_num}.tif')
    if not os.path.exists(class_path):
        raise FileNotFoundError(f"分类文件不存在: {class_path}")

    # 重采样分类图（使用最近邻，适合分类数据！）
    class_data = resample_raster_to_reference(
        class_path, sos_ds, resample_method=gdal.GRA_NearestNeighbour
    )

    # 假设分类图中 1 表示属于该类，其他值（0/NoData）忽略
    # 将属于当前类的像元赋值为 class_num - 1
    cluster_res = np.where(class_data == 1, class_num - 1, cluster_res)

print("分类数据加载并重采样完成。")

# =============== 统计设置 ===============
n_months = 6  # 季前月份数：1, 2, 3
n_classes = 4  # C1 ~ C4

C_count = {}  # 每类总像元数
C_month_count = {}  # 每类中各季前月份的频次
C_sum_month = {}  # 每类中有效季前月份的总和（用于计算平均值）
C_valid_count = {}  # 每类中有效统计的像元数（仅季前月份在1~3之间）

for i in range(n_classes):
    cls_name = f'C{i + 1}'
    C_count[cls_name] = np.sum(cluster_res == i)  # 总像元数
    C_month_count[cls_name] = np.zeros(n_months)  # [count_month1, count_month2, count_month3]
    C_sum_month[cls_name] = 0.0  # 有效月份总和
    C_valid_count[cls_name] = 0  # 有效统计像元数

# =============== 遍历所有像元进行统计 ===============
print("正在统计各类别中最佳季前月份分布...")
height, width = sos_best_month.shape

for i in range(height):
    for j in range(width):
        cls_val = cluster_res[i, j]
        sos_val = sos_best_month[i, j]

        if np.isnan(cls_val) or np.isnan(sos_val):
            continue

        cls_idx = int(cls_val)
        if cls_idx < 0 or cls_idx >= n_classes:
            continue

        sos_month = int(sos_val)
        if 1 <= sos_month <= n_months:  # 只统计1~3月
            cls_name = f'C{cls_idx + 1}'
            C_month_count[cls_name][sos_month - 1] += 1
            C_sum_month[cls_name] += sos_month
            C_valid_count[cls_name] += 1  # 有效统计像元数 +1

# =============== 计算结果 ===============
print("\n=== 统计结果 ===")
C_percent = {}
C_mean = {}

for i in range(n_classes):
    cls_name = f'C{i + 1}'
    total = C_count[cls_name]  # 总像元数
    valid = C_valid_count[cls_name]  # 有效统计像元数（仅月份1~3）

    if valid > 0:
        percent = (C_month_count[cls_name] / valid) * 100  # 百分比基于有效像元
        mean_val = C_sum_month[cls_name] / valid  # 平均值也基于有效像元
    else:
        percent = np.full(n_months, np.nan)
        mean_val = np.nan

    C_percent[cls_name] = percent
    C_mean[cls_name] = mean_val

    print(f"{cls_name}: 总像元={int(total)}, 有效统计像元={int(valid)}, 平均季前长度={mean_val:.2f}, 分布={percent}")

# =============== 保存结果 ===============
os.makedirs(output_dir, exist_ok=True)

# 1. 保存平均季前长度
mean_df = pd.DataFrame({
    'Class': [f'C{i + 1}' for i in range(n_classes)],
    'Total_Pixels': [C_count[f'C{i + 1}'] for i in range(n_classes)],  # 总像元数
    'Valid_Stats_Pixels': [C_valid_count[f'C{i + 1}'] for i in range(n_classes)],  # 有效统计像元数
    'Mean_Preseason_Months': [C_mean[f'C{i + 1}'] for i in range(n_classes)]  # 平均值
})
mean_df.to_csv(os.path.join(output_dir, 'SOS_season_mean.csv'), index=False)

# 2. 保存各月份占比（基于有效统计像元）
for i in range(n_classes):
    cls_name = f'C{i + 1}'
    df = pd.DataFrame(
        C_percent[cls_name].reshape(-1, 1),
        index=[f'i={m}' for m in range(1, n_months + 1)],
        columns=['SOS_Percent']
    )
    df.to_csv(os.path.join(output_dir, f'{cls_name}_SOS_percent.csv'))

print(f"\n✅ 所有结果已保存至: {output_dir}")