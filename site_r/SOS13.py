import matplotlib.pyplot as plt
import seaborn as sns
# -*- coding: utf-8 -*-
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error
from math import sqrt

# 读取CSV数据
df = pd.read_csv('F:\\pythonforR\\sos3\\sossite.csv')

# 定义实际观测列的列表
acture3 = ['Budburst']

# 定义阈值列的前缀列表
threshold_prefixes = ['SoS_doublelogisticthreshold_', 'mintomaxdoublelogistic_SoS_threshold_',
                      'SoS_filterdoublelogisticthreshold_',
                      'SoS_threshold_', 'SoS_filterthreshold_', 'SoS_mintomaxthreshold_',
                      'cubic_SoS_threshold_', 'filtercubic_SoS_threshold_', 'mintomaxcubic_SoS_threshold_']


# 定义方法列表
meth = ['NDVI', 'EVI', 'EVI2','NDPI','NDGI']

# 构建所有可能的阈值列名
all_threshold_columns1 = [
    f"{prefix}{method}{i}" for prefix in threshold_prefixes
    for method in meth
    for i in [1, 13, 2, 3, 4, 5]
]
all_threshold_columns2 = [
    f"{prefix}EVT{method}" for prefix in threshold_prefixes
    for method in meth
]
all_threshold_columns=all_threshold_columns1+all_threshold_columns2

# 筛选出数据框中实际存在的阈值列
existing_threshold_columns = [col for col in all_threshold_columns if col in df.columns]

# 创建一个空的结果DataFrame
results = pd.DataFrame()

import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, linregress
from sklearn.metrics import mean_squared_error
import math
import pandas as pd
import numpy as np  # 确保导入 numpy

# 假设 df 是你的数据框，acture3 和 existing_threshold_columns 是你想要比较的两组列名
# 你需要根据实际情况调整这些变量

# 定义每批保存的子图数量
batch_size = 30  # 每批次30个子图（因为5行6列=30）

# 计算总批次数量
num_plots = len(acture3) * len(existing_threshold_columns)
total_batches = math.ceil(num_plots / batch_size)

# 设置全局字体为Arial
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10  # 设置默认字体大小


for batch in range(total_batches):
    start_index = batch * batch_size
    end_index = min((batch + 1) * batch_size, num_plots)

    # 创建当前批次的子图网格，改为5行6列
    fig, axes = plt.subplots(5, 6, figsize=(20, 16))
    axes = axes.flatten()  # 将子图轴展平为一维数组

    letters = ['a', 'b', 'c', 'd', 'e', 'f']  # 定义字母列表

    for i in range(start_index, end_index):
        plot_index = i - start_index
        stage = acture3[i // len(existing_threshold_columns)]
        threshold = existing_threshold_columns[i % len(existing_threshold_columns)]

        # 筛选出无NaN值的行，用于后续计算
        valid_data = df.dropna(subset=[stage, threshold])

        if not valid_data.empty:
            # 在当前子图上绘制散点图
            ax = axes[plot_index]
            sns.scatterplot(x=valid_data[stage], y=valid_data[threshold], ax=ax, color='black', alpha=0.6)

            # 添加文本标签到左上角
            row_letter = letters[plot_index % 6]  # 计算对应的字母
            num_label = (plot_index // 6) + 1  # 计算对应的数字
            label = f'({row_letter}{num_label})'  # 组合字母和数字作为标签，并加上括号
            ax.text(0.05, 0.95, label, transform=ax.transAxes,
                    verticalalignment='top', fontsize=16, weight='bold',
                    horizontalalignment='left')  # 不使用bbox参数以去除背景和边框


            # 添加1:1线
            lims = [0, 200]  # 设置新的lims为0到200
            ax.plot(lims, lims, 'k-', alpha=0.75, zorder=0, label='1:1 Line')
            ax.set_xlim(lims)  # 设置x轴范围
            ax.set_ylim(lims)  # 设置y轴范围

            # 设置x轴和y轴的刻度间隔为50，并指定字体大小
            ax.set_xticks(np.arange(0, 201, 50))
            ax.set_yticks(np.arange(0, 201, 50))
            ax.tick_params(axis='both', which='major', labelsize=16)  # 设置坐标轴字体大小为8

            # 拟合线
            slope, intercept, r_value, p_value, std_err = linregress(valid_data[stage], valid_data[threshold])
            fit_line = slope * valid_data[stage] + intercept
            ax.plot(valid_data[stage], fit_line, 'r-', label=f'Fit Line (R²={r_value**2:.2f})')

            # 去除x轴和y轴标题
            ax.set_xlabel(' ')  # 移除x轴标题
            ax.set_ylabel(' ')  # 移除y轴标题
            #ax.set_title(f'{threshold}')
            #ax.legend()

            # 可选：在图中添加相关系数、RMSE和KGE的信息
            r, _ = pearsonr(valid_data[stage], valid_data[threshold])
            rmse = math.sqrt(mean_squared_error(valid_data[stage], valid_data[threshold]))
            bias = (valid_data[threshold] - valid_data[stage]).mean()
            var_ratio = valid_data[threshold].var() / valid_data[stage].var()
            r2 = 1 - ((valid_data[threshold] - valid_data[stage]) ** 2).sum() / ((valid_data[stage] - valid_data[stage].mean()) ** 2).sum()
            kge = 1 - math.sqrt((bias / valid_data[stage].std()) ** 2 + (var_ratio - 1) ** 2 + (1 - r2) ** 2)
            # 在图中添加相关系数、RMSE和KGE的信息，放置在右下角
            ax.text(0.95, 0.1, f'R: {r:.2f}\nRMSE: {rmse:.2f}\nKGE: {kge:.2f}',
                    transform=ax.transAxes,
                    horizontalalignment='right',
                    verticalalignment='bottom',
                    fontsize=16,  # 设置文本框内字体大小为8
                    bbox=dict(facecolor='white', alpha=0.5))

        # 如果有剩余未使用的子图，隐藏它们
    for i in range(end_index - start_index, len(axes)):
            fig.delaxes(axes[i])

    # 添加x轴和y轴的大标题
    fig.text(0.5, 0.04, 'Bud burst (DOY)', ha='center', fontsize=30,weight='bold')  # 大图x轴标签字体大小设为10
    fig.text(0.04, 0.5, 'MOD43A4 extracted SOS (DOY)', va='center', rotation='vertical', fontsize=30,weight='bold')  # 大图y轴标签字体大小设为10

    # 调整布局，确保标签不会重叠
    plt.tight_layout(rect=[0.05, 0.05, 1, 0.95])

    # 保存当前批次的大图到文件
    plt.savefig(f'F:\\pythonforR\\SOS1\\SOS_2_{batch + 1}.png', dpi=600, bbox_inches='tight')

    # 清理当前图形以释放内存
    plt.clf()
    plt.close(fig)