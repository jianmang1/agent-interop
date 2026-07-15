import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import matplotlib.font_manager as fm
from matplotlib.lines import Line2D

# 设置中文字体
font_path = 'C:/Windows/Fonts/simhei.ttf'
zh_font = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = zh_font.get_name()
plt.rcParams['axes.unicode_minus'] = False


# 加载并预处理数据
def load_data(filepath):
    df = pd.read_csv(
        filepath,
        encoding='GBK',
        usecols=['phase_early', 'phase_late',
                 'doy_early_coeff', 'temp_coeff', 'precip_coeff',
                 'doy_temp_coeff', 'doy_precip_coeff',
                 'temp_precip_coeff', 'doy_temp_precip_coeff']
    ).replace([np.inf, -np.inf], np.nan)
    return df.dropna()


# 数据聚合函数
def aggregate_data(df):
    # 对相同 phase 组合取均值并取绝对值
    grouped = df.groupby(['phase_early', 'phase_late'], as_index=False).agg({
        'doy_early_coeff': lambda x: np.abs(np.nanmean(x)),
        'temp_coeff': lambda x: np.abs(np.nanmean(x)),
        'precip_coeff': lambda x: np.abs(np.nanmean(x)),
        'doy_temp_coeff': lambda x: np.abs(np.nanmean(x)),
        'doy_precip_coeff': lambda x: np.abs(np.nanmean(x)),
        'temp_precip_coeff': lambda x: np.abs(np.nanmean(x)),
        'doy_temp_precip_coeff': lambda x: np.abs(np.nanmean(x))
    })
    return grouped


# 归一化函数
def normalize_effects(effects):
    total_effect = sum(effects)
    if total_effect == 0:
        return [0] * len(effects)
    return [effect / total_effect for effect in effects]


# 可视化函数
def plot_normalized_pie_charts(phases, grouped_df):
    phase_idx = {phase: i for i, phase in enumerate(phases)}
    n = len(phases)

    fig, axes = plt.subplots(nrows=n, ncols=n, figsize=(24, 20), subplot_kw=dict(aspect='equal'))

    # 绘制网格
    for ax in axes.flat:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines[:].set_visible(False)
        ax.grid(which='both', color='lightgray', linestyle=':', linewidth=0.5)

    for i in range(len(phases)):
        for j in range(len(phases)):
            if i >= j:
                continue

            row = grouped_df[(grouped_df['phase_early'] == phases[i]) & (grouped_df['phase_late'] == phases[j])]
            if row.empty:
                continue

            ph = row.iloc[0]['doy_early_coeff']
            temp = row.iloc[0]['temp_coeff']
            precip = row.iloc[0]['precip_coeff']

            temp_precip = row.iloc[0]['temp_precip_coeff']

            effects = [ph, temp, precip, temp_precip]

            normalized_effects = normalize_effects(effects)

            labels = ['物候效应', '温度效应', '降水效应', '交互项效应']
            colors = ['#2ca02c', '#d62728', '#1f77b4', '#ff7f0e']

            wedges, texts, autotexts = axes[n-1-j, i].pie(normalized_effects, colors=colors,
                                                       autopct='%1.1f%%', startangle=90, textprops={'fontsize': 8})

    # 设置横坐标轴标签
    for ax, col in zip(axes[-1], phases):
        ax.set_xlabel(col, fontsize=10, ha='center')

    # 设置纵坐标轴标签
    for ax, row in zip(axes[:, 0], reversed(phases)):
        ax.set_ylabel(row, fontsize=10, rotation=0, va='center', ha='right')

    # 添加图例
    legend_elements = [
        Line2D([0], [0], color='#2ca02c', lw=4, label='物候效应'),
        Line2D([0], [0], color='#d62728', lw=4, label='温度效应'),
        Line2D([0], [0], color='#1f77b4', lw=4, label='降水效应'),
        Line2D([0], [0], color='#ff7f0e', lw=4, label='交互项效应')
    ]
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.2), title="图例", ncol=4)

    plt.tight_layout(rect=[0, 0.03, 1, 0.9])
    return fig


# 主流程
if __name__ == "__main__":
    # 数据加载与处理
    df = load_data('F:/站点/中国地面/clime/交互/clim_carryover_effect_ridge.csv')

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

    # 可视化
    fig = plot_normalized_pie_charts(valid_phases, grouped_df)
    fig.savefig('gl_aggregated_phenology_pie_charts_with_interactions.png', dpi=600, bbox_inches='tight')
    plt.show()