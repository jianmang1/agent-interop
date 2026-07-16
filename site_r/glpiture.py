import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression

# 加载Excel文件
df = pd.read_csv('F:\pythonforR\POS\\pos.csv')

# 清洗数据，确保没有NaN值
df.dropna(subset=['POS_doublelogisticNDGI', 'fruit2'], inplace=True)

# 定义计算函数
def calculate_stats(valid_data, stage, threshold):
    # 计算相关系数 R
    r, _ = pearsonr(valid_data[stage], valid_data[threshold])

    # 计算均方根误差 RMSE
    rmse = np.sqrt(mean_squared_error(valid_data[stage], valid_data[threshold]))

    # 计算Kling-Gupta效率系数 KGE
    alpha = valid_data[threshold].std() / valid_data[stage].std()
    thresholdCV = valid_data[threshold].std() / valid_data[threshold].mean()
    stageCV = valid_data[stage].std() / valid_data[stage].mean()
    beta = thresholdCV / stageCV
    kge = 1 - np.sqrt(((r - 1) ** 2) + ((alpha - 1) ** 2) + ((beta - 1) ** 2))

    return {'R': r, 'RMSE': rmse, 'KGE': kge}

# 对所有数据进行计算
valid_data = df[['POS_doublelogisticNDGI', 'fruit2']]
stats = calculate_stats(valid_data, 'POS_doublelogisticNDGI', 'fruit2')

# 创建散点图
plt.figure(figsize=(12, 6))
sns.scatterplot(data=df, x='POS_doublelogisticNDGI', y='fruit2', hue='Site', palette='viridis')
plt.title('Scatter Plot of POS_doublelogisticNDGI')
plt.xlabel('POS_doublelogisticNDGI')
plt.ylabel('fruit2')
plt.legend(title='Site')

# 添加统计信息到图中
text_str = f"R: {stats['R']:.2f}\nRMSE: {stats['RMSE']:.2f}\nKGE: {stats['KGE']:.2f}"
plt.text(0.05, 0.95, text_str, transform=plt.gca().transAxes, fontsize=10, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.5))

# 添加拟合线
x = df['POS_doublelogisticNDGI'].values.reshape(-1, 1)
y = df['fruit2'].values
model = LinearRegression().fit(x, y)
y_pred = model.predict(x)
plt.plot(x, y_pred, color='red', label='Fit Line')

# 添加1:1线
lims = [np.min([x.min(), y.min()]), np.max([x.max(), y.max()])]
plt.plot(lims, lims, 'k--', label='1:1 Line')

plt.legend()
plt.show()