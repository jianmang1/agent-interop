# -*- coding: utf-8 -*-
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error
from math import sqrt
import numpy as np

# 读取数据
df = pd.read_csv('F:\pythonforR\ALLPLANT0.csv')
# 定义阈值列的列表  Budburst	flower	fruit	SeedDisper	Senescence
acture1  = ['bud']
acture2  = ['flower','fruit','SeedDisper']
acture3  = ['Senescence']


thresholds  = ['filtercubic_SoS_threshold_EVI5','filtercubic_SoS_threshold_EVI6','filtercubic_SoS_threshold_EVI7','filtercubic_SoS_threshold_EVI8','filtercubic_SoS_threshold_EVI9']

# 初始化一个DataFrame来存储所有计算结果
results = pd.DataFrame()

for stage in acture1:
    for threshold in thresholds:
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
        alpha = valid_data[threshold].std() / valid_data[stage].std()  # 变异性比率
        thresholdCV = valid_data[threshold].std() / valid_data[threshold].mean()
        stageCV = valid_data[stage].std() / valid_data[stage].mean()
        # 计算变异系数
        beta = thresholdCV / stageCV  # 计算KGE
        kge = 1 - np.sqrt(((r - 1) ** 2) + ((alpha - 1) ** 2) + ((beta - 1) ** 2))
        temp_df['KGE'] = kge

        # 添加标识列，表明这是哪个阶段与哪个阈值的统计信息
        temp_df['name'] = stage + threshold

        # 将结果合并到总的DataFrame中
        results = pd.concat([results, temp_df], ignore_index=True)

print(results)

# Save results
results.to_csv('allsos_opti.csv', index=False)