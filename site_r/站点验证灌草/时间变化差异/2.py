import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体显示中文
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 读取Excel文件
file_path = r'F:\站点\植物物候观测数据集20161202\\年.xlsx'
df = pd.read_excel(file_path)

# 过滤CLASS为‘草本’和‘灌木’的行
filtered_df = df[df['CLASS'].isin(['草本', '灌木'])]

# 定义需要处理的列
columns =  [
    'Budburst_Trend', 'Budburst_Change',
    'Flower_Trend', 'Flower_Change',
    'Fruit_Trend', 'Fruit_Change',
    'Coloration_Trend', 'Coloration_Change'
]

# 创建一个新的DataFrame来存储Trend和Change的数据
trend_change_data = filtered_df[columns].copy()

# 将Trend和Change分离到两个不同的列表中
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

# 计算所有点的Change值范围
all_changes = np.concatenate(grass_changes + shrub_changes)
norm = plt.Normalize(vmin=min(all_changes), vmax=max(all_changes))

# 计算所有线段的变化差值范围
all_changes_diff = []
for change_values in grass_changes + shrub_changes:
    diff_values = [change_values[j + 1] - change_values[j] for j in range(len(change_values) - 1)]
    all_changes_diff.extend(diff_values)

# 合并所有变化值和变化差值以确定最终的颜色范围
combined_values = np.concatenate((all_changes, all_changes_diff))
final_norm = plt.Normalize(vmin=min(combined_values), vmax=max(combined_values))

# 创建图形和轴
fig, ax = plt.subplots(figsize=(14, 8))

# 存储散点图对象以便添加到图例
scatter_handles = []

# 绘制草本数据
for i in range(len(grass_trends)):
    # 获取当前行的趋势值和变化值
    trend_values = grass_trends[i]
    change_values = grass_changes[i]

    # 计算每个线段的变化差值
    diff_values = [change_values[j + 1] - change_values[j] for j in range(len(change_values) - 1)]

    # 使用趋势值作为点的位置
    x = list(range(len(trend_values)))

    # 绘制点，颜色由Change值决定
    point_colors = cmap(final_norm(change_values))
    scatter = ax.scatter(x, trend_values, color=point_colors, s=100, marker='o', label='草本')

    # 添加到散点图对象列表
    if '草本' not in [handle.get_label() for handle in scatter_handles]:
        scatter_handles.append(scatter)

    # 绘制线段，颜色由下一个Change值减去当前Change值决定
    for j in range(len(x) - 1):
        line_color = cmap(final_norm(diff_values[j]))
        ax.plot([x[j], x[j + 1]], [trend_values[j], trend_values[j + 1]], color=line_color)

# 绘制灌木数据
for i in range(len(shrub_trends)):
    # 获取当前行的趋势值和变化值
    trend_values = shrub_trends[i]
    change_values = shrub_changes[i]

    # 计算每个线段的变化差值
    diff_values = [change_values[j + 1] - change_values[j] for j in range(len(change_values) - 1)]

    # 使用趋势值作为点的位置
    x = list(range(len(trend_values)))

    # 绘制点，颜色由Change值决定
    point_colors = cmap(final_norm(change_values))
    scatter = ax.scatter(x, trend_values, color=point_colors, s=100, marker='^', label='灌木')

    # 添加到散点图对象列表
    if '灌木' not in [handle.get_label() for handle in scatter_handles]:
        scatter_handles.append(scatter)

    # 绘制线段，颜色由下一个Change值减去当前Change值决定
    for j in range(len(x) - 1):
        line_color = cmap(final_norm(diff_values[j]))
        ax.plot([x[j], x[j + 1]], [trend_values[j], trend_values[j + 1]], color=line_color)

# 添加箭头
if len(grass_trends) > 0 and len(shrub_trends) > 0:
    for period in range(len(columns) // 2):
        grass_trend = grass_trends[0][period]
        shrub_trend = shrub_trends[0][period]
        grass_change = grass_changes[0][period]
        shrub_change = shrub_changes[0][period]

        difference = grass_change - shrub_change
        direction = (grass_trend - shrub_trend) * difference

        arrow_length = abs(difference) * 0.5  # 调整箭头长度
        y_position = (grass_trend + shrub_trend) / 2

        if direction < 0:
            ax.annotate('', xy=(period, y_position), xytext=(period, y_position + arrow_length),
                        arrowprops=dict(facecolor=cmap(final_norm(difference)), shrink=0.05, headwidth=5, headlength=5))
        elif direction > 0:
            ax.annotate('', xy=(period, y_position), xytext=(period, y_position - arrow_length),
                        arrowprops=dict(facecolor=cmap(final_norm(difference)), shrink=0.05, headwidth=5, headlength=5))

# 添加标签和标题
ax.set_xlabel('时期')
ax.set_ylabel('DOY')
ax.set_title('草本和灌木的趋势与变化可视化')
ax.set_xticks(list(range(len(columns) // 2)))
ax.set_xticklabels(columns[::2], rotation=45, ha='right')

# 添加颜色条（图例）
sm = plt.cm.ScalarMappable(cmap=cmap, norm=final_norm)
sm.set_array([])
colorbar = fig.colorbar(sm, ax=ax, label='Day Year$^{-1}$')


# 添加图例
legend_labels = [handle.get_label() for handle in scatter_handles]
unique_legend_labels = list(set(legend_labels))
handles = [handle for handle in scatter_handles if handle.get_label() in unique_legend_labels]

# 创建自定义图例
custom_lines = handles + [
    plt.Line2D([0], [0], color='w', marker='o', markersize=10, markerfacecolor='gray', label='草本'),
    plt.Line2D([0], [0], color='w', marker='^', markersize=10, markerfacecolor='gray', label='灌木'),

]

ax.legend(custom_lines, ['草本', '灌木', '物候差异拉开则箭头朝上，反之箭头朝下'], title='植物类型及箭头方向')

# 显示图形
plt.tight_layout()
plt.show()



