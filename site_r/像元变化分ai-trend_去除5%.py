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
from scipy import stats
from itertools import combinations

# ================== 全局设置 (大字体风格) ==================
plt.rcParams.update({'font.size': 20})  # 全局字体大小 20
plt.rcParams['font.sans-serif'] = ['SimHei']  # 正常显示中文
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

# ================== 文件路径配置 ==================
# 定义掩膜文件路径
mask_files = [
    r"D:\MOD12Q2\vs\classai\1.tif",
    r"D:\MOD12Q2\vs\classai\2.tif",
    r"D:\MOD12Q2\vs\classai\3.tif",
    r"D:\MOD12Q2\vs\classai\4.tif"
]

# 定义配置项和TIFF文件路径 (使用 slope_values.tif)
mean_config = [
    (r'D:\MODIS43A4_2024\masked_without_tibet\SOS2\slope_values.tif', 'SOS slope'),
    (r'D:\MODIS43A4_2024\masked_without_tibet\POS2\slope_values.tif', 'POS slope'),
    (r'D:\MODIS43A4_2024\masked_without_tibet\EOS2\slope_values.tif', 'EOS slope'),
    (r'D:\MODIS43A4_Value\masked_without_tibet\SOS\slope_values.tif', 'vSOS slope'),
    (r'D:\MODIS43A4_Value\masked_without_tibet\POS\slope_values.tif', 'vPOS slope'),
    (r'D:\MODIS43A4_Value\masked_without_tibet\EOS\slope_values.tif', 'vEOS slope'),
    (r'D:\MODIS43A4_2024\masked_without_tibet\LOS\slope_values.tif', 'LOS slope'),
    (r'D:\MODIS43A4_2024\masked_without_tibet\ROG\slope_values.tif', 'ROG slope'),
    (r'D:\MODIS43A4_2024\masked_without_tibet\ROS\slope_values.tif', 'ROS slope'),
]

# 输出目录
output_dir = r"D:\MODIS43A4_Value"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)


# ================== 函数定义 ==================

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
        # 注意：对于斜率数据，可能包含负值，这里不再强制过滤 != 0，除非确定0是无效值
        # 如果斜率0代表无效，保留下行；如果斜率可以是0，请注释掉下行
        valid_image = valid_image[valid_image != 0]

        return valid_image
    except Exception as e:
        print(f"Error processing {file_path} with mask {mask_path}: {e}")
        return np.array([])


def remove_outliers(data, factor=1.5):
    if len(data) == 0:
        return data
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    lower_bound = Q1 - factor * IQR
    upper_bound = Q3 + factor * IQR
    return data[(data >= lower_bound) & (data <= upper_bound)]


def perform_pairwise_mann_whitney(data_dict, alpha=0.05):
    """
    执行两两 Mann-Whitney U 检验，并生成显著性字母标注
    返回：(p_value矩阵, 字母标注列表)
    """
    groups = list(data_dict.keys())
    n = len(groups)

    # 初始化 P 值矩阵 (对称矩阵)
    p_matrix = np.ones((n, n))
    group_indices = {g: i for i, g in enumerate(groups)}

    # 1. 执行两两检验
    for (g1, g2) in combinations(groups, 2):
        d1 = data_dict[g1]
        d2 = data_dict[g2]

        if len(d1) > 0 and len(d2) > 0:
            try:
                _, p_val = stats.mannwhitneyu(d1, d2, alternative='two-sided')
                i, j = group_indices[g1], group_indices[g2]
                p_matrix[i, j] = p_val
                p_matrix[j, i] = p_val
            except:
                pass

    # 2. 生成字母标注 (Compact Letter Display 算法简化版)
    # 逻辑：如果 p >= alpha，则认为两组无显著差异，应共享字母
    letters = [''] * n

    # 构建"无显著差异"的关系图
    # similar[i][j] = True 表示组 i 和 组 j 无显著差异
    similar = np.zeros((n, n), dtype=bool)
    for i in range(n):
        for j in range(n):
            if i == j:
                similar[i, j] = True
            elif p_matrix[i, j] >= alpha:
                similar[i, j] = True

    # 按均值大小排序组，然后分配字母
    # 计算每组均值
    means = [np.mean(data_dict[g]) if len(data_dict[g]) > 0 else 0 for g in groups]
    sorted_indices = np.argsort(means)[::-1]  # 从大到小排序

    # 重建映射
    sorted_groups = [groups[i] for i in sorted_indices]
    sorted_means = [means[i] for i in sorted_indices]
    original_to_sorted_idx = {original: new for new, original in enumerate(sorted_indices)}

    final_labels_map = {}  # map original_group_name -> string like "a", "ab"

    # 改进的贪心算法 (按均值降序):
    sorted_labels = [""] * n
    # 初始化所有组都有所有潜在字母？不。

    # 初始化：每个位置是一个集合，存放它拥有的字母索引
    group_letter_sets = [set() for _ in range(n)]

    groups_in_letter = {}  # key: letter_int, value: set of indices

    for i in range(n):
        # 找出所有能与 i 共存的已有字母
        # 条件：对于某个字母 L，如果 L 中包含的所有组都与 i 无显著差异，则 i 可以加入 L
        candidate_letters = []

        for l_idx, members in groups_in_letter.items():
            can_join = True
            for m in members:
                if not similar[sorted_indices[i], m]:  # 如果 i 与成员 m 有显著差异
                    can_join = False
                    break
            if can_join:
                candidate_letters.append(l_idx)

        if candidate_letters:
            # 收集所有能加入的字母
            final_letters_for_i = set(candidate_letters)

            # 特殊情况：如果没有任何现有字母能容纳它
            if not final_letters_for_i:
                # 创建新字母
                new_l_idx = len(groups_in_letter)
                groups_in_letter[new_l_idx] = {sorted_indices[i]}
                group_letter_sets[i].add(new_l_idx)
            else:
                # 如果它能加入 A 也能加入 B，它应该同时拥有 A 和 B
                # 这样它就是 'ab'
                for l in final_letters_for_i:
                    group_letter_sets[i].add(l)
                    groups_in_letter[l].add(sorted_indices[i])
        else:
            # 不能加入任何现有字母（与所有现有团的某些成员都有显著差异）
            # 创建新字母
            new_l_idx = len(groups_in_letter)
            groups_in_letter[new_l_idx] = {sorted_indices[i]}
            group_letter_sets[i].add(new_l_idx)

    # 转换字母索引为字符
    for i in range(n):
        indices = sorted(list(group_letter_sets[i]))
        label_str = "".join([chr(97 + idx) for idx in indices])
        original_g = sorted_groups[i]
        final_labels_map[original_g] = label_str

    return final_labels_map, p_matrix, sorted_groups, sorted_means


# ================== 数据处理 ==================
results = []

# 遍历每个配置项和掩膜文件
for tiff_path, config_name in mean_config:
    for mask_file in mask_files:
        if not os.path.exists(tiff_path):
            continue
        raw_data = extract_valid_data(tiff_path, mask_file)
        clean_data = remove_outliers(raw_data)
        mean_val = np.mean(clean_data) if len(clean_data) > 0 else np.nan
        var_val = np.var(clean_data) if len(clean_data) > 0 else np.nan
        results.append({
            'Config': config_name.strip(),
            'Mask': os.path.basename(mask_file).split('.')[0],
            'Mean': mean_val,
            'Variance': var_val,
            'Data': list(clean_data),
            'MaskType': 'Masked'
        })

# 添加全幅统计
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
output_excel = os.path.join(output_dir, "mean_variance_results_slope_去除离群值.xlsx")
results_df.to_excel(output_excel, index=False)
print(f"结果已保存到 {output_excel}")

# 3. 执行差异性统计 (仅 Mann-Whitney U + 字母标注)
print("\n正在执行差异性统计 (Mann-Whitney U)...")
statistical_results = {}  # 存储每个 Config 的字母标注结果

for config_name in results_df['Config'].unique():
    config_data = results_df[results_df['Config'] == config_name]
    data_dict = {}
    for _, row in config_data.iterrows():
        mask_label = row['Mask']
        data = np.array(row['Data'])
        if len(data) > 0:
            data_dict[mask_label] = data

    if len(data_dict) > 1:
        # 获取字母标注
        # 返回：{group_name: "a"}, p_matrix, sorted_groups, sorted_means
        labels_map, p_mat, s_groups, s_means = perform_pairwise_mann_whitney(data_dict, alpha=0.05)

        statistical_results[config_name] = {
            'labels': labels_map,
            'p_matrix': p_mat,
            'sorted_groups': s_groups,
            'sorted_means': s_means,
            'original_groups': list(data_dict.keys())
        }

        # 打印简要结果
        print(f"\n{config_name}:")
        for g in s_groups:
            print(f"  {g} (Mean={np.mean(data_dict[g]):.4f}): {labels_map[g]}")

# 保存统计详情到 Excel (可选，保存 P 值矩阵)
stat_details = []
for config_name, res in statistical_results.items():
    groups = res['original_groups']
    n = len(groups)
    if n < 2: continue

    # 展平矩阵
    for i, g1 in enumerate(groups):
        for j, g2 in enumerate(groups):
            if i < j:
                p_val = res['p_matrix'][i, j]
                sig = "Yes" if p_val < 0.05 else "No"
                stat_details.append({
                    'Config': config_name,
                    'Group1': g1,
                    'Group2': g2,
                    'P_Value': p_val,
                    'Significant_Difference': sig
                })

if stat_details:
    detail_df = pd.DataFrame(stat_details)
    detail_excel = os.path.join(output_dir, "pairwise_mann_whitney_details_slope.xlsx")
    detail_df.to_excel(detail_excel, index=False)
    print(f"详细 P 值已保存到: {detail_excel}")

# ================== 绘图部分 ==================
mask_labels_map = {
    '1': 'Hyper-arid',
    '2': 'Arid',
    '3': 'Semi-arid',
    '4': 'Subhumid',
    'All': 'All'
}
# 为了绘图顺序一致，我们定义标准顺序
standard_mask_order = ['1', '2', '3', '4', 'All']
display_names = ['Hyper-arid', 'Arid', 'Semi-arid', 'Subhumid', 'All']
colors = ['#FF6666', '#FFCC66', '#99CC99', '#77AADD', '#AAAAAA']

# 创建3x3子图，调整大小为 (20, 18)
fig, axes = plt.subplots(3, 3, figsize=(20, 18))
axes = axes.flatten()

unique_configs = [name.strip() for _, name in mean_config]

for idx, config_name in enumerate(unique_configs):
    ax = axes[idx]
    config_data = results_df[results_df['Config'] == config_name].copy()

    # 过滤出有效的 Mask 类型并排序
    valid_masks = [m for m in standard_mask_order if m in config_data['Mask'].values]
    # 确保 'All' 在最后
    if 'All' in valid_masks:
        valid_masks.remove('All')
        valid_masks.append('All')

    data_list = []
    labels_display = []
    violin_colors = []
    letter_annotations = []  # 存储对应的字母

    has_stats = config_name in statistical_results
    stats_obj = statistical_results.get(config_name, {})
    labels_map = stats_obj.get('labels', {})

    for mask_key in valid_masks:
        row = config_data[config_data['Mask'] == mask_key]
        if row.empty:
            continue

        data = np.array(row.iloc[0]['Data'])
        if len(data) == 0:
            continue

        data_list.append(data)

        # 显示名称
        disp_name = mask_labels_map.get(mask_key, mask_key)
        labels_display.append(disp_name)

        # 颜色
        if mask_key == 'All':
            violin_colors.append(colors[-1])
        else:
            try:
                c_idx = int(mask_key) - 1
                violin_colors.append(colors[c_idx])
            except:
                violin_colors.append('#CCCCCC')

        # 获取字母标注
        if has_stats and mask_key in labels_map:
            letter_annotations.append(labels_map[mask_key])
        else:
            letter_annotations.append("")

    if len(data_list) == 0:
        ax.set_title(f"{config_name}\n(无有效数据)", fontsize=16)
        ax.axis('off')
        continue

    # 绘制小提琴图
    positions = range(1, len(data_list) + 1)
    parts = ax.violinplot(data_list, positions=positions, showmeans=True, showmedians=True, showextrema=True)

    # 设置颜色
    for pc, color in zip(parts['bodies'], violin_colors):
        pc.set_facecolor(color)
        pc.set_alpha(0.7)
        pc.set_edgecolor('black')
        pc.set_linewidth(1)

    # 设置中线和均值线颜色
    if 'cmedians' in parts:
        parts['cmedians'].set_color('blue')
        parts['cmedians'].set_linewidth(1.5)
    if 'cmeans' in parts:
        parts['cmeans'].set_color('red')
        parts['cmeans'].set_linewidth(1.5)

    # 添加均值数值标注 (白色描边)
    for i, data in enumerate(data_list):
        mean_val = np.mean(data)
        if 'cmeans' in parts:
            segments = parts['cmeans'].get_segments()
            if i < len(segments):
                x_mean = segments[i][0][0]
                y_mean = segments[i][0][1]

                fmt = '.4f' if config_name in ['ROG slope', 'ROS slope'] else '.4f'
                txt = f'{mean_val:{fmt}}'

                ax.text(x_mean, y_mean, txt,
                        ha='left', va='bottom',
                        fontsize=24, color='white',
                        weight='bold',
                        path_effects=[pe.withStroke(linewidth=2, foreground='black')],
                        zorder=10)

    # 【核心功能】添加显著性字母标注
    # 位置：小提琴顶部的上方
    for i, letter in enumerate(letter_annotations):
        if not letter:
            continue
        x_pos = positions[i]
        # 获取该小提琴的最大值 (extrema 的最大值)
        # parts['cmaxima'] 包含最大值线段
        if 'cmaxima' in parts:
            segs = parts['cmaxima'].get_segments()
            if i < len(segs):
                y_top = segs[i][0][1]  # 最大值点的 Y
            else:
                y_top = np.max(data_list[i])
        else:
            y_top = np.max(data_list[i])

        # 在顶部上方一点的位置写字母
        y_offset = (np.max(data_list[i]) - np.min(data_list[i])) * 0.05
        ax.text(x_pos, y_top + y_offset, letter,
                ha='center', va='bottom',
                fontsize=22, fontweight='bold',
                color='black',
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.6, pad=1),
                zorder=11)

    # 设置X轴刻度
    ax.set_xticks(positions)
    # 【核心修改】仅最后一行显示标签 (idx // 3 == 2)
    if idx // 3 == 2:
        ax.set_xticklabels(labels_display, rotation=45, ha='right', fontsize=20)
    else:
        ax.set_xticklabels([])  # 隐藏非最后一行的标签

    # 动态设置 Y 轴标签
    if config_name in ['SOS slope', 'POS slope', 'EOS slope', 'LOS slope']:
        ylabel = 'days year$^{-1}$'
    elif config_name in ['vSOS slope', 'vPOS slope', 'vEOS slope']:
        ylabel = 'VI year$^{-1}$'
    elif config_name in ['ROG slope', 'ROS slope']:
        ylabel = 'VI day$^{-1}$ year$^{-1}$'
    else:
        ylabel = 'Value'

    ax.set_ylabel(ylabel, fontsize=20)
    ax.set_title(config_name, fontsize=20, pad=10)
    ax.grid(axis='y', linestyle='--', alpha=0.3)

    # 自动调整Y轴范围
    all_data_values = [val for sublist in data_list for val in sublist]
    if len(all_data_values) > 0:
        y_min, y_max = min(all_data_values), max(all_data_values)
        y_range = y_max - y_min
        padding = y_range * 0.15  # 顶部留多一点空间给字母
        ax.set_ylim(y_min - padding * 0.33, y_max + padding)

# 添加图例 (字体大小调整为 24)
legend_elements = [Patch(facecolor=colors[i], label=display_names[i], edgecolor='black', linewidth=0.5) for i in
                   range(len(colors))]
fig.legend(handles=legend_elements,
           loc='lower center',
           ncol=5,
           bbox_to_anchor=(0.5, 0.02),
           fontsize=24, frameon=False)

# 布局调整
plt.tight_layout(rect=[0, 0.08, 1, 0.95])

# 保存高 DPI 图片
output_png = os.path.join(output_dir, "mean_variance_violinplot_3x3_slope_去除离群值_带显著性标注.png")
plt.savefig(output_png, dpi=600, bbox_inches='tight')
print(f"图片已保存到 {output_png}")

plt.show()

print("\n分析全部完成！")
print("说明：图中小提琴上方的字母 (a, b, ab...) 表示统计显著性分组。")
print("      具有相同字母的组之间差异不显著 (P >= 0.05)。")
print("      字母完全不同的组之间差异显著 (P < 0.05)。")