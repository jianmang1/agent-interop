import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import ttest_ind

# 加载数据
data1 = pd.read_excel(r'F:\个人\S0S_COV\wdsos_results1.xlsx')
data2 = pd.read_excel(r'F:\个人\S0S_COV\glsos_results1.xlsx')
data3 = pd.read_excel(r'F:\个人\S0S_COV\ALLsos_results1.xlsx')  # 新添加的数据集

# 对每个 Coverage Value 计算 Mean EVI 的平均值
mean_evi_data1 = data1.groupby('Coverage Value')['Mean EVI'].mean().reset_index()
mean_evi_data2 = data2.groupby('Coverage Value')['Mean EVI'].mean().reset_index()
mean_evi_data3 = data3.groupby('Coverage Value')['Mean EVI'].mean().reset_index()  # 新添加的数据集

# 定义一个函数来拟合曲线，这里假设我们使用线性回归模型
def linear_func(x, a, b):
    return a * x + b

# 拟合数据
params1, _ = curve_fit(linear_func, mean_evi_data1['Coverage Value'], mean_evi_data1['Mean EVI'])
params2, _ = curve_fit(linear_func, mean_evi_data2['Coverage Value'], mean_evi_data2['Mean EVI'])
params3, _ = curve_fit(linear_func, mean_evi_data3['Coverage Value'], mean_evi_data3['Mean EVI'])  # 新添加的数据集

# 计算三条拟合线的 T-Statistic 和 P-Value
y1_fitted = linear_func(mean_evi_data1['Coverage Value'], *params1)
y2_fitted = linear_func(mean_evi_data2['Coverage Value'], *params2)
y3_fitted = linear_func(mean_evi_data3['Coverage Value'], *params3)  # 新添加的数据集

t_stat_12, p_value_12 = ttest_ind(y1_fitted, y2_fitted, equal_var=False)
t_stat_13, p_value_13 = ttest_ind(y1_fitted, y3_fitted, equal_var=False)  # 新添加的数据集
t_stat_23, p_value_23 = ttest_ind(y2_fitted, y3_fitted, equal_var=False)  # 新添加的数据集

# 绘制散点图及拟合曲线
plt.figure(figsize=(10, 6))

# 绘制第一组数据的散点图
plt.scatter(mean_evi_data1['Coverage Value'], mean_evi_data1['Mean EVI'], color='blue', edgecolor='blue', facecolor='none', alpha=0.5, s=20, label='WD')
# 绘制第一组数据的拟合曲线
x1 = np.linspace(min(mean_evi_data1['Coverage Value']), max(mean_evi_data1['Coverage Value']), 100)
y1 = linear_func(x1, *params1)
plt.plot(x1, y1, color='blue', linewidth=2)

# 绘制第二组数据的散点图
plt.scatter(mean_evi_data2['Coverage Value'], mean_evi_data2['Mean EVI'], color='red', edgecolor='red', facecolor='none', alpha=0.5, s=20, label='GL')
# 绘制第二组数据的拟合曲线
x2 = np.linspace(min(mean_evi_data2['Coverage Value']), max(mean_evi_data2['Coverage Value']), 100)
y2 = linear_func(x2, *params2)
plt.plot(x2, y2, color='red', linewidth=2)

# 绘制第三组数据的散点图
plt.scatter(mean_evi_data3['Coverage Value'], mean_evi_data3['Mean EVI'], color='green', edgecolor='green', facecolor='none', alpha=0.5, s=20, label='ALL')  # 新添加的数据集
# 绘制第三组数据的拟合曲线
x3 = np.linspace(min(mean_evi_data3['Coverage Value']), max(mean_evi_data3['Coverage Value']), 100)
y3 = linear_func(x3, *params3)
plt.plot(x3, y3, color='green', linewidth=2)  # 新添加的数据集

plt.xlabel('Coverage Value')
plt.ylabel('Mean EVI')
plt.title('WD VS GL VS ALL')
plt.legend()

# 添加T-Statistic和P-Value的注释
plt.text(0.5, 0.95, f'T-Statistic (WD vs GL): {t_stat_12:.4f}\nP-Value (WD vs GL): {p_value_12:.4e}\n'
                    f'T-Statistic (WD vs ALL): {t_stat_13:.4f}\nP-Value (WD vs ALL): {p_value_13:.4e}\n'
                    f'T-Statistic (GL vs ALL): {t_stat_23:.4f}\nP-Value (GL vs ALL): {p_value_23:.4e}',
         transform=plt.gca().transAxes, fontsize=12, verticalalignment='top')

plt.show()