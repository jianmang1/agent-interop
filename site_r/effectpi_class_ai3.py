import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import rcParams

# 设置字体为Times New Roman
rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
rcParams['axes.unicode_minus'] = False  # 正确显示负号

# 设置文件路径
mcd12_path = r'D:\MOD12Q2\ratio\mcd12'
mcd43_path = r'D:\MOD12Q2\ratio\mcd43'

# 初始化数据框列表
dataframes_mcd12 = []
dataframes_mcd43 = []

# 读取mcd12下的文件
for i in range(1, 5):
    file_path = os.path.join(mcd12_path, f'pixel_ratio_results_{i}_masked_tibet.xlsx')
    df = pd.read_excel(file_path)
    df['Source'] = 'MCD12'
    df['File'] = i
    dataframes_mcd12.append(df)

# 读取mcd43下的文件
for i in range(1, 5):
    file_path = os.path.join(mcd43_path, f'pixel_ratio_results_{i}_masked_tibet.xlsx')
    df = pd.read_excel(file_path)
    df['Source'] = 'MCD43'
    df['File'] = i
    dataframes_mcd43.append(df)

# 合并所有数据框
combined_df_mcd12 = pd.concat(dataframes_mcd12, ignore_index=True)
combined_df_mcd43 = pd.concat(dataframes_mcd43, ignore_index=True)

# 按Year, Source, File分组，并计算Ratio的总和
grouped_df_mcd12 = combined_df_mcd12.pivot_table(index='Year', columns=['Source', 'File'], values='Ratio', aggfunc='sum').fillna(0)
grouped_df_mcd43 = combined_df_mcd43.pivot_table(index='Year', columns=['Source', 'File'], values='Ratio', aggfunc='sum').fillna(0)

# 重置索引以便更容易处理
grouped_df_mcd12 = grouped_df_mcd12.reset_index()
grouped_df_mcd43 = grouped_df_mcd43.reset_index()

# 合并两个数据框
merged_df = pd.merge(grouped_df_mcd12, grouped_df_mcd43, on='Year')

# 提取Ratio列
try:
    ratios_mcd12 = merged_df[[('MCD12', i) for i in range(1, 5)]].values.T
except KeyError as e:
    print(f"KeyError: {e}")
    print("Columns in merged_df:", merged_df.columns.tolist())

try:
    ratios_mcd43 = merged_df[[('MCD43', i) for i in range(1, 5)]].values.T
except KeyError as e:
    print(f"KeyError: {e}")
    print("Columns in merged_df:", merged_df.columns.tolist())

years = merged_df['Year']
width = 0.35  # 柱子的宽度
x = range(len(years))

# 定义统一颜色列表（每个文件使用相同颜色）
colors = ['#FF6666', '#FFCC66', '#99CC99', '#77AADD']

# 新的图例标签
legend_labels = [
    'Hyper-arid (AI < 0.05)',
    'Arid (0.05 ≤ AI < 0.2)',
    'Semi-arid (0.2 ≤ AI < 0.5)',
    'Subhumid (0.5 ≤ AI < 0.65)'
]

fig, ax = plt.subplots(figsize=(16, 10))

bottom_mcd12 = [0] * len(years)
bottom_mcd43 = [0] * len(years)

# 绘制MCD12堆叠柱状图（带黑色边框）
for i in range(4):
    ax.bar(x, ratios_mcd12[i], width, bottom=bottom_mcd12,
           color=colors[i], edgecolor='black', linewidth=2)
    bottom_mcd12 = [bottom_mcd12[j] + ratios_mcd12[i][j] for j in range(len(years))]

# 绘制MCD43堆叠柱状图（无边框）
for i in range(4):
    ax.bar([pos + width for pos in x], ratios_mcd43[i], width, bottom=bottom_mcd43,
           color=colors[i], edgecolor='white', linewidth=0.5)
    bottom_mcd43 = [bottom_mcd43[j] + ratios_mcd43[i][j] for j in range(len(years))]

# 图表美化
ax.set_xlabel('Year', fontsize=30)
ax.set_ylabel('Total Ratio', fontsize=30)
ax.set_xticks([pos + width / 2 for pos in x])
ax.set_xticklabels(years, fontsize=30, rotation=45, ha='right')
ax.tick_params(axis='y', labelsize=30)

# 创建组合图例 - 包含数据产品类型和干旱等级
from matplotlib.patches import Patch
# 数据产品类型图例项
product_legend_items = [
    Patch(facecolor='lightgray', edgecolor='black', linewidth=2, label='MCD12Q2'),
    Patch(facecolor='lightgray', edgecolor='white', linewidth=0.5, label='MCD43A4')
]

# 干旱等级图例项
aridity_legend_items = [Patch(facecolor=colors[i], label=legend_labels[i]) for i in range(4)]

# 合并所有图例项
all_legend_items = product_legend_items + aridity_legend_items

# 在底部显示合并图例，单独一行
legend = ax.legend(handles=all_legend_items,
                   loc='upper center', fontsize=30, ncol=3,
                  title_fontsize=30,
                   framealpha=0.4, bbox_to_anchor=(0.5, -0.15))

# 添加网格线
ax.grid(True, linestyle='--', alpha=0.3)
ax.set_axisbelow(True)

plt.tight_layout()
plt.show()