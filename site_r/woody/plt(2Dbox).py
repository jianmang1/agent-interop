import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm

# 设置matplotlib使用Times New Roman字体
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']

# 读取Excel文件
file_path = 'F:\\个人\\allsos_class_results.xlsx'
excel_data = pd.read_excel(file_path, sheet_name='Value_22')

# 假设第一列是年份
years = excel_data.iloc[:, 0].values

# 提取需要的列
columns_of_interest = ['Min EVI', 'Q1 EVI', 'Median EVI', 'Q3 EVI', 'Max EVI']

# 确保数据的行数与年份数量一致
if len(years) != len(excel_data):
    print("Error: The number of years does not match the number of rows in the data.")
    exit()

# 创建一个图形窗口
plt.figure(figsize=(10, 6))

# 绘制箱形图
data_for_boxplot = []
for year in years:
    row_data = excel_data.loc[excel_data.iloc[:, 0] == year, columns_of_interest].values.flatten()
    data_for_boxplot.append(row_data)

plt.boxplot(data_for_boxplot, labels=years)

# 设置标题和轴标签
font_properties = {'family': 'serif', 'color': 'black', 'weight': 'normal', 'size': 12}
plt.title('Boxplot of Mean Values for "WP"', fontdict=font_properties)
plt.xlabel('Year', fontdict=font_properties)
plt.ylabel('Mean Grassland Cover Values', fontdict=font_properties)

# 添加趋势线
mean_values = excel_data[columns_of_interest].mean(axis=1)
x = np.arange(1, len(years) + 1)
y = mean_values.values
z = np.polyfit(x, y, 1)
p = np.poly1d(z)
trend_slope = z[0]
trend_p_value = excel_data['p-value'].iloc[-1]  # 假设p-value在最后一列

# 创建图例标签
legend_label = f"Trendline (Slope = {trend_slope:.4f}, p-value = {trend_p_value:.4f})"

# 绘制趋势线
plt.plot(x, p(x), "r--", label=legend_label)

# 添加图例
plt.legend(prop={'family': 'serif', 'size': 10})

# 调整布局，避免重叠
plt.tight_layout()

# 显示图形
plt.show()