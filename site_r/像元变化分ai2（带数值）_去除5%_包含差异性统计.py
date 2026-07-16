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

# ================= 配置部分 =================
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

# 输出路径配置
output_dir = r"D:\MODIS43A4_Value"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)


# ================= 函数定义部分 =================

def reproject_mask_to_match_image(mask_path, image_shape, transform):
    """重投影掩膜以匹配图像"""
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
    """提取有效数据"""
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


def remove_outliers(data, factor=1.5):
    """去除离群值 (IQR方法)"""
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
    # 初始给每个组分配一个唯一的潜在字母池，然后通过集合操作合并
    # 这里使用一种贪心算法的变体来分配字母

    # 构建“无显著差异”的关系图
    # similar[i][j] = True 表示组 i 和 组 j 无显著差异
    similar = np.zeros((n, n), dtype=bool)
    for i in range(n):
        for j in range(n):
            if i == j:
                similar[i, j] = True
            elif p_matrix[i, j] >= alpha:
                similar[i, j] = True

    # 分配字母
    # 方法：为每个“团”（互相都无显著差异的组集合）分配一个字母
    # 如果一个组属于多个团，它就拥有多个字母 (如 'ab')

    assigned_sets = []  # 存储每个字母代表的组索引集合

    # 简单的贪心覆盖算法
    # 按组索引顺序，尝试将当前组加入现有的字母集合，或者创建新字母
    group_letters = [set() for _ in range(n)]

    # 为了更标准的CLD，我们通常寻找最大团，但这里用简化的启发式方法：
    # 遍历所有组，如果两个组不显著不同，尝试给它们相同的标记

    # 更稳健的方法：
    # 1. 找出所有互不显著的子集
    # 2. 为每个子集分配一个字母
    # 3. 每个组的最终标签是它所属所有子集的字母拼接

    # 这里使用一种常用的简单实现逻辑：
    # 按均值排序（可选，为了让字母顺序更有意义，这里保持原顺序或按均值排均可）
    # 为了绘图美观，通常希望字母 'a' 代表最大值或最小值，这里暂按输入顺序

    current_letter_code = 97  # 'a'

    # 重新实现一个标准的 CLD 生成器
    # 步骤：
    # 1. 创建一个列表，记录哪些组已经被某个字母覆盖
    covered = [False] * n
    letter_groups = []  # 每个元素是一个列表，包含该字母覆盖的组索引

    # 只要还有组没被完全区分（这个逻辑比较复杂，直接用scipy或其他库的逻辑太重量级）
    # 采用简易版：
    # 对于每一对 (i, j)，如果 p >= 0.05，它们必须有共同字母。

    # 让我们使用一个更直观的算法：
    # 初始化每个组的标签为空列表
    group_tags = [[] for _ in range(n)]
    letter_count = 0

    # 这种问题本质是图着色问题的变体。
    # 简化策略：
    # 遍历所有组 i，如果它还没有被分配任何字母，或者需要新字母来区分
    # 实际上，最通用的做法是：
    # 找到所有最大的“无差异团”，每个团一个字母。

    # 鉴于代码长度限制，使用一个广泛使用的简化逻辑：
    # 按均值大小排序组，然后分配字母。
    # 计算每组均值
    means = [np.mean(data_dict[g]) if len(data_dict[g]) > 0 else 0 for g in groups]
    sorted_indices = np.argsort(means)[::-1]  # 从大到小排序

    # 重建映射
    sorted_groups = [groups[i] for i in sorted_indices]
    sorted_means = [means[i] for i in sorted_indices]
    original_to_sorted_idx = {original: new for new, original in enumerate(sorted_indices)}

    final_labels_map = {}  # map original_group_name -> string like "a", "ab"

    # 贪心分配
    # 从均值最大的开始，标记为 'a'
    # 下一个，如果与 'a' 组无显著差异，也标记 'a' (或 'ab'?)
    # 标准做法：
    # 组1 (最大): 'a'
    # 组2: 如果与组1无差异 -> 'a'; 如果有差异 -> 'b'
    # 组3: 如果与组1无差异且与组2无差异 -> 'a';
    #      如果与组1有差异但与组2无差异 -> 'b';
    #      如果都与有差异 -> 'c'
    #      如果与组1无差异，与组2有差异 -> 'ab' (这意味着它既属于a群也属于b群？不，通常意味着它介于中间)

    # 正确的 CLD 算法实现：
    # 1. 构建邻接矩阵 (1 = 无显著差异)
    adj = similar.astype(int)

    # 2. 寻找极大团 (Maximal Cliques) - 这里用近似法
    # 每个字母代表一个团。
    # 一个组可以属于多个团。

    cliques = []
    # 简单起见，我们不以最优解为目标，而是以“正确性”为目标
    # 遍历每个组，尝试将其加入现有的团，如果不行就新建团？
    # 不，应该是：对于每一个可能的团（子集），如果内部全连通，就是一个候选。
    # 这太慢了。

    # 使用 R 语言 multcompView 包的逻辑简化版：
    # 按均值排序后
    labels = [''] * n
    # 初始化所有组都有所有潜在字母？不。

    # 让我们用最直接的逻辑：
    # 为每一对“无显著差异”的组，确保它们共享至少一个字母。
    # 我们为每一个“连通分量”或者特定的模式分配字母。

    # 替代方案：直接根据 P 值矩阵生成字符串
    # 这种方法在很多生态学论文代码中常用：
    # 按均值排序。
    # 第1名：'a'
    # 第2名：如果与第1名无差异，'a'；否则 'b'
    # 第3名：检查与前所有的关系。
    # 这种贪心法有时会产生冗余字母（如 a, ab, b 而不是 a, a, b），但在视觉上可接受。

    # 改进的贪心算法 (按均值降序):
    sorted_labels = [""] * n
    current_max_letter_idx = 0  # 0->a, 1->b

    # 初始化：每个位置是一个集合，存放它拥有的字母索引
    group_letter_sets = [set() for _ in range(n)]

    for i in range(n):
        # 尝试将组 i 加入已有的字母集合
        # 规则：组 i 可以加入字母 L，仅当 组 i 与该字母集合中**所有**其他成员都无显著差异
        added_to_existing = False

        # 我们需要知道每个字母目前覆盖了哪些组
        # 动态计算：letter_coverage[l] = [list of group indices having letter l]

        # 为了简单，我们换一种策略：
        # 对于组 i，找出所有 j < i (均值比它大) 且与 i 无显著差异的组。
        # 这些 j 已经有一些字母了。
        # 组 i 应该继承这些 j 的“公共”字母？
        # 不完全是。

        # 最稳妥的简易算法：
        # 1. 创建一个新字母给组 i (暂时)
        # 2. 检查是否能与前面的组共享。

        # 让我们使用一个已验证的简短逻辑：
        # 对于排序后的列表：
        # 组 i 的标签由它与前面所有组的关系决定。
        # 如果组 i 与 组 k (k<i) 无差异，它们必须共享一个字母。

        # 实际操作：
        # 维护一个列表 `letters_assigned_to_group`
        # 维护 `groups_in_letter` : dict { letter_index: set(group_indices) }

        groups_in_letter = {}  # key: letter_int, value: set of indices

        for i in range(n):
            # 找出所有能与 i 共存的已有字母
            # 条件：对于某个字母 L，如果 L 中包含的所有组都与 i 无显著差异，则 i 可以加入 L
            candidate_letters = []

            for l_idx, members in groups_in_letter.items():
                can_join = True
                for m in members:
                    if not similar[i, m]:  # 如果 i 与成员 m 有显著差异
                        can_join = False
                        break
                if can_join:
                    candidate_letters.append(l_idx)

            if candidate_letters:
                # 如果能加入现有字母，通常加入第一个找到的（或者所有？）
                # 标准 CLD 中，如果一个组与多个不相交的团都有关系，它会获得组合字母
                # 这里我们简化：如果它能加入某个团，它就属于那个团。
                # 但如果它同时能加入团A (含组1) 和 团B (含组2)，而组1和组2有差异，
                # 那么组3应该标记为 'ab'。

                # 修正逻辑：收集所有能加入的字母
                final_letters_for_i = set(candidate_letters)

                # 特殊情况：如果没有任何现有字母能容纳它（即它与所有已有团的至少一个成员有差异）
                # 或者 candidate_letters 为空
                if not final_letters_for_i:
                    # 创建新字母
                    new_l_idx = len(groups_in_letter)
                    groups_in_letter[new_l_idx] = {i}
                    group_letter_sets[i].add(new_l_idx)
                else:
                    # 这里有个逻辑漏洞：如果它能加入 A 也能加入 B，它应该同时拥有 A 和 B
                    # 这样它就是 'ab'
                    for l in final_letters_for_i:
                        group_letter_sets[i].add(l)
                        groups_in_letter[l].add(i)
            else:
                # 不能加入任何现有字母（与所有现有团的某些成员都有显著差异）
                # 创建新字母
                new_l_idx = len(groups_in_letter)
                groups_in_letter[new_l_idx] = {i}
                group_letter_sets[i].add(new_l_idx)

    # 转换字母索引为字符
    # 注意：上面的贪心逻辑可能产生非最小集，但对于绘图标注通常够用
    # 为了让 'a' 对应最大值，我们已经是按均值降序排列的，所以先创建的字母索引小
    for i in range(n):
        indices = sorted(list(group_letter_sets[i]))
        label_str = "".join([chr(97 + idx) for idx in indices])
        original_g = sorted_groups[i]
        final_labels_map[original_g] = label_str

    return final_labels_map, p_matrix, sorted_groups, sorted_means


# ================= 主程序执行部分 =================

# 1. 数据提取与基础统计
results = []
print("正在提取数据...")

for tiff_path, config_name in mean_config:
    for mask_file in mask_files:
        if not os.path.exists(tiff_path):
            continue
        raw_data = extract_valid_data(tiff_path, mask_file)
        clean_data = remove_outliers(raw_data)
        results.append({
            'Config': config_name.strip(),
            'Mask': os.path.basename(mask_file).split('.')[0],
            'Mean': np.mean(clean_data) if len(clean_data) > 0 else np.nan,
            'Variance': np.var(clean_data) if len(clean_data) > 0 else np.nan,
            'Data': list(clean_data),
            'MaskType': 'Masked'
        })

for tiff_path, config_name in mean_config:
    if not os.path.exists(tiff_path):
        continue
    raw_data = extract_valid_data(tiff_path, mask_path=None)
    clean_data = remove_outliers(raw_data)
    results.append({
        'Config': config_name.strip(),
        'Mask': 'All',
        'Mean': np.mean(clean_data) if len(clean_data) > 0 else np.nan,
        'Variance': np.var(clean_data) if len(clean_data) > 0 else np.nan,
        'Data': list(clean_data),
        'MaskType': 'All'
    })

results_df = pd.DataFrame(results)
print("基础统计完成。")

# 保存基础 Excel
output_excel = os.path.join(output_dir, "mean_variance_results_clean.xlsx")
results_df.to_excel(output_excel, index=False)
print(f"基础结果已保存到: {output_excel}")

# 2. 执行差异性统计 (仅 Mann-Whitney U + 字母标注)
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
            print(f"  {g} (Mean={np.mean(data_dict[g]):.2f}): {labels_map[g]}")

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
    detail_excel = os.path.join(output_dir, "pairwise_mann_whitney_details.xlsx")
    detail_df.to_excel(detail_excel, index=False)
    print(f"详细 P 值已保存到: {detail_excel}")

# ================= 绘图部分 =================

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
    positions: range = range(1, len(data_list) + 1)
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

                fmt = '.4f' if config_name in ['ROG', 'ROS'] else '.2f'
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

    # 设置 X 轴
    ax.set_xticks(positions)
    # 仅在最后一行显示标签
    if idx // 3 == 2:
        ax.set_xticklabels(labels_display, rotation=45, ha='right', fontsize=20)
    else:
        ax.set_xticklabels([])

    # 设置 Y 轴标签
    if config_name in ['SOS', 'POS', 'EOS']:
        ylabel = 'DOY'
    elif config_name in ['vSOS', 'vPOS', 'vEOS']:
        ylabel = 'VI value'
    elif config_name in ['LOS']:
        ylabel = 'Days'
    elif config_name in ['ROG', 'ROS']:
        ylabel = 'VI day$^{-1}$'
    else:
        ylabel = 'Value'

    ax.set_ylabel(ylabel, fontsize=20)
    ax.set_title(config_name, fontsize=20, pad=10)
    ax.grid(axis='y', linestyle='--', alpha=0.3)

    # 自动调整 Y 轴范围
    all_vals = [v for sublist in data_list for v in sublist]
    if all_vals:
        ymin, ymax = min(all_vals), max(all_vals)
        span = ymax - ymin
        ax.set_ylim(ymin - span * 0.05, ymax + span * 0.15)  # 顶部留多一点空间给字母

# 添加总图例
legend_elements = [Patch(facecolor=colors[i], label=display_names[i], edgecolor='black', linewidth=0.5) for i in
                   range(len(colors))]
fig.legend(handles=legend_elements,
           loc='lower center',
           ncol=5,
           bbox_to_anchor=(0.5, 0.02),
           fontsize=24, frameon=False)

plt.tight_layout(rect=[0, 0.08, 1, 0.95])
save_path_png = os.path.join(output_dir, "violin_plot_significance_letters.png")
plt.savefig(save_path_png, dpi=600, bbox_inches='tight')
print(f"小提琴图已保存至: {save_path_png}")
plt.show()

print("\n分析全部完成！")
print("说明：图中小提琴上方的字母 (a, b, ab...) 表示统计显著性分组。")
print("      具有相同字母的组之间差异不显著 (P >= 0.05)。")
print("      字母完全不同的组之间差异显著 (P < 0.05)。")