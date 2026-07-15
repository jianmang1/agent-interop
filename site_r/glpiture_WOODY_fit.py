# -*- coding: utf-8 -*-
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error
from math import sqrt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import rcParams

# 读取数据
df = pd.read_csv('F:\pythonforR\WOODY_cublic.csv')
# 定义阈值列的列表  bud	leaf	flower1	flower2	fruit	autumn	fall
acture1  = ['bud','leaf']
acture2  = ['flower1','flower2','fruit']
acture3  = ['autumn','fall']
thresholds= ['1','13','2','3','4','5']

BIOINDIX  = ['EVI_cublicSoSthreshold', 'NDGI_cublicSoSthreshold', 'NDVI_cublicSoSthreshold', 'NDPI_cublicSoSthreshold','PPI_cublicSoSthreshold']
SoS_thresholds = [
    f"SoS_{bio}_{threshold}"
    for bio in BIOINDIX
    for threshold in thresholds
]
PoS_thresholds = ['PoS_threshold_EVI',  'PoS_threshold_NDVI', 'PoS_threshold_PPI', 'PoS_threshold_NDGI', 'PoS_threshold_NDPI']

EoS_thresholds = [
    f"EoS_{bio}_{threshold}"
    for bio in BIOINDIX
    for threshold in thresholds
]
#添加filterday_
#filterdaysos_thresholds = ['filter' + SoS_threshold for SoS_threshold in SoS_thresholds]
#filterdayeos_thresholds = ['filter' + EoS_threshold for EoS_threshold in EoS_thresholds]


for stage in acture3:
    fig = plt.figure(figsize=(20, 30))
    grid = gridspec.GridSpec(5, 6)
    counter = 0
    for threshold in EoS_thresholds:
        # 临时DataFrame用于存储当前对的统计信息
        temp_df = pd.DataFrame()

        # 筛选出无NaN值的行，用于后续计算
        valid_data = df.dropna(subset=[stage, threshold])

        # 计算差值
        temp_df['dif'] = valid_data[stage] - valid_data[threshold]
        dif = temp_df['dif'].mean()

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

        # 图
        ax = fig.add_subplot(grid[counter])  # 使用GridSpec定位子图

        ax.scatter(valid_data[stage], valid_data[threshold],
                   label=f'R={r:.2f}, '
                         f'RMSE={rmse:.2f}')
        fit = np.polyfit(valid_data[stage], valid_data[threshold], deg=1)
        poly1d_fn = np.poly1d(fit)
        x_fit = np.linspace(min(valid_data[stage]), max(valid_data[stage]), 100)
        ax.plot(x_fit, poly1d_fn(x_fit), color='red', linestyle='--', label='Linear Fit')
        ax.plot(x_fit, x_fit, color='blue', linestyle=':', label='1:1 Line')

        ax.set_xlabel(stage)
        ax.set_ylabel(threshold)
        ax.legend(bbox_to_anchor=(1.05, 0), loc='lower right', borderaxespad=0.)  # 优化图例位置
        ax.grid(True)

        counter += 1  # 移动到下一个子图
        #fig.text(0.5, 0.0, stage+'(Phenological Days at Site)', ha='center', fontsize=16)  # 横坐标名称
    plt.tight_layout()  # 自动调整子图参数，使之填充整个图像区域
    output_filename = stage+'(cubicfitting)'
    #output_filename = 'filterday'+output_filename
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')  # 导出图片，可选提高dpi以获得更清晰的图像
    plt.show()  # 如果还需要显示图像，则保留此行