# -*- coding: utf-8 -*-
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error
from math import sqrt
import numpy as np

# 读取数据
df = pd.read_csv('F:\pythonforR\sos/GL_SOS.csv')
# 定义阈值列的列表Budburst	flower	fruit	SeedDisper	Senescence
acture1  = ['Budburst']
acture2  = ['flower','fruit', 'SeedDisper']
acture3  = ['Senescence']


thresholds  = ['SoS_threshold_NDGI1','SoS_threshold_NDGI13','SoS_threshold_NDGI2', 'SoS_threshold_NDGI3', 'SoS_threshold_NDGI4','SoS_threshold_NDGI5',
               'SoS_threshold_EVI1','SoS_threshold_EVI3','SoS_threshold_EVI2', 'SoS_threshold_EVI3','SoS_threshold_EVI4', 'SoS_threshold_EVI5',
               'SoS_threshold_NDPI1','SoS_threshold_NDPI13','SoS_threshold_NDPI2','SoS_threshold_NDPI3', 'SoS_threshold_NDPI4', 'SoS_threshold_NDPI5',
                'SoS_threshold_NDVI1','SoS_threshold_NDVI13','SoS_threshold_NDVI2', 'SoS_threshold_NDVI3', 'SoS_threshold_NDVI4','SoS_threshold_NDVI5',
               'SoS_threshold_PPI1','SoS_threshold_PPI13','SoS_threshold_PPI2', 'SoS_threshold_PPI3','SoS_threshold_PPI4', 'SoS_threshold_PPI5']
filtersos_thresholds = ['filter' + threshold for threshold in thresholds]
mintomaxsos_thresholds = ['mintomax' + threshold for threshold in thresholds]

cubicSOS = ['cubic_' + threshold for threshold in thresholds]
filtercubicsos_thresholds = ['filter_' + cubic for cubic in cubicSOS]
mintomaxcubicsos_thresholds = ['mintomax' + cubic for cubic in cubicSOS]

doublelogisticSOS = ['doublelogistic_' + threshold for threshold in thresholds]
filterdoublelogisticthresholds = ['filter' + doublelogis for doublelogis in doublelogisticSOS]
mintomdoublelogisticthresholds = ['mintomax' + doublelogis for doublelogis in doublelogisticSOS]

combined_list = cubicSOS + filtercubicsos_thresholds + mintomaxcubicsos_thresholds + doublelogisticSOS + filterdoublelogisticthresholds + mintomdoublelogisticthresholds
print(combined_list)
# 初始化一个DataFrame来存储所有计算结果
results = pd.DataFrame()


for stage in acture1:
    for threshold in combined_list:
        # 临时DataFrame用于存储当前对的统计信息
        temp_df = pd.DataFrame()

        # 计算差值
        temp_df['dif'] = df[stage] - df[threshold]

        # 计算相关系数 R
        r, _ = pearsonr(df[stage], df[threshold])
        temp_df['R'] = r

        # 计算均方根误差 RMSE
        rmse = sqrt(mean_squared_error(df[stage], df[threshold]))
        temp_df['RMSE'] = rmse

        # 计算Kling-Gupta效率系数 KGE
        bias = (df[threshold] - df[stage]).mean()
        var_ratio = df[threshold].var() / df[stage].var()
        r2 = 1 - ((df[threshold] - df[stage]) ** 2).sum() / ((df[stage]) ** 2).sum()
        kge = 1 - sqrt((bias / df[stage].std()) ** 2 + (var_ratio - 1) ** 2 + (1 - r2) ** 2)
        temp_df['KGE'] = kge

        # 添加标识列，表明这是哪个阶段与哪个阈值的统计信息
        temp_df['name'] =stage+threshold

        # 将结果合并到总的DataFrame中
        results = pd.concat([results, temp_df], ignore_index=True)

print(results)
# 保存结果到CSV
results.to_csv('GL_sos_statistical_results.csv', index=False)