# -*- coding: utf-8 -*-
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error
from math import sqrt
# 读取数据
df = pd.read_csv('F:\pythonforR\POS\\pos.csv')
# 定义阈值列的列表Budburst	flower	fruit	SeedDisper	Senescence
acture3  = ['flower','fruit','fruit2']
thresholds= ['1','13','2','3','4','5']
meth= ['NDGI', 'EVI', 'NDPI', 'NDVI', 'DVI']


BIOINDIX  =['POS_cublic','POS_doublelogistic','POS_ nonsmooth']
pos = [
    f"{bio}{threshold}"
    for bio in BIOINDIX
    for threshold in meth
]
results = pd.DataFrame()

for stage in acture3:
    for threshold in pos:
        # 临时DataFrame用于存储当前对的统计信息
        temp_df = pd.DataFrame()

        # 筛选出无NaN值的行，用于后续计算
        valid_data = df.dropna(subset=[stage, threshold])

        # 计算差值
        temp_df['dif'] = valid_data[stage] - valid_data[threshold]

        # 计算相关系数 R
        r, _ = pearsonr(valid_data[stage], valid_data[threshold])
        temp_df['R'] = r

        # 计算均方根误差 RMSE
        rmse = sqrt(mean_squared_error(valid_data[stage], valid_data[threshold]))
        temp_df['RMSE'] = rmse

        # 计算Kling-Gupta效率系数 KGE
        bias = (valid_data[threshold] - valid_data[stage]).mean()
        var_ratio = valid_data[threshold].var() / valid_data[stage].var()
        r2 = 1 - ((valid_data[threshold] - valid_data[stage]) ** 2).sum() / ((valid_data[stage]) ** 2).sum()
        kge = 1 - sqrt((bias / valid_data[stage].std()) ** 2 + (var_ratio - 1) ** 2 + (1 - r2) ** 2)
        temp_df['KGE'] = kge

        # 添加标识列，表明这是哪个阶段与哪个阈值的统计信息
        temp_df['name'] = stage + threshold

        # 将结果合并到总的DataFrame中
        results = pd.concat([results, temp_df], ignore_index=True)
# 保存结果到CSV
results.to_csv('POS_statistical_result.csv', index=False)