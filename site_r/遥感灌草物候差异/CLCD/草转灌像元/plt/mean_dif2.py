import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, ttest_ind
from scipy.stats import t as t_dist
import numpy as np


def cohens_d(x, y):
    """计算Cohen's d效应量"""
    nx = len(x)
    ny = len(y)
    dof = nx + ny - 2
    pooled_std = np.sqrt(((nx - 1) * np.var(x, ddof=1) + (ny - 1) * np.var(y, ddof=1)) / dof)
    return (np.mean(x) - np.mean(y)) / pooled_std


def calculate_confidence_interval(x, confidence=0.95):
    """计算均值的置信区间"""
    n = len(x)
    if n < 2:
        return np.mean(x), np.mean(x)
    mean = np.mean(x)
    se = np.std(x, ddof=1) / np.sqrt(n)
    t_val = t_dist.ppf((1 + confidence) / 2, df=n - 1)
    margin_error = t_val * se
    return mean - margin_error, mean + margin_error


def remove_outliers_iqr(series):
    """使用IQR方法移除单个Series中的离群点"""
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    # 返回布尔索引，用于过滤离群点
    return (series >= lower_bound) & (series <= upper_bound)


# 读取数据
file_path = r'D:\MODIS43A4_2024\all_output2.csv'
df = pd.read_csv(file_path)

phenology_metrics = ['sos', 'pos', 'eos']

# 创建子图布局 (2行3列)
fig, axes = plt.subplots(2, 3, figsize=(18, 16))
plt.tight_layout(pad=4)

for i, metric in enumerate(phenology_metrics):
    col_3_var = f'{metric}_3_var'
    col_4_var = f'{metric}_4_var'
    col_si_current = 'si_current'

    # 过滤无效值：0 或 NaN
    initial_valid_mask = (
            (df[col_3_var] != 0) & (~df[col_3_var].isna()) &
            (df[col_4_var] != 0) & (~df[col_4_var].isna()) &
            (df[col_si_current] != 0) & (~df[col_si_current].isna())
    )
    initial_valid_df = df[initial_valid_mask].copy()
    if initial_valid_df.empty:
        print(f"无有效数据: {metric}")
        continue

    # ---【新增】过滤离群点---
    mask_3_no_outliers = remove_outliers_iqr(initial_valid_df[col_3_var])
    mask_4_no_outliers = remove_outliers_iqr(initial_valid_df[col_4_var])

    # 结合初始有效值和离群点过滤
    final_valid_mask = initial_valid_df.index.isin(initial_valid_df[mask_3_no_outliers & mask_4_no_outliers].index)
    valid_df = initial_valid_df[mask_3_no_outliers & mask_4_no_outliers].copy()
    # print(f"过滤后有效数据量 ({metric}): {len(valid_df)}") # 可选：打印过滤后数量

    if valid_df.empty:
        print(f"过滤离群点后无有效数据: {metric}")
        continue

    # 计算物候差值的绝对值 (如果需要用于第一行散点图)
    valid_df[f'{metric}_diff'] = valid_df[col_3_var] - valid_df[col_4_var]

    # 提取 SCR 和物候差值 (如果需要用于第一行散点图)
    # 假设 scr 列存在且已过滤
    if 'scr' in valid_df.columns and not valid_df['scr'].empty:
        y = valid_df[f'{metric}_diff']
        x = valid_df['scr']

        # 计算皮尔逊相关系数
        corr, p_value = pearsonr(x, y)
        corr_text = f'R = {corr:.2f} p = {p_value:.7f}'

        # 绘制散点图（第一行）
        ax1 = axes[0, i]
        sns.scatterplot(x=x, y=y, alpha=0.6, color='blue', ax=ax1)
        sns.regplot(x=x, y=y, scatter=False, color='red', ax=ax1)

        # 添加标题和注释
        ax1.set_title(f"{metric} {corr_text}")
        ax1.set_xlabel(f"SCR (Invasion Rate %)")
        ax1.set_ylabel(f"{metric} Difference (3_var - 4_var)")

        # 显示显著性（p < 0.05）
        if p_value < 0.05:
            ax1.text(0.05, 0.95, "*", fontsize=16, ha='left', va='top', transform=ax1.transAxes)
    else:
        print(f"列 'scr' 不存在或在过滤后为空: {metric}")
        ax1 = axes[0, i]
        ax1.set_title(f"{metric} (No 'scr' data)")

    # --- 第二行：对比分析3和4是否存在显著差异 (使用过滤后的数据) ---
    ax2 = axes[1, i]

    # 准备3类和4类的数据 (已过滤)
    data_3 = valid_df[col_3_var].dropna()
    data_4 = valid_df[col_4_var].dropna()

    # 如果过滤后任一数据集为空，则跳过此部分
    if data_3.empty or data_4.empty:
        print(f"过滤离群点后，类别3或4数据为空: {metric}")
        ax2.text(0.5, 0.5, f"No valid data after outlier removal",
                 horizontalalignment='center', verticalalignment='center',
                 transform=ax2.transAxes, fontsize=12)
        ax2.set_title(f"{metric} Comparison (Skipped)")
        continue

    # 执行独立样本t检验 (使用过滤后的数据)
    t_stat, t_p_value = ttest_ind(data_3, data_4, equal_var=False)

    # 计算效应量 (使用过滤后的数据)
    effect_size = cohens_d(data_3, data_4)

    # 计算置信区间 (使用过滤后的数据)
    ci_3_lower, ci_3_upper = calculate_confidence_interval(data_3)
    ci_4_lower, ci_4_upper = calculate_confidence_interval(data_4)

    # 准备数据
    box_data = [data_3.values, data_4.values]
    x_tick_labels = ['VPD', 'SM']  # 或者 'Class 3', 'Class 4'
    colors = ['#E89B76', '#8FC1E3']

    # 绘制箱线图
    bp = ax2.boxplot(
        box_data,
        tick_labels=x_tick_labels,
        patch_artist=True,
        widths=0.5,
        showmeans=True,
        meanprops={
            "marker": "o",
            "markerfacecolor": "white",
            "markeredgecolor": "black",
            "markersize": 8,
            "linestyle": "none"
        },
        medianprops=dict(color="black", linewidth=2)
    )

    # 设置箱体颜色
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_edgecolor('black')
        patch.set_linewidth(1.5)

    # 设置须线颜色
    for whisker in bp['whiskers']:
        whisker.set_color('black')
        whisker.set_linewidth(1.5)
    for cap in bp['caps']:
        cap.set_color('black')
        cap.set_linewidth(1.5)

    # 1. 标注均值数值 (使用过滤后的数据计算的均值)
    mean_3 = np.mean(data_3)
    mean_4 = np.mean(data_4)

    # 获取箱体底部 Y 坐标 (使用过滤后的数据绘制的箱线图)
    bottom_y_3 = bp['whiskers'][0].get_ydata()[0]  # 第一个箱体的下须线末端
    bottom_y_4 = bp['whiskers'][2].get_ydata()[0]  # 第二个箱体的下须线末端

    # 动态计算偏移量
    y_range = ax2.get_ylim()[1] - ax2.get_ylim()[0]
    offset = y_range * 0.05

    ax2.text(1, bottom_y_3 - offset, f'Mean: {mean_3:.3f}',
             horizontalalignment='center', verticalalignment='top',
             color=colors[0], fontsize=10, fontweight='bold')

    ax2.text(2, bottom_y_4 - offset, f'Mean: {mean_4:.3f}',
             horizontalalignment='center', verticalalignment='top',
             color=colors[1], fontsize=10, fontweight='bold')

    # 2. 添加显著性标记 (使用过滤后的数据计算的 p 值)
    max_whisker = max([w.get_ydata()[1] for w in bp['whiskers']])  # 上须线的最大值
    line_height = max_whisker + y_range * 0.05

    # 画横线
    ax2.plot([1, 2], [line_height, line_height], color='black', linewidth=1.5)
    # 画两端竖线
    vert_len = y_range * 0.03
    ax2.plot([1, 1], [line_height, line_height - vert_len], color='black', linewidth=1.5)
    ax2.plot([2, 2], [line_height, line_height - vert_len], color='black', linewidth=1.5)

    # 画星号
    sig_text = ""
    if t_p_value < 0.001:
        sig_text = "***"
    elif t_p_value < 0.01:
        sig_text = "**"
    elif t_p_value < 0.05:
        sig_text = "*"

    if sig_text:
        ax2.text(1.5, line_height + y_range * 0.01,
                 sig_text, horizontalalignment='center', verticalalignment='bottom',
                 fontsize=14, fontweight='bold')

    ax2.set_title(f"{metric} Comparison", fontsize=14)
    ax2.set_ylabel("Value", fontsize=12)

    # 美化边框
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

# 保存图像
output_plot_path = r'D:\MODIS43A4_2024\phenology_scr_correlation_boxplot_style_no_outliers.png'
plt.savefig(output_plot_path, dpi=300, bbox_inches='tight')
plt.show()

# 打印统计摘要 (使用过滤后的数据)
print("\n统计摘要 (已移除离群点):")
for metric in phenology_metrics:
    col_3_var = f'{metric}_3_var'
    col_4_var = f'{metric}_4_var'
    col_si_current = 'si_current'

    # 重复过滤步骤
    initial_valid_mask = (
            (df[col_3_var] != 0) & (~df[col_3_var].isna()) &
            (df[col_4_var] != 0) & (~df[col_4_var].isna()) &
            (df[col_si_current] != 0) & (~df[col_si_current].isna())
    )
    initial_valid_df = df[initial_valid_mask].copy()

    if initial_valid_df.empty:
        print(f"\n{metric}: 初始数据为空")
        continue

    mask_3_no_outliers = remove_outliers_iqr(initial_valid_df[col_3_var])
    mask_4_no_outliers = remove_outliers_iqr(initial_valid_df[col_4_var])

    valid_df = initial_valid_df[mask_3_no_outliers & mask_4_no_outliers].copy()

    if valid_df.empty:
        print(f"\n{metric}: 过滤离群点后数据为空")
        continue

    data_3 = valid_df[col_3_var].dropna()
    data_4 = valid_df[col_4_var].dropna()

    if data_3.empty or data_4.empty:
        print(f"\n{metric}: 某一类别过滤后为空")
        continue

    t_stat, t_p_value = ttest_ind(data_3, data_4, equal_var=False)
    effect_size = cohens_d(data_3, data_4)

    print(f"\n{metric} 类别间差异检验 (已移除离群点):")
    print(f"  Class 3: n={len(data_3)}, mean={np.mean(data_3):.2f}, std={np.std(data_3):.2f}")
    print(f"  Class 4: n={len(data_4)}, mean={np.mean(data_4):.2f}, std={np.std(data_4):.2f}")
    print(f"  t-test p-value: {t_p_value:.6e}")
    print(f"  Cohen's d (Effect Size): {effect_size:.4f}")

    if abs(effect_size) >= 0.8:
        es_interpret = "Large effect"
    elif abs(effect_size) >= 0.5:
        es_interpret = "Medium effect"
    elif abs(effect_size) >= 0.2:
        es_interpret = "Small effect"
    else:
        es_interpret = "Negligible effect"

    print(f"  Effect Size Interpretation: {es_interpret}")

    if t_p_value < 0.001 and abs(effect_size) >= 0.2:
        print(f"  统计结论: Highly significant with meaningful difference")
    elif t_p_value < 0.05 and abs(effect_size) >= 0.2:
        print(f"  统计结论: Significant with meaningful difference")
    elif t_p_value < 0.05:
        print(f"  统计结论: Statistically significant but small effect size")
    else:
        print(f"  统计结论: Not statistically significant")