import pandas as pd
import matplotlib.pyplot as plt
import os

# 设置全局字体为Times New Roman
plt.rcParams['font.family'] = 'Times New Roman'

# 设置文件路径
path = r'E:\Desktop\旱区物候\plt1'

# 读取所有CSV文件
df1 = pd.read_csv(os.path.join(path, '1.csv'), parse_dates=['date'])  # 原始每日数据
df2 = pd.read_csv(os.path.join(path, '2.csv'), parse_dates=['date'])  # 15天窗口数据
df3 = pd.read_csv(os.path.join(path, '3.csv'), parse_dates=['date'])  # 平滑后数据

# 计算振幅和最小值
min_value = df3['value'].min()
amplitude = df3['value'].max() - min_value

# 定义系数列表（避免使用元组）
sos_coeffs = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3]  # SOS系数
eos_coeffs = [0.45, 0.5, 0.55, 0.6, 0.65, 0.7]  # EOS系数

# 生成阈值（最小值 + 振幅 × 系数）
sos_thresholds = [min_value + amplitude * t for t in sos_coeffs]
eos_thresholds = [min_value + amplitude * t for t in eos_coeffs]

# 创建绘图
fig, ax = plt.subplots(figsize=(14, 8))

# 绘制原始数据（每日数据）- 使用浅灰色
ax.plot(df1['date'], df1['value'],
        'o', markersize=3, alpha=0.5,
        color='#B0B0B0', label='Original Daily Data')

# 绘制15天窗口数据-使用中等灰色
ax.plot(df2['date'], df2['value'],
        's', markersize=5, alpha=0.7,
        color='#808080', label='15-day Window Data')

# 绘制平滑后数据（曲线）-使用深绿色
ax.plot(df3['date'], df3['value'],
        '-', linewidth=2.5, color='#228B22',
        label='Smoothed Data')

# 或者使用更自然的植物颜色渐变：
# 复苏：从冬季褐色到春季绿色
sos_colors = ['#8D6E63', '#A1887F', '#78909C', '#4DB6AC', '#81C784', '#66BB6A']

# 衰败：从夏季绿色到秋季褐色
eos_colors = ['#8D6E63', '#A1887F', '#78909C', '#4DB6AC', '#81C784', '#66BB6A']
# 绘制SOS阈值竖线（第一个超过阈值的点）-实线
for i, t in enumerate(sos_thresholds):
    mask = df3['value'] > t
    if mask.any():
        first_date = df3.loc[mask, 'date'].iloc[0]  # 第一个超过阈值的点
        ax.axvline(first_date, color=sos_colors[i], linestyle='-',
                   linewidth=1.5, alpha=0.8,
                   label=f'{int(sos_coeffs[i] * 100)}% SOS Threshold ')

# 绘制EOS阈值竖线（最后一个超过阈值的点）-虚线
for i, t in enumerate(eos_thresholds):
    mask = df3['value'] > t
    if mask.any():
        last_date = df3.loc[mask, 'date'].iloc[-1]  # 最后一个超过阈值的点
        ax.axvline(last_date, color=eos_colors[i], linestyle='--',
                   linewidth=1.5, alpha=0.8,
                   label=f'{int(eos_coeffs[i] * 100)}% EOS Threshold ')

# 图表美化
ax.set_xlabel('Date', fontsize=10, fontweight='bold')
ax.set_ylabel('EVI Value', fontsize=10, fontweight='bold')

# 设置图例
legend = ax.legend(bbox_to_anchor=(0.82, 1), loc='upper left', fontsize=10, frameon=True, fancybox=True, shadow=True)
legend.get_frame().set_facecolor('white')
legend.get_frame().set_alpha(0.9)

# 设置网格
ax.grid(True, linestyle='--', alpha=0.3, color='gray')
ax.set_axisbelow(True)

# 日期格式调整
fig.autofmt_xdate()

# 调整布局
plt.tight_layout()
plt.subplots_adjust(right=0.85)  # 为图例留出空间
plt.show()



