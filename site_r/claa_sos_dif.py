import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress
import matplotlib.font_manager as fm

# 设置matplotlib使用Times New Roman字体
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']

# 读取Excel文件
file_path = 'F:\\个人\\allsos_class_results_31_32_33.xlsx'
excel_data = pd.read_excel(file_path, sheet_name='dif')

# 假设第一列是年份
years = excel_data['Year'].values

# 提取需要的列
gl_evi = excel_data['GL EVI'].values
wp_evi = excel_data['WP EVI'].values
dif = excel_data['dif'].values

# 创建一个图形窗口
plt.figure(figsize=(10, 6))

# 定义颜色
colors = ['blue', 'green', 'red']
labels = ['GL EVI', 'WP EVI', 'Dif']

# 绘制散点图
plt.scatter(years, gl_evi, color=colors[0], label=labels[0])
plt.scatter(years, wp_evi, color=colors[1], label=labels[1])
plt.scatter(years, dif, color=colors[2], label=labels[2])

# 拟合线
for i, (data, label, color) in enumerate(zip([gl_evi, wp_evi, dif], labels, colors)):
    slope, intercept, r_value, p_value, std_err = linregress(years, data)
    y_fit = slope * years + intercept
    legend_label = f"{label} (Slope = {slope:.4f}, p-value = {p_value:.4f})"
    plt.plot(years, y_fit, color=color, linestyle='--', label=legend_label)

# 设置标题和轴标签
font_properties = {'family': 'serif', 'color': 'black', 'weight': 'normal', 'size': 12}
plt.xlabel('Year', fontdict=font_properties)
plt.ylabel('EVI Values', fontdict=font_properties)

# 添加图例
plt.legend(prop={'family': 'serif', 'size': 10})

# 调整布局，避免重叠
plt.tight_layout()

# 显示图形
plt.show()