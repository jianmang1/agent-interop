import os
import rasterio
import numpy as np
import pandas as pd
from rasterio.enums import Resampling
import rasterio.warp as warp
import matplotlib.pyplot as plt

# 定义掩膜文件路径
mask_files = [
    r"D:\MOD12Q2\vs\classai\1.tif",
    r"D:\MOD12Q2\vs\classai\2.tif",
    r"D:\MOD12Q2\vs\classai\3.tif",
    r"D:\MOD12Q2\vs\classai\4.tif"
]

# 定义配置项和TIFF文件路径
mean_config = [
    (r'D:\MODIS43A4_2024\SOS2\slope_values.tif', 'SOS'),
    (r'D:\MODIS43A4_2024\POS2\slope_values.tif', 'POS'),
    (r'D:\MODIS43A4_2024\EOS2\slope_values.tif', 'EOS'),
    (r'D:\MODIS43A4_2024\LOS\slope_values.tif', 'LOS'),
]

# 重投影掩膜函数
def reproject_mask_to_match_image(mask_path, image_shape, transform):
    with rasterio.open(mask_path) as src:
        mask = src.read(1)
        out_profile = src.profile.copy()
        out_profile.update({
            'height': image_shape[0],
            'width': image_shape[1],
            'transform': transform,
            'driver': 'GTiff',
            'dtype': src.meta['dtype']
        })
        reprojected_mask = np.zeros((out_profile['height'], out_profile['width']), dtype=src.meta['dtype'])
        warp.reproject(
            source=mask,
            destination=reprojected_mask,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=out_profile['transform'],
            dst_crs=src.crs,
            resampling=Resampling.nearest
        )
    return reprojected_mask

# 统计满足条件的像元的均值和方差
def calculate_mean_variance(file_path, mask_path):
    try:
        with rasterio.open(file_path) as src_img, rasterio.open(mask_path) as src_mask:
            image = src_img.read(1)
            transform = src_img.transform
            nodata = src_img.nodata

        # 重投影掩膜
        reprojected_mask = reproject_mask_to_match_image(mask_path, image.shape, transform)

        # 应用掩膜（值为1的区域）
        valid_mask = (reprojected_mask == 1)
        valid_image = image[valid_mask]

        # 过滤无效值（nodata 和 NaN/Inf）
        if nodata is not None:
            valid_image = valid_image[valid_image != nodata]
        valid_image = valid_image[np.isfinite(valid_image)]

        # 计算均值和方差
        mean_val = np.mean(valid_image) if len(valid_image) > 0 else np.nan
        var_val = np.var(valid_image) if len(valid_image) > 0 else np.nan

        return mean_val, var_val
    except Exception as e:
        print(f"Error processing {file_path} with mask {mask_path}: {e}")
        return np.nan, np.nan

# 初始化结果列表
results = []

# 遍历每个配置项和掩膜文件
for tiff_path, config_name in mean_config:
    for mask_file in mask_files:
        if not os.path.exists(tiff_path):
            print(f"文件未找到: {tiff_path}. 跳过。")
            continue
        mean_val, var_val = calculate_mean_variance(tiff_path, mask_file)
        results.append({
            'Config': config_name,
            'Mask': os.path.basename(mask_file).split('.')[0],  # 提取掩膜编号
            'Mean': mean_val,
            'Variance': var_val
        })

# 转换为DataFrame
results_df = pd.DataFrame(results)

# 输出统计结果
print("统计结果：")
print(results_df)

# 保存到Excel文件
output_excel = r"D:\MOD12Q2\ratio\slope_variance_results.xlsx"
results_df.to_excel(output_excel, index=False)
print(f"结果已保存到 {output_excel}")

# 可视化：分组柱状图展示均值
fig, ax = plt.subplots(figsize=(12, 7))
bar_width = 0.2
index = np.arange(len(mean_config))

# 定义掩膜编号
masks = [os.path.basename(mask_file).split('.')[0] for mask_file in mask_files]

# 定义颜色和图例标签
colors = ['#FF6666', '#FFCC66', '#99CC99', '#77AADD']
legend_labels = [
    'Hyper-arid (AI < 0.05)',
    'Arid (0.05 ≤ AI < 0.2)',
    'Semi-arid (0.2 ≤ AI < 0.5)',
    'Subhumid (0.5 ≤ AI < 0.65)'
]

# 绘制每个掩膜下的均值
for i, mask in enumerate(masks):
    subset = results_df[results_df['Mask'] == mask]
    means = subset['Mean'].values
    std_dev = np.sqrt(subset['Variance'].values)
    ax.bar(index + i * bar_width, means, bar_width, label=legend_labels[i], color=colors[i], alpha=0.8)

# 添加标签和标题
#ax.set_xlabel('Configuration', fontsize=12)
ax.set_ylabel('Trend Value', fontsize=12)
#ax.set_title('Mean of Valid Pixels by Configuration and Mask', fontsize=14)
ax.set_xticks(index + bar_width * 1.5)
ax.set_xticklabels([config for _, config in mean_config], rotation=0, ha='center')  # 修改这里
ax.legend(title='')  # 去除图例标题
plt.tight_layout()
plt.show()