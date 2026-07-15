import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# 读取CSV文件
file_path = r"D:\海拔\1\slope_sd_results_combined.csv"
data = pd.read_csv(file_path)

# 确保数据包含所需列
required_columns = ['Dataset', 'Slope', 'Year', 'SD']
if not all(col in data.columns for col in required_columns):
    raise ValueError("CSV文件缺少必要的列，请检查数据格式。")

# 按 Dataset 列筛选数据
eos_data = data[data['Dataset'] == 'EOS']
sos_data = data[data['Dataset'] == 'SOS']
los_data = data[data['Dataset'] == 'LOS']

# 定义绘图函数
def plot_phenology(data, label, color):
    years = np.sort(data['Year'])  # 确保 years 有序
    slopes = data['Slope'].values[np.argsort(data['Year'])]  # 对齐排序后的 years

    # 计算线性回归
    slope_reg, intercept, r_value, p_value, std_err = linregress(years, slopes)
    regression_line = slope_reg * years + intercept

    # 计算残差标准差
    residuals = slopes - regression_line
    residual_std = np.std(residuals, ddof=2)  # ddof=2 因为自由度为 n-2

    # 计算置信区间
    n = len(years)
    t_value = 1.96  # 95% 置信区间
    confidence_interval = t_value * residual_std * np.sqrt(
        1/n + (years - np.mean(years))**2 / np.sum((years - np.mean(years))**2)
    )
    lower_bound = regression_line - confidence_interval
    upper_bound = regression_line + confidence_interval

    # 绘制原始数据点
    plt.scatter(data['Year'], data['Slope'], color=color, alpha=0.7, s=50)

    # 添加线性回归虚线
    plt.plot(years, regression_line, linestyle='--', color=color, alpha=0.7)

    # 填充置信区间
    plt.fill_between(years, lower_bound, upper_bound, color=color, alpha=0.3)
    # 格式化图例标签
    yearly_std = np.std(slopes, ddof=1)  # 使用样本标准差
    slope_label = f"{slope_reg:.4f} ± {yearly_std:.2f} d·year⁻¹"
    if p_value < 0.01:
        p_label = " (p < 0.01)"
    else:
        p_label = f" (p = {p_value:.2f})"
    r2_label = f"R² = {r_value ** 2:.2f}"
    legend_label = f"{label}: {slope_label}{p_label}, {r2_label}"

    # 在图例中显示
    plt.plot([], [], label=legend_label, color=color)

# 创建图表
plt.figure(figsize=(10, 6))

# 绘制 EOS、SOS 和 LOS 数据
plot_phenology(sos_data, 'SOS', 'brown')
plot_phenology(los_data, 'LOS', 'green')
plot_phenology(eos_data, 'EOS', 'purple')

# 设置图表标题和标签
plt.ylabel(r'Elevation-induced phenological shift (d·1000m$^{-1}$)', fontsize=10)
plt.xlabel('Year', fontsize=10)
plt.title('Elevation-induced Phenological Shifts Over Time', fontsize=10)

# 设置图例在右上角
plt.legend(bbox_to_anchor=(0.98, 0.98), loc='upper right', fontsize=10)

# 显示图表
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
