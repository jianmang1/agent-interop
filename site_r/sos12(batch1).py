import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, linregress
from sklearn.metrics import mean_squared_error
import math
import pandas as pd
import numpy as np

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

# 构建所有可能的阈值列名并筛选出存在的列
all_threshold_columns1 = [f"{prefix}{method}_{i}" for prefix in threshold_prefixes for method in meth for i in
                          [5, 1, 13, 2, 21, 3]]
all_threshold_columns2 = [f"{prefix}EVT{method}" for prefix in threshold_prefixes for method in meth]
all_threshold_columns = all_threshold_columns1 + all_threshold_columns2
existing_threshold_columns = [col for col in all_threshold_columns if col in df.columns]

# 计算总批次数量
num_plots = len(acture3) * len(existing_threshold_columns)
batch_size = 30  # 每批次中的子图数量
total_batches = math.ceil(num_plots / batch_size)

## 设置全局字体为Arial
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 8  # 设置默认字体大小

# 将宽度从毫米转换为英寸
fig_width_inch = 580 / 25.4  # 转换为英寸
fig_height_inch = len(meth) * 4  # 增加高度以便为每个子图提供更多空间

for batch in range(total_batches):

    start_index = batch * batch_size
    end_index = min((batch + 1) * batch_size, num_plots)

    fig, axes = plt.subplots(len(meth), 6, figsize=(fig_width_inch, fig_height_inch),
                             constrained_layout=False, gridspec_kw={'wspace': 0.3, 'hspace': 0.4})
    axes = axes.flatten() if len(meth) > 1 else list(axes)  # 将子图轴展平为一维数组或保持为列表以适应单行情况
    letters = ['a', 'b', 'c', 'd', 'e', 'f']  # 定义字母列表

    for i in range(start_index, end_index):
        plot_index = i - start_index
        global_plot_index = i
        stage = acture3[global_plot_index // len(existing_threshold_columns)]
        threshold = existing_threshold_columns[global_plot_index % len(existing_threshold_columns)]

        valid_data = df.dropna(subset=[stage, threshold])

        if not valid_data.empty:
            ax = axes[plot_index]
            sns.scatterplot(x=valid_data[stage], y=valid_data[threshold], ax=ax, color='black', alpha=0.6)

            # 添加文本标签到左上角
            row_letter = letters[plot_index // 6]  # 计算对应的字母（按行分配）
            num_label = plot_index % 6 + 1  # 计算对应的数字（按列分配）
            label = f'({row_letter}{num_label})'  # 组合字母和数字作为标签
            ax.text(0.05, 0.95, label, transform=ax.transAxes,
                    verticalalignment='top', fontsize=24, weight='bold',
                    horizontalalignment='left')  # 不使用bbox参数以去除背景和边框

            # 添加1:1线
            lims = [0, 200]
            ax.plot(lims, lims, 'k-', alpha=0.75, zorder=0, label='1:1 Line')
            ax.set_xlim(lims)
            ax.set_ylim(lims)

            # 设置x轴和y轴的刻度间隔为50，并指定字体大小
            ax.set_xticks(np.arange(0, 201, 50))
            ax.set_yticks(np.arange(0, 201, 50))
            ax.tick_params(axis='both', which='major', labelsize=24)

            # 拟合线
            slope, intercept, r_value, p_value, std_err = linregress(valid_data[stage], valid_data[threshold])
            fit_line = slope * valid_data[stage] + intercept
            ax.plot(valid_data[stage], fit_line, 'r-', label=f'Fit Line (R²={r_value ** 2:.2f})')

            # 在图中添加相关系数、RMSE的信息
            r, _ = pearsonr(valid_data[stage], valid_data[threshold])
            rmse = math.sqrt(mean_squared_error(valid_data[stage], valid_data[threshold]))
            ax.text(0.95, 0.1, f'R: {r:.2f}\nRMSE: {rmse:.2f}',
                    transform=ax.transAxes,
                    horizontalalignment='right',
                    verticalalignment='bottom',
                    fontsize=24,
                    bbox=dict(facecolor='white', alpha=0.5))

            # 移除x轴和y轴标题
            ax.set_xlabel('')
            ax.set_ylabel('')

    # 如果有剩余未使用的子图，隐藏它们
    for i in range(end_index - start_index, len(axes)):
        fig.delaxes(axes[i])

    # 添加大图的大标题Threshold
    fig.text(0.5, 0.06, 'Bud burst (DOY)', ha='center', fontsize=30, weight='bold')
    fig.text(0.04, 0.5, 'MOD43A4 SOS (DOY)', va='center', rotation='vertical', fontsize=30, weight='bold')
    fig.text(0.5, 0.92, 'Threshold', ha='center', fontsize=30, weight='bold')

    # 添加大图的Y轴坐标（基于meth）
    for idx, method in enumerate(meth):
        fig.text(0.07, 0.8 - (idx * 0.16), method, va='center', rotation='vertical', fontsize=24, weight='bold')

    # 添加大图的X轴坐标（固定位置）
    x_ticks_positions = [0.3, 0.25, 0.2, 0.15, 0.1, 0.05]
    for idx, pos in enumerate(x_ticks_positions):
        fig.text(0.85 - (idx * 0.135), 0.9, str(pos), ha='center', fontsize=24, weight='bold')

    # 保存当前批次的大图到文件
    plt.savefig(f'F:\\pythonforR\\sos3\\SOS_scatter_plots_withoutsjm_batch2_{batch + 1}.png', dpi=600, bbox_inches='tight')
    plt.clf()
    plt.close(fig)