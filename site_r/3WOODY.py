# -*- coding: utf-8 -*-
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error
from math import sqrt
import numpy as np
from permetrics.regression import RegressionMetric

# 读取数据
df = pd.read_csv('F:\pythonforR\\all_D.CSV')
# 定义阈值列的列表  bud	leaf	flower1	flower2	fruit	autumn	fall
acture1  = ['plantbud']
acture2  = ['flower1','flower2','fruit']
acture3  = ['autumn','fall']
thresholds= ['1','13','2','3','4','5']

BIOINDIX  = ['threshold_NDGI',  'threshold_EVI', 'threshold_NDPI', 'threshold_NDVI', 'threshold_PPI']
SoS_thresholds = [
    f"SoS_{bio}{threshold}"
    for bio in BIOINDIX
    for threshold in thresholds
]
PoS_thresholds = [
    f"PoS_{bio}"
    for bio in BIOINDIX
]
EoS_thresholds = [
    f"EoS_{bio}{threshold}"
    for bio in BIOINDIX
    for threshold in thresholds
]
#添加day
filterdaysos_thresholds = ['filter' + SoS_threshold for SoS_threshold in SoS_thresholds]
mintomaxdaysos_thresholds =['mintomax' + SoS_threshold for SoS_threshold in SoS_thresholds]

cubic_SoS= ['cubic_' + SoS_threshold for SoS_threshold in SoS_thresholds]
filtercubic_SoS= ['filter_cubic_' + SoS_threshold for SoS_threshold in SoS_thresholds]
mintomaxcubic_SoS= ['mintomaxcubic_' + SoS_threshold for SoS_threshold in SoS_thresholds]

doublelogistic_SoS= ['doublelogistic_' + SoS_threshold for SoS_threshold in SoS_thresholds]
filterdoublelogistic_SoS= ['filterdoublelogistic_' + SoS_threshold for SoS_threshold in SoS_thresholds]
mintomaxdoublelogistic_SoS= ['mintomaxdoublelogistic_' + SoS_threshold for SoS_threshold in SoS_thresholds]

allsos=SoS_thresholds+filterdaysos_thresholds+mintomaxdaysos_thresholds+cubic_SoS+filtercubic_SoS+mintomaxcubic_SoS+doublelogistic_SoS+filterdoublelogistic_SoS+mintomaxdoublelogistic_SoS
# 初始化一个DataFrame来存储所有计算结果
results = pd.DataFrame()

for stage in acture1:
    for threshold in allsos:
        # 临时DataFrame用于存储当前对的统计信息
        temp_df = pd.DataFrame()

        # 计算差值
        # temp_df['dif'] = df[stage] - df[threshold]

        # 计算相关系数 R
        r, _ = pearsonr(df[stage], df[threshold])
        temp_df['R'] = [r]

        # 计算均方根误差 RMSE
        rmse = sqrt(mean_squared_error(df[stage], df[threshold]))
        temp_df['RMSE'] = [rmse]

        # 计算Kling-Gupta效率系数 KGE
        bias = (df[threshold] - df[stage]).mean()
        var_ratio = df[threshold].var() / df[stage].var()
        r2 = 1 - ((df[threshold] - df[stage]) ** 2).sum() / ((df[stage]) ** 2).sum()
        kge = 1 - sqrt((bias / df[stage].std()) ** 2 + (var_ratio - 1) ** 2 + (1 - r2) ** 2)
        temp_df['KGE'] = [kge]


        # 添加标识列，表明这是哪个阶段与哪个阈值的统计信息
        temp_df['name'] =[stage+threshold]

        # 将结果合并到总的DataFrame中
        results = pd.concat([results, temp_df], ignore_index=True)

# 保存结果到CSV
results.to_csv('sos_statistical_results_all_D.csv', index=False)