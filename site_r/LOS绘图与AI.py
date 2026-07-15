import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# 使用通用字体，避免中文乱码
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})

# 读取数据
file_path = r"F:\pythonforR\LOS\3.csv"
df = pd.read_csv(file_path)
df.columns = df.columns.str.strip()  # 清理列名空格

# 检查数据形状与缺失值
print("数据形状:", df.shape)
print("列名:", df.columns.tolist())
print("缺失值统计:\n", df.isnull().sum())

# 检查是否所有值都相同（无法拟合）
print("\nAI 列统计:")
print(df['AI'].describe())
print("\nLOS 列统计:")
print(df['LOS'].describe())
print("\nPixel_Value 列统计:")
print(df['Pixel_Value'].describe())

# 提取关键列
x = df['AI']
y1_raw = df['LOS']
y2_raw = df['Pixel_Value']
y1_mean = df['LOS_mean']
y2_mean = df['Pixel_Value_mean']

# 数据清洗：移除 NaN 和无穷值
valid_mask = x.notna() & y1_mean.notna() & y2_mean.notna()
x_clean = x[valid_mask]
y1_clean = y1_mean[valid_mask]
y2_clean = y2_mean[valid_mask]

print(f"\n清洗后有效数据点数: {len(x_clean)}")

# 检查是否仍有足够数据点拟合
if len(x_clean) < 2:
    print("❌ 错误：清洗后数据点不足，无法拟合")
    exit()

# 创建图形
plt.figure(figsize=(9, 6))

# 绘制原始散点（底层，透明度高，小点）
plt.scatter(x, y1_raw, alpha=0.3, color='gray', s=20, label='Site_LOS (Site Values)', zorder=1)
plt.scatter(x, y2_raw, alpha=0.3, color='lightgray', s=20, label='Pixel_LOS (Remote Sensing)', zorder=1)

# 绘制均值数据（顶层，醒目）
plt.scatter(x_clean, y1_clean, color='tab:blue', s=80, edgecolor='k', linewidth=0.5, label='Site_LOS_mean', zorder=5)
plt.scatter(x_clean, y2_clean, color='tab:red', s=80, edgecolor='k', linewidth=0.5, marker='^', label='Pixel_LOS_mean', zorder=5)

# 拟合 LOS_mean
if len(x_clean) > 1 and x_clean.std() != 0 and y1_clean.std() != 0:
    slope1, intercept1, r1, p1, se1 = stats.linregress(x_clean, y1_clean)
    r2_1 = r1**2
    line1 = slope1 * x_clean + intercept1
    plt.plot(x_clean, line1, color='tab:blue', linestyle='-', linewidth=2, zorder=3)
    text1 = f'Site_LOS_mean: y = {intercept1:.2f} {"-" if slope1 < 0 else "+"} {abs(slope1):.2f} * x\nR² = {r2_1:.3f}'
else:
    text1 = 'Site_LOS_mean: Cannot fit (no variance)'

# 拟合 Pixel_Value_mean
if len(x_clean) > 1 and x_clean.std() != 0 and y2_clean.std() != 0:
    slope2, intercept2, r2, p2, se2 = stats.linregress(x_clean, y2_clean)
    r2_2 = r2**2
    line2 = slope2 * x_clean + intercept2
    plt.plot(x_clean, line2, color='tab:red', linestyle='--', linewidth=2, zorder=3)
    text2 = f'Pixel_LOS_mean: y = {intercept2:.2f} {"-" if slope2 < 0 else "+"} {abs(slope2):.2f} * x\nR² = {r2_2:.3f}'
else:
    text2 = 'Pixel_LOS_mean: Cannot fit (no variance)'

# 添加文本框（左上角）
plt.text(0.02, 0.98, text1, transform=plt.gca().transAxes, fontsize=10,
         verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))

plt.text(0.02, 0.85, text2, transform=plt.gca().transAxes, fontsize=10,
         verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral", alpha=0.7))

# 标签与标题
plt.xlabel('AI')
plt.ylabel('LOS')
plt.title('Relationship between AI and LOS')
plt.legend(loc='upper right')
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()

# 保存图像
output_path = r"F:\pythonforR\LOS\AI_vs_LOS_with_mean_and_fit_cleaned.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"✅ Image saved to: {output_path}")

plt.show()