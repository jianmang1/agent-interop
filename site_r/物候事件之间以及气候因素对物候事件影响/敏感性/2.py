import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import matplotlib.font_manager as fm

# 设置 Nature 推荐的字体
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10  # 默认字体大小
plt.rcParams['axes.unicode_minus'] = False  # 解决负号 '-' 显示问题

# 中英缩写映射字典
PHASE_ABBREVIATIONS = {
    # 保持原字典内容不变
}

# 数据加载与预处理函数（保持原逻辑）
def load_data(filepath):
    df = pd.read_csv(
        filepath,
        encoding='GBK',
        usecols=['phase_early', 'phase_late', 'sensitivity_ph',
                 'sensitivity_temp', 'sensitivity_precip']
    ).replace([np.inf, -np.inf], np.nan)
    return df.dropna()

# 数据聚合函数（保持原逻辑）
def aggregate_data(df):
    grouped = df.groupby(['phase_early', 'phase_late'], as_index=False).agg({
        'sensitivity_ph': lambda x: np.nanmean(x),
        'sensitivity_temp': lambda x: np.nanmean(x),
        'sensitivity_precip': lambda x: np.nanmean(x)
    })
    return grouped

# 矩阵构建函数（保持原逻辑）
def build_matrix(phases, grouped_df):
    phase_idx = {phase: i for i, phase in enumerate(phases)}
    n = len(phases)

    matrices = {
        'ph': np.full((n, n), np.nan),
        'temp': np.full((n, n), np.nan),
        'precip': np.full((n, n), np.nan)
    }

    for _, row in grouped_df.iterrows():
        try:
            i = phase_idx[row['phase_early']]
            j = phase_idx[row['phase_late']]
            if i >= j: continue

            matrices['ph'][i, j] = row['sensitivity_ph']
            matrices['temp'][i, j] = row['sensitivity_temp']
            matrices['precip'][i, j] = row['sensitivity_precip']
        except KeyError:
            continue

    return matrices

# 可视化函数（核心修改：嵌入龙卷风图）
def plot_nature_format(phases, matrices):
    n = len(phases)
    inset_width = 0.2  # 每个龙卷风图的宽度
    fig_width = 18 / 2.54 + (inset_width * n) / 2.54  # 扩展图表宽度以容纳右侧的龙卷风图
    fig_height = fig_width * 0.8  # 横纵比 4:5
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=300)
    ax.set_aspect('equal')

    # 绘制网格
    for i in range(n + 1):
        ax.axhline(i - 0.5, color='lightgray', linestyle=':', linewidth=0.5)
        ax.axvline(i - 0.5, color='lightgray', linestyle=':', linewidth=0.5)

    # 主图的坐标轴范围扩展以容纳右侧的龙卷风图
    ax.set_xlim(-0.5, n - 0.5 + inset_width)
    ax.set_ylim(-0.5, n)

    # 设置坐标轴标签（加粗+英文）
    x_labels = [PHASE_ABBREVIATIONS[p] for p in phases]
    y_labels = [PHASE_ABBREVIATIONS[p] for p in phases]
    ax.set_xticks(np.arange(n))
    ax.set_xticklabels(x_labels, fontdict={'size': 10, 'weight': 'bold'})
    ax.set_yticks(np.arange(n))
    ax.set_yticklabels(y_labels, fontdict={'size': 10, 'weight': 'bold'})

    # 旋转标签避免重叠
    plt.xticks(rotation=45, ha='right', rotation_mode='anchor')
    plt.yticks(rotation=0)

    # 添加主标题
    ax.set_title('Sensitivity Matrix with Tornado Subplots', fontsize=12, fontweight='bold', pad=20)

    # 移除边框
    for spine in ax.spines.values():
        spine.set_visible(False)

    # 在每个单元格右侧添加龙卷风图
    for i in range(n):
        for j in range(n):
            if i >= j:
                continue

            # 单元格位置
            x, y = i, j
            ph = matrices['ph'][i, j]
            temp = matrices['temp'][i, j]
            precip = matrices['precip'][i, j]

            # 确定龙卷风图的位置和大小
            left = x + 0.5  # 单元格右侧边界
            bottom = y - 0.5  # 单元格下边界
            width = inset_width  # 龙卷风图宽度
            height = 1.0  # 单元格高度

            # 添加子图
            inset_ax = fig.add_axes([left, bottom, width, height])

            # 计算x轴范围（根据最大绝对值）
            values = [ph, temp, precip]
            valid_values = [v for v in values if not np.isnan(v)]
            if valid_values:
                max_val = max(abs(v) for v in valid_values)
                inset_ax.set_xlim(-max_val * 1.1, max_val * 1.1)
            else:
                continue  # 没有有效数据则跳过

            # 绘制三个水平条形图
            factors = [ph, temp, precip]
            labels = ['PH', 'Temp', 'Precip']
            colors = ['seagreen', 'indianred', 'steelblue']
            for idx, (val, label, color) in enumerate(zip(factors, labels, colors)):
                if not np.isnan(val):
                    if val > 0:
                        left_pos = 0
                        bar_width = val
                    else:
                        left_pos = val
                        bar_width = -val
                    inset_ax.barh(idx, bar_width, left=left_pos, height=0.4, color=color, edgecolor='black')
                    inset_ax.axvline(0, color='black', linestyle='--', linewidth=1)

            # 设置子图样式
            inset_ax.set_yticks([0, 1, 2])
            inset_ax.set_yticklabels(labels, fontsize=6)
            inset_ax.set_xticks([])
            for spine in inset_ax.spines.values():
                spine.set_visible(False)

    # 图例（Nature 风格）
    legend_elements = [
        plt.Line2D([0], [0], color='seagreen', lw=2, label='PHENOLOGY'),
        plt.Line2D([0], [0], color='indianred', lw=2, label='TEMPERATURE'),
        plt.Line2D([0], [0], color='steelblue', lw=2, label='PRECIPITATION')
    ]
    ax.legend(handles=legend_elements, loc='lower right', frameon=False, fontsize=9)

    plt.tight_layout()
    return fig

# 主流程
if __name__ == "__main__":
    df = load_data('F:/站点/中国地面/clime/clim_carryover_effect_wd2.csv')
    predefined_phases = [
        # 保持原定义不变
    ]
    valid_phases = [p for p in predefined_phases if p in set(df['phase_early']).union(df['phase_late'])]
    grouped_df = aggregate_data(df)
    matrices = build_matrix(valid_phases, grouped_df)
    fig = plot_nature_format(valid_phases, matrices)
    fig.savefig('wd_sensitivity_matrix_with_tornado.png', dpi=300, bbox_inches='tight')
    plt.show()