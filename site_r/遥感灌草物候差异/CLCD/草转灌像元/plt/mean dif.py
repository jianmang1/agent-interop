import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import ttest_ind

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 支持中文显示
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号


def cohens_d(x, y):
    """计算Cohen's d效应量"""
    nx = len(x)
    ny = len(y)
    dof = nx + ny - 2
    pooled_std = np.sqrt(((nx - 1) * np.var(x, ddof=1) + (ny - 1) * np.var(y, ddof=1)) / dof)
    return (np.mean(x) - np.mean(y)) / pooled_std


def calculate_confidence_interval(x, confidence=0.95):
    """计算均值的置信区间"""
    from scipy.stats import t as t_dist
    n = len(x)
    if n < 2:
        return np.mean(x), np.mean(x)
    mean = np.mean(x)
    se = np.std(x, ddof=1) / np.sqrt(n)
    t_val = t_dist.ppf((1 + confidence) / 2, df=n - 1)
    margin_error = t_val * se
    return mean - margin_error, mean + margin_error


# 读取数据
file_path = r'D:\MODIS43A4_2024\all_output.csv'
df = pd.read_csv(file_path)

# 定义物候指标列表和对应的Y轴范围
phenology_metrics = ['sos', 'pos', 'eos']
y_axis_ranges = {
    'sos': (70, 160),
    'pos': (170, 250),
    'eos': (220, 280)
}

# 创建子图布局 (1行3列，仅箱形图)
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
plt.tight_layout(pad=4)

# 分析每个物候指标
for i, metric in enumerate(phenology_metrics):
    col_3_mean = f'{metric}_3_mean'
    col_4_mean = f'{metric}_4_mean'
    col_si_current = 'si_current'

    # 过滤无效值：0 或 NaN
    initial_valid_mask = (
            (df[col_3_mean] != 0) & (~df[col_3_mean].isna()) &
            (df[col_4_mean] != 0) & (~df[col_4_mean].isna()) &
            (df[col_si_current] != 0) & (~df[col_si_current].isna())
    )
    valid_df = df[initial_valid_mask].copy()

    if valid_df.empty:
        print(f"无有效数据: {metric}")
        continue

    # 准备3类和4类的数据 (使用原始数据)
    data_3 = valid_df[col_3_mean].dropna()
    data_4 = valid_df[col_4_mean].dropna()

    # 如果任一数据集为空，则跳过此部分
    if data_3.empty or data_4.empty:
        print(f"过滤后，类别3或4数据为空: {metric}")
        axes[i].text(0.5, 0.5, f"无有效数据",
                     horizontalalignment='center', verticalalignment='center',
                     transform=axes[i].transAxes, fontsize=20)
        axes[i].set_title(f"{metric.upper()} 对比", fontsize=20)
        continue

    # 执行独立样本t检验 (使用原始数据)
    t_stat, t_p_value = ttest_ind(data_3, data_4, equal_var=False)

    # 计算效应量 (使用原始数据)
    effect_size = cohens_d(data_3, data_4)

    # 计算置信区间 (使用原始数据)
    ci_3_lower, ci_3_upper = calculate_confidence_interval(data_3)
    ci_4_lower, ci_4_upper = calculate_confidence_interval(data_4)

    # 准备数据 - 调换顺序，草本在左，灌木在右
    box_data = [data_4.values, data_3.values]  # 草本在前，灌木在后
    x_tick_labels = ['草本', '灌木']  # 左草右灌

    # 定义颜色 - 草本在前（索引0），灌木在后（索引1）
    box_colors = ['#2C5C8A', '#CC6633']  # 草本深蓝色，灌木暖橙色
    whisker_caps_colors = ['#87CEEB', '#FFA500']  # 草本浅蓝色，灌木浅橙色

    # 【关键修改】添加 flierprops 来隐藏离群点
    bp = axes[i].boxplot(
        box_data,
        tick_labels=x_tick_labels,
        patch_artist=True,
        widths=0.6,
        showmeans=True,
        meanprops={
            "marker": "o",
            "markerfacecolor": "white",
            "markeredgecolor": "black",
            "markersize": 10,
            "linestyle": "none"
        },
        medianprops=dict(color="black", linewidth=3),
        # --- 隐藏离群点 ---
        flierprops=dict(marker='.', markersize=0, alpha=0, color='white')
        # ------------------
    )

    # 设置箱体颜色和边框颜色
    for patch, color in zip(bp['boxes'], box_colors):
        patch.set_facecolor(color)
        patch.set_edgecolor('black')  # 边框颜色与填充颜色一致
        patch.set_linewidth(2)

    # 1. 标注均值数值 (使用原始数据计算的均值) - 调换顺序
    mean_4 = np.mean(data_4)  # 草本在左边
    mean_3 = np.mean(data_3)  # 灌木在右边

    # 获取箱体底部 Y 坐标 (使用原始数据绘制的箱线图)
    bottom_y_4 = bp['whiskers'][0].get_ydata()[0]  # 第一个箱体（草本）的下须线末端
    bottom_y_3 = bp['whiskers'][2].get_ydata()[0]  # 第二个箱体（灌木）的下须线末端

    # 动态计算偏移量
    y_range = axes[i].get_ylim()[1] - axes[i].get_ylim()[0]
    offset = y_range * 0.05

    axes[i].text(1, bottom_y_4, f'均值: {mean_4:.2f}',
                 horizontalalignment='right', verticalalignment='top',
                 color='black', fontsize=0, fontweight='bold')

    axes[i].text(2, bottom_y_3, f'均值: {mean_3:.2f}',
                 horizontalalignment='right', verticalalignment='top',
                 color='black', fontsize=0, fontweight='bold')

    # 2. 添加显著性标记 (使用原始数据计算的 p 值)
    max_whisker = max([w.get_ydata()[1] for w in bp['whiskers']])  # 上须线的最大值
    min_whisker = min([w.get_ydata()[0] for w in bp['whiskers']])  # 下须线的最小值
    line_height = max_whisker  # 固定加50

    # 画星号
    sig_text = ""
    if t_p_value < 0.001:
        sig_text = "***"
    elif t_p_value < 0.01:
        sig_text = "**"
    elif t_p_value < 0.05:
        sig_text = "*"

    if sig_text:
        axes[i].text(1.5, line_height + 5,  # 星号位置稍微上移
                     sig_text, horizontalalignment='center', verticalalignment='bottom',
                     fontsize=24, fontweight='bold', color='red')

    axes[i].set_title(f"{metric.upper()} 对比", fontsize=20)
    axes[i].set_ylabel("DOY", fontsize=20)
    axes[i].set_xticklabels(x_tick_labels, fontsize=20)

    # 调大坐标轴标签字体
    axes[i].tick_params(axis='y', labelsize=20)

    # 美化边框
    axes[i].spines['top'].set_visible(False)
    axes[i].spines['right'].set_visible(False)

    # 设置特定的Y轴范围
    y_min, y_max = y_axis_ranges[metric]
    axes[i].set_ylim(y_min, y_max)

    # 设置以10为步长的刻度
    start_tick = int(y_min // 10) * 10
    end_tick = int((y_max // 10 + 1)) * 10

    # 生成10的倍数刻度
    ticks = list(range(start_tick, end_tick + 10, 10))
    axes[i].set_yticks(ticks)

# 保存图像
output_plot_path = r'E:\Desktop\物候差异\遥感\草转灌.png'
plt.savefig(output_plot_path, dpi=300, bbox_inches='tight')
plt.close()  # 关闭图形以释放内存

# 打印统计摘要 (使用原始数据) - 也相应调整顺序
print("\n统计摘要 (使用原始数据):")
for metric in phenology_metrics:
    col_3_mean = f'{metric}_3_mean'
    col_4_mean = f'{metric}_4_mean'
    col_si_current = 'si_current'

    # 使用原始数据进行过滤
    initial_valid_mask = (
            (df[col_3_mean] != 0) & (~df[col_3_mean].isna()) &
            (df[col_4_mean] != 0) & (~df[col_4_mean].isna()) &
            (df[col_si_current] != 0) & (~df[col_si_current].isna())
    )
    valid_df = df[initial_valid_mask].copy()

    if valid_df.empty:
        print(f"\n{metric}: 初始数据为空")
        continue

    data_3 = valid_df[col_3_mean].dropna()
    data_4 = valid_df[col_4_mean].dropna()

    if data_3.empty or data_4.empty:
        print(f"\n{metric}: 某一类别过滤后为空")
        continue

    t_stat, t_p_value = ttest_ind(data_4, data_3, equal_var=False)  # 注意这里也调换了顺序，草本在前，灌木在后
    effect_size = cohens_d(data_4, data_3)  # 注意这里也调换了顺序

    print(f"\n{metric.upper()} 类别间差异检验 (使用原始数据，草本 vs 灌木):")
    print(f"  草本 (原4类): n={len(data_4)}, 均值={np.mean(data_4):.2f}, 标准差={np.std(data_4):.2f}")
    print(f"  灌木 (原3类): n={len(data_3)}, 均值={np.mean(data_3):.2f}, 标准差={np.std(data_3):.2f}")
    print(f"  t检验 p值: {t_p_value:.6e}")
    print(f"  Cohen's d (效应量): {effect_size:.4f}")

    # 解释效应量
    if abs(effect_size) >= 0.8:
        es_interpret = "大效应"
    elif abs(effect_size) >= 0.5:
        es_interpret = "中等效应"
    elif abs(effect_size) >= 0.2:
        es_interpret = "小效应"
    else:
        es_interpret = "可忽略效应"

    print(f"  效应量解释: {es_interpret}")

    if t_p_value < 0.001 and abs(effect_size) >= 0.2:
        print(f"  统计结论: 极显著且存在有意义的差异")
    elif t_p_value < 0.05 and abs(effect_size) >= 0.2:
        print(f"  统计结论: 显著且存在有意义的差异")
    elif t_p_value < 0.05:
        print(f"  统计结论: 统计学显著但效应量小")
    else:
        print(f"  统计结论: 无统计学显著性")

print(f"\n图像已保存至: {output_plot_path}")
