import os
import rasterio
import numpy as np
import pandas as pd
from rasterio.enums import Resampling
import rasterio.warp as warp
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Patch
import matplotlib.patheffects as pe

# 设置全局字体大小
plt.rcParams.update({'font.size': 18})
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 定义掩膜文件路径
mask_files = [
    r"D:\MOD12Q2\vs\classai\1.tif",
    r"D:\MOD12Q2\vs\classai\2.tif",
    r"D:\MOD12Q2\vs\classai\3.tif",
    r"D:\MOD12Q2\vs\classai\4.tif"
]

# 定义配置项和TIFF文件路径
mean_config = [
    (r'D:\MODIS43A4_2024\masked_without_tibet\SOS2\mean_values.tif', 'SOS '),
    (r'D:\MODIS43A4_2024\masked_without_tibet\POS2\mean_values.tif', 'POS '),
    (r'D:\MODIS43A4_2024\masked_without_tibet\EOS2\mean_values.tif', 'EOS '),
    (r'D:\MODIS43A4_Value\masked_without_tibet\SOS\mean_values.tif', 'vSOS '),
    (r'D:\MODIS43A4_Value\masked_without_tibet\POS\mean_values.tif', 'vPOS '),
    (r'D:\MODIS43A4_Value\masked_without_tibet\EOS\mean_values.tif', 'vEOS '),
    (r'D:\MODIS43A4_2024\masked_without_tibet\LOS\mean_values.tif', 'LOS '),
    (r'D:\MODIS43A4_2024\masked_without_tibet\ROG\mean_values.tif', 'ROG '),
    (r'D:\MODIS43A4_2024\masked_without_tibet\ROS\mean_values.tif', 'ROS '),
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


# 提取满足条件的像元数据
def extract_valid_data(file_path, mask_path=None):
    try:
        with rasterio.open(file_path) as src_img:
            image = src_img.read(1)
            transform = src_img.transform
            nodata = src_img.nodata

        if mask_path is not None:
            with rasterio.open(mask_path) as src_mask:
                reprojected_mask = reproject_mask_to_match_image(mask_path, image.shape, transform)
                valid_mask = (reprojected_mask == 1)
                valid_image = image[valid_mask]
        else:
            valid_image = image.flatten()

        if nodata is not None:
            valid_image = valid_image[valid_image != nodata]
        valid_image = valid_image[np.isfinite(valid_image)]
        valid_image = valid_image[valid_image != 0]

        return valid_image
    except Exception as e:
        print(f"Error processing {file_path} with mask {mask_path}: {e}")
        return np.array([])


# 去除离群值
def remove_outliers(data, factor=1.5):
    if len(data) == 0:
        return data
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    lower_bound = Q1 - factor * IQR
    upper_bound = Q3 + factor * IQR
    return data[(data >= lower_bound) & (data <= upper_bound)]


# 初始化结果列表
results = []

# 遍历统计
for tiff_path, config_name in mean_config:
    for mask_file in mask_files:
        if not os.path.exists(tiff_path):
            continue
        raw_data = extract_valid_data(tiff_path, mask_file)
        clean_data = remove_outliers(raw_data)
        mean_val = np.mean(clean_data) if len(clean_data) > 0 else np.nan
        var_val = np.var(clean_data) if len(clean_data) > 0 else np.nan
        results.append({
            'Config': config_name.strip(),  # 去掉空格以便后续匹配，如果原意需要保留空格可去掉.strip()
            'Mask': os.path.basename(mask_file).split('.')[0],
            'Mean': mean_val,
            'Variance': var_val,
            'Data': list(clean_data),
            'MaskType': 'Masked'
        })

for tiff_path, config_name in mean_config:
    if not os.path.exists(tiff_path):
        continue
    raw_data = extract_valid_data(tiff_path, mask_path=None)
    clean_data = remove_outliers(raw_data)
    mean_val = np.mean(clean_data) if len(clean_data) > 0 else np.nan
    var_val = np.var(clean_data) if len(clean_data) > 0 else np.nan
    results.append({
        'Config': config_name.strip(),
        'Mask': 'All',
        'Mean': mean_val,
        'Variance': var_val,
        'Data': list(clean_data),
        'MaskType': 'All'
    })

results_df = pd.DataFrame(results)
print("统计结果已生成")

# 保存Excel
output_excel = r"D:\MODIS43A4_Value\mean_variance_results_去除离群值.xlsx"
results_df.to_excel(output_excel, index=False)
print(f"结果已保存到 {output_excel}")

# ================== 提琴图部分（修改了X轴标签逻辑） ==================
mask_labels = [
    'Hyper-arid',
    'Arid',
    'Semi-arid',
    'Subhumid',
    'All'
]

colors = ['#FF6666', '#FFCC66', '#99CC99', '#77AADD', '#AAAAAA']

# 增加整体图形大小，为图例预留空间
fig, axes = plt.subplots(3, 3, figsize=(20, 18))
axes = axes.flatten()

# 注意：这里需要确保 unique_configs 的顺序和 mean_config 一致，且去除了多余空格
unique_configs = [name.strip() for _, name in mean_config]

for idx, config_name in enumerate(unique_configs):
    ax = axes[idx]
    # 确保Config列的名称与unique_configs一致（去除了空格）
    config_data = results_df[results_df['Config'] == config_name].copy()

    masked_data = config_data[config_data['MaskType'] == 'Masked']
    all_data = config_data[config_data['MaskType'] == 'All']

    # 排序掩膜数据 (按文件名数字排序)
    if not masked_data.empty:
        masked_data = masked_data.sort_values('Mask', key=lambda x: x.astype(int))

    combined_data = pd.concat([masked_data, all_data])

    data_list = []
    labels = []
    violin_colors = []

    for _, row in combined_data.iterrows():
        data = row['Data']
        if len(data) > 0:
            data_list.append(data)
            if row['Mask'] == 'All':
                labels.append('All')
                violin_colors.append(colors[4])
            else:
                try:
                    mask_idx = int(row['Mask']) - 1
                    labels.append(mask_labels[mask_idx])
                    violin_colors.append(colors[mask_idx])
                except (ValueError, IndexError):
                    continue

    if len(data_list) == 0:
        ax.set_title(f"{config_name}\n(无有效数据)", fontsize=16)
        ax.axis('off')
        continue

    parts = ax.violinplot(data_list, positions=range(1, len(data_list) + 1), showmeans=True, showmedians=True,
                          showextrema=True)

    for pc, color in zip(parts['bodies'], violin_colors):
        pc.set_facecolor(color)
        pc.set_alpha(0.7)
        pc.set_edgecolor('black')
        pc.set_linewidth(1)

    if 'cmedians' in parts:
        parts['cmedians'].set_color('blue')
        parts['cmedians'].set_linewidth(1)
    if 'cmeans' in parts:
        parts['cmeans'].set_color('red')
        parts['cmeans'].set_linewidth(1)

    # 添加数值标注
    for i, data in enumerate(data_list):
        mean_val = np.mean(data)
        if 'cmeans' in parts:
            segments = parts['cmeans'].get_segments()
            if i < len(segments):
                x_mean = segments[i][0][0]
                y_mean = segments[i][0][1]
                # 对于最后两个子图（ROG和ROS），使用4位小数；其他使用2位小数
                if config_name in ['ROG', 'ROS']:
                    format_str = f'{mean_val:.4f}'
                else:
                    format_str = f'{mean_val:.2f}'

                # 添加白色艺术字标注（最上层，线中间）
                ax.text(x_mean, y_mean, format_str,
                        ha='left', va='bottom',
                        fontsize=18, color='white',
                        weight='bold',
                        path_effects=[pe.withStroke(linewidth=2, foreground='black')],
                        zorder=10)

    # 设置X轴刻度和标签
    ax.set_xticks(range(1, len(data_list) + 1))

    # 【核心修改】仅最后一行显示标签
    # 3x3网格，总共有9个子图，索引0-8。最后一行是索引 6, 7, 8
    # 通用写法：if idx // 3 == 2: (表示第3行，索引从0开始)
    if idx // 3 == 2:
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=24)  # 可选旋转角度以防重叠
    else:
        ax.set_xticklabels([])  # 隐藏标签

    # 动态设置 Y 轴标签
    if config_name in ['SOS', 'POS', 'EOS']:
        ylabel = 'DOY'
    elif config_name in ['vSOS', 'vPOS', 'vEOS']:
        ylabel = 'VI value'
    elif config_name in ['LOS']:
        ylabel = 'days'
    elif config_name in ['ROG', 'ROS']:  # LOS已经在上面判断了，这里修正逻辑避免重复
        ylabel = 'VI day$^{-1}$'
    else:
        ylabel = 'Value'

    # 仅在每行的第一个图或者所有图显示Y轴标签？通常保留所有或仅最左列。
    # 这里保持原逻辑，所有图都显示Y轴标签，除非你想进一步优化
    ax.set_ylabel(ylabel, fontsize=24)

    ax.set_title(config_name, fontsize=18, pad=8)
    ax.grid(axis='y', linestyle='--', alpha=0.4)

    all_data_values = [val for sublist in data_list for val in sublist]
    if len(all_data_values) > 0:
        y_min, y_max = min(all_data_values), max(all_data_values)
        y_range = y_max - y_min
        padding = y_range * 0.05
        ax.set_ylim(y_min - padding, y_max + padding)

# 添加图例 - 调整位置和字体大小
legend_elements = [Patch(facecolor=colors[i], label=mask_labels[i], edgecolor='black', linewidth=0.5) for i in range(len(colors))]
fig.legend(handles=legend_elements,
           loc='lower center',
           ncol=5,
           bbox_to_anchor=(0.5, 0.02),
           fontsize=18)

plt.tight_layout(rect=[0, 0.08, 1, 0.95])
plt.savefig(r"D:\MODIS43A4_Value\mean_variance_violinplot_3x3_去除离群值_trend.png", dpi=600, bbox_inches='tight')
plt.show()
