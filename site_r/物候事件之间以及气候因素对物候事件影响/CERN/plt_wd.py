import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import matplotlib.font_manager as fm

# 设置 Nature 推荐的字体
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10  # 默认字体大小
plt.rcParams['axes.unicode_minus'] = False  # 解决负号 '-' 显示问题

# 定义中英缩写映射字典
PHASE_ABBREVIATIONS = {
    'Budburst':'Budburst', 'Flower':'Flower', 'Fruit': 'Fruit', 'Coloration':'Coloration'
}

# 加载并预处理数据
def load_data(filepath):
    df = pd.read_csv(
        filepath,
        encoding='GBK',
        usecols=['phase_early', 'phase_late', 'partial_corr_ph',
                 'partial_corr_temp', 'partial_corr_precip']
    ).replace([np.inf, -np.inf], np.nan)
    return df.dropna()

# 数据聚合函数
def aggregate_data(df):
    grouped = df.groupby(['phase_early', 'phase_late'], as_index=False).agg({
        'partial_corr_ph': lambda x: np.nanmean(x),
        'partial_corr_temp': lambda x: np.nanmean(x),
        'partial_corr_precip': lambda x: np.nanmean(x)
    })
    return grouped

# 矩阵构建函数
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

            matrices['ph'][i, j] = row['partial_corr_ph']
            matrices['temp'][i, j] = row['partial_corr_temp']
            matrices['precip'][i, j] = row['partial_corr_precip']
        except KeyError:
            continue

    return matrices

# 可视化函数（Nature 格式）
def plot_nature_format(phases, matrices):
    # 设置图表尺寸（双栏宽度：18 cm，单栏：8.8 cm）
    fig_width = 18 / 2.54  # 18 cm to inches
    fig_height = fig_width * 0.8  # 横纵比 4:5
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=300)
    ax.set_aspect('equal')
    max_radius = 0.3  # 更小的半径以适应紧凑布局

    # 绘制网格
    for i in range(len(phases) + 1):
        ax.axhline(i - 0.5, color='lightgray', linestyle=':', linewidth=0.5)
        ax.axvline(i - 0.5, color='lightgray', linestyle=':', linewidth=0.5)

    # 绘制各效应
    for i in range(len(phases)):
        for j in range(len(phases)):
            if i >= j: continue

            x, y = i, j
            ph = matrices['ph'][i, j]
            temp = matrices['temp'][i, j]
            precip = matrices['precip'][i, j]

            # 物候效应（绿色）
            if not np.isnan(ph):
                linestyle = '-' if ph > 0 else '--'
                circle = Circle((x, y), radius=np.abs(ph) * max_radius,
                                edgecolor='seagreen', facecolor='none',
                                linewidth=1, linestyle=linestyle)
                ax.add_patch(circle)

            # 温度效应（橙色）
            if not np.isnan(temp):
                linestyle = '-' if temp > 0 else '--'
                circle = Circle((x, y), radius=np.abs(temp) * max_radius,
                                edgecolor='indianred', facecolor='none',
                                linewidth=1, linestyle=linestyle)
                ax.add_patch(circle)

            # 降水效应（蓝色）
            if not np.isnan(precip):
                linestyle = '-' if precip > 0 else '--'
                circle = Circle((x, y), radius=np.abs(precip) * max_radius,
                                edgecolor='steelblue', facecolor='none',
                                linewidth=1, linestyle=linestyle)
                ax.add_patch(circle)

    # 坐标轴设置
    ax.set(xticks=np.arange(len(phases)),
           yticks=np.arange(len(phases)),
           xlim=(-0.5, len(phases) - 0.5),
           ylim=(-0.5, len(phases) - 0.5))

    # 设置坐标轴标签（加粗+英文）
    x_labels = [PHASE_ABBREVIATIONS[p] for p in phases]
    y_labels = [PHASE_ABBREVIATIONS[p] for p in phases]
    ax.set_xticks(np.arange(len(phases)))
    ax.set_xticklabels(x_labels, fontdict={'size': 10, 'weight': 'bold'})
    ax.set_yticks(np.arange(len(phases)))
    ax.set_yticklabels(y_labels, fontdict={'size': 10, 'weight': 'bold'})

    # 旋转标签避免重叠
    plt.xticks(rotation=45, ha='right', rotation_mode='anchor')
    plt.yticks(rotation=0)

    # 添加主标题（符合 Nature 风格）
    ax.set_title('WD Phenology and Climate Effects Matrix', fontsize=12, fontweight='bold', pad=20)

    # 图例（Nature 风格：无边框）
    legend_elements = [
        plt.Line2D([0], [0], color='seagreen', lw=2, label='PHENOLOGY'),
        plt.Line2D([0], [0], color='indianred', lw=2, label='TEMPERATURE'),
        plt.Line2D([0], [0], color='steelblue', lw=2, label='PRECIPITATION')
    ]
    ax.legend(handles=legend_elements, loc='lower right', frameon=False, fontsize=9)

    # 移除边框
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    return fig

# 主流程
if __name__ == "__main__":
    # 数据加载与处理
    df = load_data('F:\站点\植物物候观测数据集20161202\CLIME\clim_carryover_effect_wd.csv')

    # 定义阶段顺序
    predefined_phases = [
        'Budburst', 'Flower', 'Fruit', 'Coloration'
    ]
    valid_phases = [p for p in predefined_phases if p in set(df['phase_early']).union(df['phase_late'])]

    # 数据聚合
    grouped_df = aggregate_data(df)

    # 构建矩阵
    matrices = build_matrix(valid_phases, grouped_df)

    # 可视化
    fig = plot_nature_format(valid_phases, matrices)
    fig.savefig('F:\站点\植物物候观测数据集20161202\CLIME\wd_phenology_matrix.png', dpi=300, bbox_inches='tight')
    plt.show()