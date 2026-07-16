# -*- coding: utf-8 -*-
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error
from math import sqrt
# 读取数据
df = pd.read_csv('F:\pythonforR\EoS_yanzhen_ap\\eos_nonquilty.csv')
# 定义阈值列的列表Budburst	flower	fruit	SeedDisper	Senescence
acture3  = ['EOS']
thresholds= ['1','13','2','3','4','5']
meth= ['NDGI', 'EVI', 'NDPI', 'NDVI', 'DVI']


BIOINDIX  = ['threshold_NDGI',  'threshold_EVI', 'threshold_NDPI', 'threshold_NDVI', 'threshold_DVI']
BIOINDIX2  =['cubic_EoS_EVT','filtercubic_EoS_EVT','mintomaxcubiccubic_EoS_EVT']
EoS_thresholds = [
    f"{bio}{threshold}"
    for bio in BIOINDIX
    for threshold in thresholds
]
EoS_EVT = [
    f"{bio}{threshold}"
    for bio in BIOINDIX2
    for threshold in meth
]



#添加day
daysos_thresholds = ['EoS_' + SoS_threshold for SoS_threshold in EoS_thresholds]
filterdaysos_thresholds = ['EoS_filter' + SoS_threshold for SoS_threshold in EoS_thresholds]
mintomaxdaysos_thresholds =['EoS_mintomax' + SoS_threshold for SoS_threshold in EoS_thresholds]

cubic_SoS= ['EoS_cubic_' + SoS_threshold for SoS_threshold in EoS_thresholds]
filtercubic_SoS= ['EoS_filtercubic_' + SoS_threshold for SoS_threshold in EoS_thresholds]
mintomaxcubic_SoS= ['EoS_mintomaxcubic_' + SoS_threshold for SoS_threshold in EoS_thresholds]

doublelogistic_SoS= ['EoS_doublelogistic_' + SoS_threshold for SoS_threshold in EoS_thresholds]
filterdoublelogistic_SoS= ['EoS_filterdoublelogistic_' + SoS_threshold for SoS_threshold in EoS_thresholds]
mintomaxdoublelogistic_SoS= ['EoS_mintomaxdoublelogistic_' + SoS_threshold for SoS_threshold in EoS_thresholds]

allEoS=daysos_thresholds+filterdaysos_thresholds+mintomaxdaysos_thresholds+cubic_SoS+filtercubic_SoS+mintomaxcubic_SoS+doublelogistic_SoS+filterdoublelogistic_SoS+mintomaxdoublelogistic_SoS+EoS_EVT
# 初始化一个DataFrame来存储所有计算结果
results = pd.DataFrame()

for stage in acture3:
    for threshold in allEoS:
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
results.to_csv('EOS_statistical_result_nonquilty.csv', index=False)