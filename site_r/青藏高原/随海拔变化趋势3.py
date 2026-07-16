import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from scipy.stats import pearsonr

# 读取csv文件
df = pd.read_csv(r'D:\海拔\2\qtg_los_data.csv')

# 删除包含NaN的行
df.dropna(subset=['DEM', 'QTG_LOS'], inplace=True)

x = df['DEM'].values.reshape(-1, 1)  # 将x转换为列向量形式
y = df['QTG_LOS'].values

# 创建并训练线性回归模型
model = LinearRegression()
model.fit(x, y)

# 预测
y_pred = model.predict(x)

# 计算相关系数r和p值
r, p = pearsonr(x.ravel(), y)

# 样本数N
N = len(df)

# 拟合线公式
fit_eq = f'y = {model.coef_[0]:.4f}x + {model.intercept_:.2f}'

# 设置全局字体为Times New Roman，大小为8pt
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 10

# 绘制散点图和拟合线
fig = plt.figure(figsize=(4, 4 * (6/10)))  # 宽度设为5cm（约1.97英寸），保持原宽高比
sns.scatterplot(x='DEM', y='QTG_LOS', color='brown', data=df, s=1, alpha=0.3)  # 设置点的大小为1

plt.plot(df['DEM'], y_pred, color='brown', label='Fitted line')  # 拟合线

# 添加图例信息
if p < 0.01:
    legend_text = f'N = {N}\n{fit_eq}\n$R^{{2}} = {r**2:.2f}$ ,P < 0.01'
else:
    legend_text = f'N = {N}\n{fit_eq}\n$R^{{2}} = {r**2:.2f}$ ,P = {p:.2e}'
plt.legend([legend_text], handlelength=0, bbox_to_anchor=(0.50, 0.0), loc='lower left', frameon=False)

plt.xlabel('Elevation (m)')
plt.ylabel('QTP_LOS (d)')
plt.tight_layout()  # 自动调整子图参数,使之填充整个图像区域

# 导出图片，指定dpi确保尺寸准确
plt.savefig('output_plot.png', format='png', dpi=600, bbox_inches='tight')
plt.show()



