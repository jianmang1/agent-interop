import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from mpl_toolkits.axes_grid1 import make_axes_locatable

# 设置 Nature 推荐的字体
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10  # 默认字体大小
plt.rcParams['axes.unicode_minus'] = False  # 解决负号 '-' 显示问题

# 定义中英缩写映射字典
PHASE_ABBREVIATIONS = {
    '叶芽开始膨大期': 'BUD_S',
    '叶芽开放期': 'BUD_O',
    '花芽开始膨大期': 'FLB_S',
    '花芽开放期': 'FLB_O',
    '开始展叶期': 'LEA_S',
    '展叶盛期': 'LEA_F',
    '花序或花蕾出现期': 'INF_S',
    '开花始期': 'BLO_S',
    '开花盛期': 'BLO_F',
    '开花末期': 'BLO_E',
    '果实成熟期': 'FRU_M',
    '果实脱落开始期': 'FRU_S',
    '果实脱落末期': 'FRU_E',
    '叶开始变色期': 'COL_S',
    '叶全部变色期': 'COL_F',
    '开始落叶期': 'FAL_S',
    '落叶末期': 'FAL_E'
}

# 数据加载与处理函数保持不变
def load_data(filepath):
    df = pd.read_csv(
        filepath,
        encoding='GBK',
        usecols=['phase_early', 'phase_late', 'sensitivity_ph',
                 'sensitivity_temp', 'sensitivity_precip']
    ).replace([np.inf, -np.inf], np.nan)
    return df.dropna()


def aggregate_data(df):
    grouped = df.groupby(['phase_early', 'phase_late'], as_index=False).agg({
        'sensitivity_ph': lambda x: np.nanmean(x),
        'sensitivity_temp': lambda x: np.nanmean(x),
        'sensitivity_precip': lambda x: np.nanmean(x)
    })
    return grouped


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
            i = phase_idx[row['phase_early']]  # 早期阶段索引
            j = phase_idx[row['phase_late']]    # 晚期阶段索引
            if i >= j:
                continue

            # 交换行列位置：将 (i, j) 改为 (j, i)
            matrices['ph'][j, i] = row['sensitivity_ph']
            matrices['temp'][j, i] = row['sensitivity_temp']
            matrices['precip'][j, i] = row['sensitivity_precip']
        except KeyError:
            continue

    return matrices


def plot_nature_heatmap(phases, matrices):
    fig_width = 8.4
    fig_height = fig_width * 1.4
    fig, axes = plt.subplots(1, 3, figsize=(fig_width, fig_height), dpi=300,
                             gridspec_kw={'wspace': 0.3, 'hspace': 0.5})

    common_cmap = 'coolwarm'

    all_matrices = [matrices['ph'], matrices['temp'], matrices['precip']]
    abs_vals = [np.nanmax(np.abs(m)) for m in all_matrices]
    abs_max = max(abs_vals)
    vmin = -abs_max
    vmax = abs_max

    for ax, matrix, title in zip(
        axes,
        [matrices['ph'], matrices['temp'], matrices['precip']],
        ['PHENOLOGY', 'TEMPERATURE', 'PRECIPITATION']
    ):
        sns.heatmap(
            matrix,
            annot=False,
            cmap=common_cmap,
            center=0,
            linewidths=0.5,
            linecolor='lightgray',
            square=True,
            cbar=False,
            ax=ax,
            vmin=vmin,
            vmax=vmax
        )

        # 设置坐标轴标签
        x_labels = [PHASE_ABBREVIATIONS[p] for p in phases]
        y_labels = [PHASE_ABBREVIATIONS[p] for p in phases]
        ax.set_xticks(np.arange(len(phases)))
        ax.set_xticklabels(x_labels, rotation=45, ha='right', fontsize=10, fontweight='bold')
        ax.set_yticks(np.arange(len(phases)))
        ax.set_yticklabels(y_labels, rotation=0, fontsize=10, fontweight='bold')

        # 反转 Y 轴方向
        ax.invert_yaxis()

        # 设置标题
        ax.set_title(title, fontsize=12, fontweight='bold', pad=20)

        # 调整边框
        for _, spine in ax.spines.items():
            spine.set_visible(False)

    # 添加底部色条
    cax = fig.add_axes([0.1, 0.05, 0.8, 0.02])
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    sm = plt.cm.ScalarMappable(cmap=common_cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cax, orientation='horizontal')
    cbar.ax.set_xlabel("Sensitivity", fontsize=10, fontweight='bold')
    cbar.ax.tick_params(labelsize=10)

    plt.tight_layout(rect=[0, 0.15, 1, 1])
    return fig


# 主流程
if __name__ == "__main__":
    # 数据加载与处理
    df = load_data('F:/站点/中国地面/clime/clim_carryover_effect_gl2.csv')

    # 定义阶段顺序
    predefined_phases = [
        '叶芽开始膨大期', '叶芽开放期', '花芽开始膨大期',
        '花芽开放期', '开始展叶期', '展叶盛期',
        '花序或花蕾出现期', '开花始期', '开花盛期',
        '开花末期', '果实成熟期', '果实脱落开始期',
        '果实脱落末期', '叶开始变色期', '叶全部变色期',
        '开始落叶期', '落叶末期'
    ]
    valid_phases = [p for p in predefined_phases if p in set(df['phase_early']).union(df['phase_late'])]

    # 数据聚合
    grouped_df = aggregate_data(df)

    # 构建矩阵
    matrices = build_matrix(valid_phases, grouped_df)

    # 可视化
    fig = plot_nature_heatmap(valid_phases, matrices)
    fig.savefig('gl_sensitivity_heatmap_bottom_colorbar.png', dpi=300, bbox_inches='tight')
    plt.show()