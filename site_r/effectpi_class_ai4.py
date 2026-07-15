import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import rcParams
import numpy as np

# 设置中文字体支持
rcParams['font.sans-serif'] = ['Times New Roman','DejaVu Sans']  # 支持中文显示
rcParams['axes.unicode_minus'] = False  # 正确显示负号

# 设置文件路径
mcd12_path = r'D:\MOD12Q2\ratio\plantclass\mcd12'
mcd43_path = r'D:\MOD12Q2\ratio\plantclass\mcd43'

# 初始化数据框列表
dataframes_mcd12 = []
dataframes_mcd43 = []

# 读取mcd12下的文件 (只处理1-4和7号文件)
files_to_process = [1, 2, 3, 4, 7]
for i in files_to_process:
    file_path = os.path.join(mcd12_path, f'pixel_ratio_results_{i}.xlsx')
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        df['Source'] = 'MCD12'
        df['File'] = i
        dataframes_mcd12.append(df)
        print(f"Loaded MCD12 file: pixel_ratio_results_{i}.xlsx")
    else:
        print(f"Warning: {file_path} does not exist")

# 读取mcd43下的文件 (只处理1-4和7号文件)
for i in files_to_process:
    file_path = os.path.join(mcd43_path, f'pixel_ratio_results_{i}.xlsx')
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        df['Source'] = 'MCD43'
        df['File'] = i
        dataframes_mcd43.append(df)
        print(f"Loaded MCD43 file: pixel_ratio_results_{i}.xlsx")
    else:
        print(f"Warning: {file_path} does not exist")

# 检查是否有数据
if not dataframes_mcd12 and not dataframes_mcd43:
    raise ValueError("No valid data files found!")

# 合并所有数据框
if dataframes_mcd12:
    combined_df_mcd12 = pd.concat(dataframes_mcd12, ignore_index=True)
else:
    combined_df_mcd12 = pd.DataFrame(columns=['Year', 'Ratio', 'Source', 'File'])

if dataframes_mcd43:
    combined_df_mcd43 = pd.concat(dataframes_mcd43, ignore_index=True)
else:
    combined_df_mcd43 = pd.DataFrame(columns=['Year', 'Ratio', 'Source', 'File'])

# 按Year, Source, File分组，并计算Ratio的总和
if not combined_df_mcd12.empty:
    grouped_df_mcd12 = combined_df_mcd12.pivot_table(index='Year', columns=['Source', 'File'], values='Ratio',
                                                     aggfunc='sum').fillna(0)
    grouped_df_mcd12 = grouped_df_mcd12.reset_index()
else:
    grouped_df_mcd12 = pd.DataFrame(columns=['Year'])

if not combined_df_mcd43.empty:
    grouped_df_mcd43 = combined_df_mcd43.pivot_table(index='Year', columns=['Source', 'File'], values='Ratio',
                                                     aggfunc='sum').fillna(0)
    grouped_df_mcd43 = grouped_df_mcd43.reset_index()
else:
    grouped_df_mcd43 = pd.DataFrame(columns=['Year'])

# 合并两个数据框
if not grouped_df_mcd12.empty and not grouped_df_mcd43.empty:
    merged_df = pd.merge(grouped_df_mcd12, grouped_df_mcd43, on='Year', how='outer')
elif not grouped_df_mcd12.empty:
    merged_df = grouped_df_mcd12
elif not grouped_df_mcd43.empty:
    merged_df = grouped_df_mcd43
else:
    raise ValueError("No valid data to plot!")

# 获取实际存在的文件编号
existing_files_mcd12 = [col[1] for col in merged_df.columns if isinstance(col, tuple) and col[0] == 'MCD12']
existing_files_mcd43 = [col[1] for col in merged_df.columns if isinstance(col, tuple) and col[0] == 'MCD43']
all_existing_files = sorted(set(existing_files_mcd12 + existing_files_mcd43))

# 提取Ratio列
try:
    mcd12_cols = [('MCD12', i) for i in all_existing_files if ('MCD12', i) in merged_df.columns]
    mcd43_cols = [('MCD43', i) for i in all_existing_files if ('MCD43', i) in merged_df.columns]

    # 过滤实际存在的列
    existing_mcd12_cols = [col for col in mcd12_cols if col in merged_df.columns]
    existing_mcd43_cols = [col for col in mcd43_cols if col in merged_df.columns]

    if existing_mcd12_cols:
        ratios_mcd12 = merged_df[existing_mcd12_cols].values.T
    else:
        ratios_mcd12 = None

    if existing_mcd43_cols:
        ratios_mcd43 = merged_df[existing_mcd43_cols].values.T
    else:
        ratios_mcd43 = None

except KeyError as e:
    print(f"KeyError: {e}")
    print("Columns in merged_df:", merged_df.columns.tolist())
    ratios_mcd12 = None
    ratios_mcd43 = None

years = merged_df['Year'].astype(int)  # 确保年份为整数

# 根据实际文件数量调整宽度和颜色
num_files = len(all_existing_files)
width = 0.35
x = range(len(years))

# 定义颜色列表（使用更直观的颜色对应土地类型）
colors = [
    '#F4A460',  # 沙棕色 - 农田
    '#228B22',  # 森林绿 - 森林
    '#9ACD32',  # 黄绿色 - 灌木
    '#32CD32',  # 酸 lime 绿 - 草原
    '#8B4513'   # 巧克力色 - 裸地 (对应文件7)
]

# 对应的中文标签（为5个文件提供标签：1-4和7）
legend_labels_map = {
    1: 'Cropland',
    2: 'Forest',
    3: 'Shrubland',
    4: 'Grassland',
    7: 'Barren'
}

# 根据实际文件创建对应的标签
legend_labels = [legend_labels_map.get(i, f'类别{i}') for i in all_existing_files]

fig, ax = plt.subplots(figsize=(16, 10))

bottom_mcd12 = [0] * len(years) if ratios_mcd12 is not None else [0] * len(years)
bottom_mcd43 = [0] * len(years) if ratios_mcd43 is not None else [0] * len(years)

# 绘制MCD12堆叠柱状图（带黑色边框）
if ratios_mcd12 is not None:
    for i in range(ratios_mcd12.shape[0]):
        file_num = existing_mcd12_cols[i][1]  # 获取文件编号
        color_idx = all_existing_files.index(file_num)  # 获取在总列表中的位置
        ax.bar(x, ratios_mcd12[i], width, bottom=bottom_mcd12,
               color=colors[color_idx], edgecolor='black', linewidth=2)
        bottom_mcd12 = [bottom_mcd12[j] + ratios_mcd12[i][j] for j in range(len(years))]

# 绘制MCD43堆叠柱状图（无边框）
if ratios_mcd43 is not None:
    offset_x = [pos + width for pos in x]
    for i in range(ratios_mcd43.shape[0]):
        file_num = existing_mcd43_cols[i][1]  # 获取文件编号
        color_idx = all_existing_files.index(file_num)  # 获取在总列表中的位置
        ax.bar(offset_x, ratios_mcd43[i], width, bottom=bottom_mcd43,
               color=colors[color_idx], edgecolor='gray', linewidth=0.5)
        bottom_mcd43 = [bottom_mcd43[j] + ratios_mcd43[i][j] for j in range(len(years))]

# 图表美化（使用中文标签）
ax.set_xlabel('Year', fontsize=30)
ax.set_ylabel('Total Ratio', fontsize=30)

# 修正x轴刻度为整数
ax.set_xticks([int(pos + width / 2) if ratios_mcd12 is not None else int(pos) for pos in x])
ax.set_xticklabels([int(year) for year in years], fontsize=30, rotation=45, ha='right')

ax.tick_params(axis='y', labelsize=30)

# 创建组合图例 - 包含数据产品类型和植被类型
from matplotlib.patches import Patch

# 数据产品类型图例项
product_legend_items = []
if ratios_mcd12 is not None:
    product_legend_items.append(Patch(facecolor='lightgray', edgecolor='black', linewidth=2, label='MCD12Q2'))
if ratios_mcd43 is not None:
    product_legend_items.append(Patch(facecolor='lightgray', edgecolor='gray', linewidth=0.5, label='MCD43A4'))

# 植被类型图例项（仅显示实际使用的数量）
actual_num_files = len(all_existing_files)
type_legend_items = []
for i, file_num in enumerate(all_existing_files):
    type_legend_items.append(Patch(facecolor=colors[i], label=legend_labels_map.get(file_num, f"类别{file_num}")))

# 合并所有图例项
all_legend_items = product_legend_items + type_legend_items

# 在底部显示合并图例，单独一行
if all_legend_items:
    legend = ax.legend(handles=all_legend_items,
                       loc='upper center', fontsize=30, ncol=4,
                       title_fontsize=30,
                       framealpha=0.4, bbox_to_anchor=(0.5, -0.15))

# 添加网格线
ax.grid(True, linestyle='--', alpha=0.3)
ax.set_axisbelow(True)

plt.tight_layout()
plt.show()

print(f"处理了 {len(years)} 年的数据")
print(f"MCD12 实际文件: {existing_mcd12_cols}")
print(f"MCD43 实际文件: {existing_mcd43_cols}")
print(f"年份范围: {min(years)} - {max(years)}")
print(f"实际处理的文件编号: {all_existing_files}")
print(f"各文件对应类型: {dict(zip(all_existing_files, [legend_labels_map.get(i, f'类别{i}') for i in all_existing_files]))}")
print("\n颜色说明:")
print("- 农田: 沙棕色 (#F4A460)")
print("- 森林: 森林绿 (#228B22)")
print("- 灌木: 黄绿色 (#9ACD32)")
print("- 草原: 酸 lime 绿 (#32CD32)")
print("- 裸地: 巧克力色 (#8B4513)")
