# -*- coding: utf-8 -*-
"""
SOS降雨相关性最佳月份统计分析（仅基于分类图层）
修复版：自动重采样分类图至SOS图空间范围，修正平均值计算逻辑
针对离散型相关性数据进行统计分析
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
sos_best_month_path = r'I:\TerraClimate\preseason_extreme_index\ppt\preseason_1\2021_ppt.tif'
class_dir = r'I:\AI'  # 分类文件所在目录 (1.tif ~ 4.tif)
output_dir = r'I:\output\preseason_1climate'

# =============== 读取SOS降雨相关性数据 ===============
print("正在读取SOS降雨相关性数据...")
sos_ds = gdal.Open(sos_best_month_path)
if sos_ds is None:
    raise FileNotFoundError(f"无法打开SOS文件: {sos_best_month_path}")
sos_best_month = sos_ds.ReadAsArray().astype(np.float32)
print(f"SOS数据形状: {sos_best_month.shape}")
print(f"SOS数据范围: {np.nanmin(sos_best_month)} 到 {np.nanmax(sos_best_month)}")

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
n_classes = 4  # C1 ~ C4

C_count = {}  # 每类总像元数
C_correlation_values = {}  # 每类中所有相关性值的列表（用于统计分析）
C_valid_count = {}  # 每类中有效统计的像元数

for i in range(n_classes):
    cls_name = f'C{i + 1}'
    C_count[cls_name] = np.sum(cluster_res == i)  # 总像元数
    C_correlation_values[cls_name] = []  # 存储相关性值列表
    C_valid_count[cls_name] = 0  # 有效统计像元数

# =============== 遍历所有像元进行统计 ===============
print("正在统计各类别中降雨相关性分布...")
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

        cls_name = f'C{cls_idx + 1}'
        C_correlation_values[cls_name].append(sos_val)
        C_valid_count[cls_name] += 1  # 有效统计像元数 +1

# =============== 计算结果 ===============
print("\n=== 统计结果 ===")
C_mean = {}
C_median = {}
C_std = {}
C_min = {}
C_max = {}

for i in range(n_classes):
    cls_name = f'C{i + 1}'
    total = C_count[cls_name]  # 总像元数
    valid = C_valid_count[cls_name]  # 有效统计像元数
    values = np.array(C_correlation_values[cls_name]) if C_correlation_values[cls_name] else np.array([])

    if len(values) > 0:
        mean_val = np.mean(values)
        median_val = np.median(values)
        std_val = np.std(values)
        min_val = np.min(values)
        max_val = np.max(values)
    else:
        mean_val = np.nan
        median_val = np.nan
        std_val = np.nan
        min_val = np.nan
        max_val = np.nan

    C_mean[cls_name] = mean_val
    C_median[cls_name] = median_val
    C_std[cls_name] = std_val
    C_min[cls_name] = min_val
    C_max[cls_name] = max_val

    print(f"{cls_name}: 总像元={int(total)}, 有效统计像元={int(valid)}")
    print(f"  - 平均降雨: {mean_val:.4f}")
    print(f"  - 中位数: {median_val:.4f}")
    print(f"  - 标准差: {std_val:.4f}")
    print(f"  - 最小值: {min_val:.4f}")
    print(f"  - 最大值: {max_val:.4f}")

# =============== 保存结果 ===============
os.makedirs(output_dir, exist_ok=True)

# 1. 保存相关性统计摘要
stats_df = pd.DataFrame({
    'Class': [f'C{i + 1}' for i in range(n_classes)],
    'Total_Pixels': [C_count[f'C{i + 1}'] for i in range(n_classes)],  # 总像元数
    'Valid_Stats_Pixels': [C_valid_count[f'C{i + 1}'] for i in range(n_classes)],  # 有效统计像元数
    'Mean_Correlation': [C_mean[f'C{i + 1}'] for i in range(n_classes)],
    'Median_Correlation': [C_median[f'C{i + 1}'] for i in range(n_classes)],
    'Std_Correlation': [C_std[f'C{i + 1}'] for i in range(n_classes)],
    'Min_Correlation': [C_min[f'C{i + 1}'] for i in range(n_classes)],
    'Max_Correlation': [C_max[f'C{i + 1}'] for i in range(n_classes)]
})
stats_df.to_csv(os.path.join(output_dir, 'SOS_rainfall_correlation_stats.csv'), index=False)

# 2. 保存每类的相关性值分布（用于进一步分析）
for i in range(n_classes):
    cls_name = f'C{i + 1}'
    values = C_correlation_values[cls_name]
    if values:
        df = pd.DataFrame({
            'Correlation_Value': values
        })
        df.to_csv(os.path.join(output_dir, f'{cls_name}_correlation_values.csv'), index=False)

print(f"\n✅ 所有结果已保存至: {output_dir}")



