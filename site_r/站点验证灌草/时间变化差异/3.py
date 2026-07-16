import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- 全局字体设置 ---
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体显示中文
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 读取Excel文件
file_path = r'F:\站点\中国地面\\phenology_stats_result.xlsx'

# 直接读取
df = pd.read_excel(file_path)

# 过滤CLASS为‘草本’和‘灌木’的行
filtered_df = df[df['CLASS'].isin(['草本', '灌木'])]

# 定义需要处理的列 (保持原有顺序)
columns = [
    '开始展叶期_Trend', '开始展叶期_Change',
    '展叶盛期_Trend', '展叶盛期_Change',
    '花序或花蕾出现期_Trend', '花序或花蕾出现期_Change',
    '开花始期_Trend', '开花始期_Change',
    '开花盛期_Trend', '开花盛期_Change',
    '开花末期_Trend', '开花末期_Change',
    '果实成熟期_Trend', '果实成熟期_Change',
    '果实脱落开始期_Trend', '果实脱落开始期_Change',
    '果实脱落末期_Trend', '果实脱落末期_Change',
    '叶开始变色期_Trend', '叶开始变色期_Change',
    '叶全部变色期_Trend', '叶全部变色期_Change'
]

# 检查列是否存在
available_columns = [col for col in columns if col in df.columns]
if len(available_columns) < 2:
    raise ValueError("Excel文件中未找到足够的指定列，请检查列名是否匹配。")

# 创建一个新的DataFrame来存储Trend和Change的数据
trend_change_data = filtered_df[available_columns].copy()

# 将Trend和Change分离
trends = trend_change_data.iloc[:, ::2].values.tolist()
changes = trend_change_data.iloc[:, 1::2].values.tolist()
classes = filtered_df['CLASS'].tolist()

# 提取草本和灌木的数据
grass_trends = [trends[i] for i in range(len(classes)) if classes[i] == '草本']
grass_changes = [changes[i] for i in range(len(classes)) if classes[i] == '草本']
shrub_trends = [trends[i] for i in range(len(classes)) if classes[i] == '灌木']
shrub_changes = [changes[i] for i in range(len(classes)) if classes[i] == '灌木']

# 设置颜色映射
cmap = plt.get_cmap('coolwarm')

# 计算归一化范围
all_changes_list = [c for c in grass_changes + shrub_changes if len(c) > 0]
if not all_changes_list:
    raise ValueError("没有有效的变化数据用于绘图。")

all_changes = np.concatenate(all_changes_list)
norm_min = min(all_changes)
norm_max = max(all_changes)

# 计算差值范围
all_changes_diff = []
for change_values in all_changes_list:
    if len(change_values) > 1:
        diff_values = [change_values[j + 1] - change_values[j] for j in range(len(change_values) - 1)]
        all_changes_diff.extend(diff_values)

if all_changes_diff:
    combined_values = np.concatenate((all_changes, all_changes_diff))
    final_norm = plt.Normalize(vmin=min(combined_values), vmax=max(combined_values))
else:
    final_norm = plt.Normalize(vmin=norm_min, vmax=norm_max)

# 创建图形和轴
fig, ax = plt.subplots(figsize=(14, 8))

scatter_handles = []

# 绘制草本数据
for i in range(len(grass_trends)):
    trend_values = grass_trends[i]
    change_values = grass_changes[i]
    if len(trend_values) == 0: continue

    diff_values = [change_values[j + 1] - change_values[j] for j in range(len(change_values) - 1)] if len(
        change_values) > 1 else []
    x = list(range(len(trend_values)))

    point_colors = cmap(final_norm(change_values))
    scatter = ax.scatter(x, trend_values, color=point_colors, s=100, marker='o', label='草本', edgecolors='black',
                         linewidth=0.5)

    if '草本' not in [handle.get_label() for handle in scatter_handles]:
        scatter_handles.append(scatter)

    for j in range(len(x) - 1):
        if j < len(diff_values):
            line_color = cmap(final_norm(diff_values[j]))
            ax.plot([x[j], x[j + 1]], [trend_values[j], trend_values[j + 1]], color=line_color, linewidth=2)

# 绘制灌木数据
for i in range(len(shrub_trends)):
    trend_values = shrub_trends[i]
    change_values = shrub_changes[i]
    if len(trend_values) == 0: continue

    diff_values = [change_values[j + 1] - change_values[j] for j in range(len(change_values) - 1)] if len(
        change_values) > 1 else []
    x = list(range(len(trend_values)))

    point_colors = cmap(final_norm(change_values))
    scatter = ax.scatter(x, trend_values, color=point_colors, s=100, marker='^', label='灌木', edgecolors='black',
                         linewidth=0.5)

    if '灌木' not in [handle.get_label() for handle in scatter_handles]:
        scatter_handles.append(scatter)

    for j in range(len(x) - 1):
        if j < len(diff_values):
            line_color = cmap(final_norm(diff_values[j]))
            ax.plot([x[j], x[j + 1]], [trend_values[j], trend_values[j + 1]], color=line_color, linewidth=2)

# 添加箭头
if len(grass_trends) > 0 and len(shrub_trends) > 0:
    g_trend = grass_trends[0]
    s_trend = shrub_trends[0]
    g_change = grass_changes[0]
    s_change = shrub_changes[0]

    min_len = min(len(g_trend), len(s_trend), len(g_change), len(s_change))

    for period in range(min_len):
        grass_trend_val = g_trend[period]
        shrub_trend_val = s_trend[period]
        grass_change_val = g_change[period]
        shrub_change_val = s_change[period]

        difference = grass_change_val - shrub_change_val
        direction = (grass_trend_val - shrub_trend_val) * difference

        arrow_length = abs(difference) * 3
        if arrow_length < 0.5: arrow_length = 0.5

        y_position = (grass_trend_val + shrub_trend_val) / 2
        color_arrow = cmap(final_norm(difference))

        if direction < 0:
            ax.annotate('', xy=(period, y_position), xytext=(period, y_position + arrow_length),
                        arrowprops=dict(facecolor=color_arrow, shrink=0.05, headwidth=8, headlength=5, linewidth=2))
        elif direction > 0:
            ax.annotate('', xy=(period, y_position), xytext=(period, y_position - arrow_length),
                        arrowprops=dict(facecolor=color_arrow, shrink=0.05, headwidth=8, headlength=5, linewidth=2))

# 设置标题和轴标签
ax.set_xlabel('物候时期', fontsize=20, fontweight='bold')
ax.set_ylabel('时间 DOY', fontsize=20, fontweight='bold')

# 增大坐标轴刻度
ax.tick_params(axis='both', which='major', labelsize=20, width=2, length=8)

# --- 核心修改：自定义X轴标签 ---
# 按照你要求的顺序和名称定义标签
# 注意：标签数量必须与 available_columns 中 Trend 列的数量一致
custom_x_labels = [
    '展叶始期',  # 对应 开始展叶期_Trend
    '展叶盛期',  # 对应 展叶盛期_Trend
    '现蕾期',  # 对应 花序或花蕾出现期_Trend (根据你的要求改为现蕾期)
    '开花始期',  # 对应 开花始期_Trend
    '开花盛期',  # 对应 开花盛期_Trend
    '开花末期',  # 对应 开花末期_Trend
    '果实成熟期',  # 对应 果实成熟期_Trend
    '果实脱落始期',  # 对应 果实脱落开始期_Trend (根据你的要求改为果实脱落始期)
    '果实脱落末期',  # 对应 果实脱落末期_Trend
    '叶变色始期',  # 对应 叶开始变色期_Trend (根据你的要求改为叶变色始期)
    '叶变色末期'  # 对应 叶全部变色期_Trend (根据你的要求改为叶变色末期)
]

# 获取实际存在的Trend列数量
num_trends = len(available_columns) // 2

# 安全检查：如果数据列数量和自定义标签数量不匹配，进行截断或报错
if len(custom_x_labels) != num_trends:
    print(f"警告：数据列包含 {num_trends} 个物候期，但提供了 {len(custom_x_labels)} 个标签。将自动截断或填充。")
    # 取两者中较小的长度进行绘图，避免索引错误
    plot_count = min(len(custom_x_labels), num_trends)
    final_labels = custom_x_labels[:plot_count]
    tick_positions = list(range(plot_count))
else:
    final_labels = custom_x_labels
    tick_positions = list(range(num_trends))

ax.set_xticks(tick_positions)
ax.set_xticklabels(final_labels, rotation=45, ha='right', fontsize=24)

# 颜色条设置
sm = plt.cm.ScalarMappable(cmap=cmap, norm=final_norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.8, aspect=20, pad=0.02)
cbar.set_label('')
cbar_ax = cbar.ax
cbar_ax.text(0.5, -0.15, '天/年', transform=cbar_ax.transAxes,
             ha='center', va='top', fontsize=20, fontweight='bold')
cbar_ax.tick_params(labelsize=20)

# 图例
legend_handles = [
    plt.Line2D([0], [0], marker='o', color='#B3D9FF', linestyle='None', markersize=12, label='草本'),
    plt.Line2D([0], [0], marker='^', color='lightgray', linestyle='None', markersize=12, label='灌木'),
    plt.Line2D([0], [0], color='gray', linewidth=2, label='连线 (颜色代表变化速率)'),
    plt.Line2D([0], [0], marker='>', color='gray',lw=0, markersize=10, label='箭头 (方向代表差异变化)')]

ax.legend(handles=legend_handles, fontsize=24, title_fontsize=24, loc='best', frameon=True)

plt.tight_layout()
plt.subplots_adjust(bottom=0.15)
plt.show()