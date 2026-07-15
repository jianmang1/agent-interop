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

# 分析每个物候指标
for i, metric in enumerate(phenology_metrics):
    # 构造字段名
    col_3_mean = f'{metric}_3_mean'
    col_4_mean = f'{metric}_4_mean'
    col_si_current = 'si_current'
    col_si_prev = 'si_prev'

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
    valid_df[f'{metric}_diff'] = abs(valid_df[col_3_mean] - valid_df[col_4_mean])

    # 提取 SCR 和物候差值
    x = valid_df['scr']  # 新增：SCR 作为 X 轴
    y = valid_df[f'{metric}_diff']  # 新增：物候差值作为 Y 轴

    # 计算皮尔逊相关系数
    corr, p_value = pearsonr(x, y)
    corr_text = f'R = {corr:.2f} p = {p_value:.3f}'

    # 绘制散点图
    ax = axes[i]
    sns.scatterplot(x=x, y=y, alpha=0.6, color='blue', ax=ax)
    sns.regplot(x=x, y=y, scatter=False, color='red', ax=ax)

    # 添加标题和注释
    ax.set_title(f"{metric} {corr_text}")
    ax.set_xlabel("Scr (Invasion Rate %)")  # 原来是 x 轴标签
    ax.set_ylabel(f"{metric} Diff")  # 原来是 y 轴标签

    # 显示显著性（p < 0.05）
    if p_value < 0.05:
        ax.text(0.05, 0.95, "*", fontsize=16, ha='left', va='top', transform=ax.transAxes)

# 隐藏最后一个空图
if len(phenology_metrics) < len(axes):
    axes[-1].axis('off')

# 保存图像
output_plot_path = r'D:\MODIS43A4_2024\phenology_scr_correlation_abs.png'
plt.savefig(output_plot_path, dpi=300, bbox_inches='tight')
plt.show()