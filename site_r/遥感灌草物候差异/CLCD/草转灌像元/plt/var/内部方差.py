import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

# 读取数据
file_path = r'D:\MODIS43A4_2024\草转灌当年像元(绝对SCR).csv'
df = pd.read_csv(file_path)

# 定义物候指标列表
phenology_metrics = ['SOS', 'POS', 'EOS', 'GUP', 'GDP']

# 创建子图布局
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
axes = axes.flatten()
plt.tight_layout(pad=4)

# 修正：按 SCR 分组，计算 SOS_3_mean - SOS_4_mean 的方差（排除分组列）
sos_diff_grouped = df.groupby('scr', group_keys=False).apply(
    lambda group: (group['SOS_3_mean'] - group['SOS_4_mean']).var()
).reset_index(name='sos_diff_var')

# 分析每个物候指标
for i, metric in enumerate(phenology_metrics):
    # 构造字段名
    col_3_mean = f'{metric}_3_var'
    col_4_mean = f'{metric}_4_var'
    col_si_current = 'si_current'

    # 过滤无效值：0 或 NaN
    valid_mask = (
        (df[col_3_mean] != 0) & (~df[col_3_mean].isna()) &
        (df[col_4_mean] != 0) & (~df[col_4_mean].isna()) &
        (df[col_si_current] != 0) & (~df[col_si_current].isna())
    )

    valid_df = df[valid_mask].copy()
    if valid_df.empty:
        print(f"无有效数据: {metric}")
        continue

    # 计算物候差值的绝对值
    valid_df[f'{metric}_diff'] = valid_df[col_3_mean] - valid_df[col_4_mean]

    # 提取 SCR 和物候差值
    x = valid_df['scr']
    if metric == 'SOS':
        # 使用预处理好的 sos_diff_grouped 数据（已按 SCR 分组）
        merged_df = pd.merge(valid_df[['scr']], sos_diff_grouped, on='scr', how='left')
        y = merged_df['sos_diff_var']
    else:
        y = valid_df[f'{metric}_diff']

    # 修正：过滤掉 NaN 值后再计算相关性
    valid_corr_mask = (~x.isna()) & (~y.isna())
    x_clean = x[valid_corr_mask]
    y_clean = y[valid_corr_mask]

    if len(x_clean) < 2:
        print(f"无法计算相关性（样本不足）: {metric}")
        corr, p_value = float('nan'), float('nan')
    else:
        corr, p_value = pearsonr(x_clean, y_clean)

    corr_text = f'R = {corr:.2f} p = {p_value:.3f}'

    # 绘制散点图
    ax = axes[i]
    if metric == 'SOS':
        # 每个 SCR 对应一个方差值（只画一个点）
        sns.scatterplot(x=x_clean, y=y_clean, alpha=0.6, color='blue', ax=ax)
        ax.set_ylabel("SOS Diff Variance")
    else:
        # 其他物候指标保持原来的散点图逻辑
        sns.scatterplot(x=x_clean, y=y_clean, alpha=0.6, color='blue', ax=ax)
        sns.regplot(x=x_clean, y=y_clean, scatter=False, color='red', ax=ax)
        ax.set_ylabel(f"{metric} Diff")

    # 添加标题和注释
    ax.set_title(f"{metric} {corr_text}")
    ax.set_xlabel("Scr (Invasion Rate %)")

    # 显示显著性（p < 0.05）
    if not pd.isna(p_value) and p_value < 0.05:
        ax.text(0.05, 0.95, "*", fontsize=16, ha='left', va='top', transform=ax.transAxes)

# 隐藏最后一个空图
if len(phenology_metrics) < len(axes):
    axes[-1].axis('off')

# 保存图像
output_plot_path = r'D:\GEE(PYTHON)\site_r\遥感灌草物候差异\CLCD\草转灌像元\plt\var\phenology_scr_correlation_sos_grouped_var.png'
plt.savefig(output_plot_path, dpi=300, bbox_inches='tight')
plt.show()