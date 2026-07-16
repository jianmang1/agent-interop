import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression

# 加载Excel文件
df = pd.read_csv(r'F:\pythonforR\sos\op\wdall\DRleaf.CSV')  # 使用原始字符串来避免转义字符问题

# 清洗数据，确保没有NaN值
df.dropna(subset=['filtercubic_SoS_threshold_EVI8', 'leaf'], inplace=True)

# 定义计算函数
def calculate_stats(valid_data, leaf_col, evi_col):
    # 计算相关系数 R
    r, _ = pearsonr(valid_data[leaf_col], valid_data[evi_col])

    # 计算均方根误差 RMSE
    rmse = np.sqrt(mean_squared_error(valid_data[leaf_col], valid_data[evi_col]))

    # 计算Kling-Gupta效率系数 KGE
    alpha = valid_data[evi_col].std() / valid_data[leaf_col].std()
    evi_cv = valid_data[evi_col].std() / valid_data[evi_col].mean()
    leaf_cv = valid_data[leaf_col].std() / valid_data[leaf_col].mean()
    beta = evi_cv / leaf_cv
    kge = 1 - np.sqrt(((r - 1) ** 2) + ((alpha - 1) ** 2) + ((beta - 1) ** 2))

    return {'R': r, 'RMSE': rmse, 'KGE': kge}

# 对所有数据进行计算
valid_data = df[['leaf', 'filtercubic_SoS_threshold_EVI8']]
stats = calculate_stats(valid_data, 'leaf', 'filtercubic_SoS_threshold_EVI8')

# 创建散点图
plt.figure(figsize=(12, 6))
sns.scatterplot(data=df, x='leaf', y='filtercubic_SoS_threshold_EVI8', hue='Site', palette='viridis')
plt.title('Scatter Plot of Leaf vs filtercubic_SoS_threshold_EVI0.08')
plt.xlabel('Leaf')
plt.ylabel('filtercubic_SoS_threshold_EVI0.08')
plt.legend(title='Site')

# 添加统计信息到图中
text_str = f"R: {stats['R']:.2f}\nRMSE: {stats['RMSE']:.2f}\nKGE: {stats['KGE']:.2f}"
plt.text(0.05, 0.95, text_str, transform=plt.gca().transAxes, fontsize=10, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.5))

# 添加拟合线
leaf = df['leaf'].values.reshape(-1, 1)  # 需要将x转换成二维数组
filtercubic_SoS_threshold_EVI8 = df['filtercubic_SoS_threshold_EVI8'].values
model = LinearRegression().fit(leaf, filtercubic_SoS_threshold_EVI8)
y_pred = model.predict(leaf)
plt.plot(leaf, y_pred, color='red', label='Fit Line')

# 添加1:1线
lims = [np.min([leaf.min(), filtercubic_SoS_threshold_EVI8.min()]), np.max([leaf.max(), filtercubic_SoS_threshold_EVI8.max()])]
plt.plot(lims, lims, 'k--', label='1:1 Line')

plt.legend()
plt.show()