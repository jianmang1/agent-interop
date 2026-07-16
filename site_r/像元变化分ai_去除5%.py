import os
import rasterio
import numpy as np
import pandas as pd
from rasterio.enums import Resampling
import rasterio.warp as warp
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Patch

# 设置全局字体大小
plt.rcParams.update({'font.size': 10})
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
    (r'D:\MODIS43A4_2024\masked_without_tibet\ROG\mean_values.tif', 'ROG '),  # 修正路径
    (r'D:\MODIS43A4_2024\masked_without_tibet\ROS\mean_values.tif', 'ROS '),  # 修正路径
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


# 提取满足条件的像元数据（过滤掉小于1的值）
def extract_valid_data(file_path, mask_path=None):
    try:
        with rasterio.open(file_path) as src_img:
            image = src_img.read(1)
            transform = src_img.transform
            nodata = src_img.nodata

        # 如果提供了掩膜路径，则应用掩膜
        if mask_path is not None:
            with rasterio.open(mask_path) as src_mask:
                reprojected_mask = reproject_mask_to_match_image(mask_path, image.shape, transform)
                # 应用掩膜（值为1的区域）
                valid_mask = (reprojected_mask == 1)
                valid_image = image[valid_mask]
        else:
            # 如果没有掩膜，使用全部数据
            valid_image = image.flatten()

        # 过滤无效值（nodata 和 NaN/Inf）
        if nodata is not None:
            valid_image = valid_image[valid_image != nodata]
        valid_image = valid_image[np.isfinite(valid_image)]

        # 过滤掉小于1的值
        valid_image = valid_image[valid_image != 0]  # 修改：保留大于等于1的值

        return valid_image
    except Exception as e:
        print(f"Error processing {file_path} with mask {mask_path}: {e}")
        return np.array([])


# 去除离群值的函数（使用IQR方法）
def remove_outliers(data, factor=1.5):
    if len(data) == 0:
        return data

    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    lower_bound = Q1 - factor * IQR
    upper_bound = Q3 + factor * IQR

    # 返回在范围内的数据
    return data[(data >= lower_bound) & (data <= upper_bound)]


# 初始化结果列表
results = []

# 遍历每个配置项和掩膜文件
for tiff_path, config_name in mean_config:
    for mask_file in mask_files:
        if not os.path.exists(tiff_path):
            print(f"文件未找到: {tiff_path}. 跳过。")
            continue
        raw_data = extract_valid_data(tiff_path, mask_file)
        # 去除离群值
        clean_data = remove_outliers(raw_data)
        mean_val = np.mean(clean_data) if len(clean_data) > 0 else np.nan
        var_val = np.var(clean_data) if len(clean_data) > 0 else np.nan
        results.append({
            'Config': config_name,
            'Mask': os.path.basename(mask_file).split('.')[0],
            'Mean': mean_val,
            'Variance': var_val,
            'Data': list(clean_data),
            'MaskType': 'Masked'
        })

# 添加全幅统计（不使用掩膜）
for tiff_path, config_name in mean_config:
    if not os.path.exists(tiff_path):
        print(f"文件未找到: {tiff_path}. 跳过。")
        continue
    raw_data = extract_valid_data(tiff_path, mask_path=None)
    # 去除离群值
    clean_data = remove_outliers(raw_data)
    mean_val = np.mean(clean_data) if len(clean_data) > 0 else np.nan
    var_val = np.var(clean_data) if len(clean_data) > 0 else np.nan
    results.append({
        'Config': config_name,
        'Mask': 'All',
        'Mean': mean_val,
        'Variance': var_val,
        'Data': list(clean_data),
        'MaskType': 'All'
    })

# 转换为DataFrame
results_df = pd.DataFrame(results)

# 输出统计结果
print("统计结果：")
print(results_df)

# 保存到Excel文件
output_excel = r"D:\MODIS43A4_Value\mean_variance_results_去除离群值.xlsx"
results_df.to_excel(output_excel, index=False)
print(f"结果已保存到 {output_excel}")

# ================== 提琴图部分（带动态Y轴标签） ==================
mask_labels = [
    'Hyper-arid (AI < 0.05)',
    'Arid (0.05 ≤ AI < 0.2)',
    'Semi-arid (0.2 ≤ AI < 0.5)',
    'Subhumid (0.5 ≤ AI < 0.65)',
    'All'
]

colors = ['#FF6666', '#FFCC66', '#99CC99', '#77AADD', '#AA99FF']

# 创建3x3子图
fig, axes = plt.subplots(3, 3, figsize=(18, 15))
axes = axes.flatten()

unique_configs = [name for _, name in mean_config]

# 按配置绘制
for idx, config_name in enumerate(unique_configs):
    ax = axes[idx]
    config_data = results_df[results_df['Config'] == config_name].copy()

    # 分离掩膜数据和全幅数据
    masked_data = config_data[config_data['MaskType'] == 'Masked']
    all_data = config_data[config_data['MaskType'] == 'All']

    # 排序掩膜数据
    masked_data = masked_data.sort_values('Mask', key=lambda x: x.astype(int))

    # 合并数据：先掩膜数据，后全幅数据
    combined_data = pd.concat([masked_data, all_data])

    data_list = []
    labels = []
    violin_colors = []

    for _, row in combined_data.iterrows():
        data = row['Data']
        if len(data) > 0:
            data_list.append(data)
            labels.append(row['Mask'])
            if row['Mask'] == 'All':
                mask_idx = 4  # All对应最后一个颜色
            else:
                mask_idx = int(row['Mask']) - 1
            violin_colors.append(colors[mask_idx])

    if len(data_list) == 0:
        ax.set_title(f"{config_name}\n(无有效数据)", fontsize=12)
        ax.axis('off')
        continue

    # 绘制提琴图
    parts = ax.violinplot(data_list, positions=range(1, len(data_list) + 1), showmeans=True, showmedians=True,
                          showextrema=True)

    # 设置颜色
    for pc, color in zip(parts['bodies'], violin_colors):
        pc.set_facecolor(color)
        pc.set_alpha(0.7)
        pc.set_edgecolor('black')
        pc.set_linewidth(1)

    # 设置其他元素的颜色 - 修复原始代码中的错误
    for partname in ('cbars', 'cmins', 'cmaxes'):
        if partname in parts:
            # 检查是否为LineCollection对象
            if hasattr(parts[partname], '__iter__'):
                for pc in parts[partname]:
                    pc.set_color('black')
                    pc.set_linewidth(1)
            else:
                # 如果不是可迭代对象，直接设置颜色
                parts[partname].set_color('black')
                parts[partname].set_linewidth(1)

    # 特别处理cmedians和cmeans
    if 'cmedians' in parts:
        if hasattr(parts['cmedians'], '__iter__') and not isinstance(parts['cmedians'], mpl.collections.LineCollection):
            for pc in parts['cmedians']:
                pc.set_color('black')
                pc.set_linewidth(1)
        else:
            parts['cmedians'].set_color('black')
            parts['cmedians'].set_linewidth(1)

    if 'cmeans' in parts:
        if hasattr(parts['cmeans'], '__iter__') and not isinstance(parts['cmeans'], mpl.collections.LineCollection):
            for pc in parts['cmeans']:
                pc.set_color('black')
                pc.set_linewidth(1)
        else:
            parts['cmeans'].set_color('black')
            parts['cmeans'].set_linewidth(1)

    # 设置X轴标签
    ax.set_xticks(range(1, len(data_list) + 1))
    ax.set_xticklabels(labels)

    # 动态设置 Y 轴标签
    if config_name in ['SOS', 'POS', 'EOS']:
        ylabel = 'DOY'
    elif config_name in ['vSOS', 'vPOS', 'vEOS']:
        ylabel = 'VI value'
    elif config_name in ['AOS', 'ROG', 'ROS']:
        ylabel = 'VI day$^{-1}$'  # 使用上标表示 -1
    else:
        ylabel = 'Value'

    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(config_name, fontsize=12, pad=8)
    ax.grid(axis='y', linestyle='--', alpha=0.4)

    # 自动调整Y轴范围 - 使用去除离群值后的数据范围
    all_data_values = [val for sublist in data_list for val in sublist]
    if len(all_data_values) > 0:
        y_min, y_max = min(all_data_values), max(all_data_values)
        y_range = y_max - y_min
        padding = y_range * 0.05  # 添加5%的边距
        ax.set_ylim(y_min - padding, y_max + padding)

# 添加图例
legend_elements = [Patch(facecolor=colors[i], label=mask_labels[i]) for i in range(len(colors))]
fig.legend(handles=legend_elements,
           loc='lower center',
           ncol=5,
           bbox_to_anchor=(0.5, 0.01),
           fontsize=10)


# 布局调整
plt.tight_layout(rect=[0, 0.05, 1, 0.95])
plt.savefig(r"D:\MODIS43A4_Value\mean_variance_violinplot_3x3_去除离群值.png", dpi=600, bbox_inches='tight')
plt.show()