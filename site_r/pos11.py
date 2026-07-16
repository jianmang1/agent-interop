import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, linregress
from sklearn.metrics import mean_squared_error
import math
import pandas as pd
import numpy as np

# 读取CSV数据
df = pd.read_csv('F:\pythonforR\POS\EPSG\\pos_nosjm.csv')

# 定义实际观测列的列表
acture3 = ['flower', 'fruit']

# 定义阈值列的前缀列表
threshold_prefixes = ['cublic', 'doublelogistic', ' nonsmooth']  # 注意这里修正了'nonsmooth'的拼写错误

# 定义方法列表
meth = ['NDVI', 'EVI', 'EVI2', 'NDPI', 'NDGI']

# 构建所有可能的阈值列名并筛选出存在的列
all_threshold_columns = [f"POS_{prefix}{method}" for prefix in threshold_prefixes for method in meth]
existing_threshold_columns = [col for col in all_threshold_columns if col in df.columns]

# 计算总批次数量
num_plots = len(acture3) * len(existing_threshold_columns)
batch_size = 15  # 每批次中的子图数量
total_batches = math.ceil(num_plots / batch_size)

# 设置全局字体为Arial
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 8  # 设置默认字体大小

# 将宽度从毫米转换为英寸
fig_width_inch = 580 / 25.4  # 转换为英寸
fig_height_per_row = 4  # 每行的高度
rows_per_batch = 3  # 每批次的行数

# 数据清理函数
def clean_numeric(data):
    return pd.to_numeric(data, errors='coerce')

for batch in range(total_batches):
    start_index = batch * batch_size
    end_index = min((batch + 1) * batch_size, num_plots)

    # 动态调整图形高度
    fig_height_inch = rows_per_batch * fig_height_per_row
    fig, axes = plt.subplots(rows_per_batch, 5, figsize=(fig_width_inch, fig_height_inch),
                             constrained_layout=False, gridspec_kw={'wspace': 0.3, 'hspace': 0.4})

    # 如果只有单行或单列，则将 axes 转换为二维数组
    if len(meth) == 1:
        axes = axes.reshape(1, -1)

    # 展平 axes 以便按索引访问
    axes = axes.flatten()

    for i in range(start_index, end_index):
        plot_index = i - start_index
        global_plot_index = i
        stage = acture3[global_plot_index // len(existing_threshold_columns)]
        threshold = existing_threshold_columns[global_plot_index % len(existing_threshold_columns)]

        # 筛选有效数据并进行数值清理
        valid_data = df.dropna(subset=[stage, threshold])
        valid_data[stage] = clean_numeric(valid_data[stage])
        valid_data[threshold] = clean_numeric(valid_data[threshold])

        # 进一步移除包含 NaN 的行
        valid_data = valid_data.dropna(subset=[stage, threshold])

        if not valid_data.empty:
            ax = axes[plot_index]
            sns.scatterplot(x=valid_data[stage], y=valid_data[threshold], ax=ax, color='black', alpha=0.6)

            # 添加1:1线
            lims = [150, 260]
            ax.plot(lims, lims, 'k-', alpha=0.75, zorder=0, label='1:1 Line')
            ax.set_xlim(lims)
            ax.set_ylim(lims)

            # 设置x轴和y轴的刻度间隔为50，并指定字体大小
            ax.set_xticks(np.arange(150, 260, 50))
            ax.set_yticks(np.arange(150, 260, 50))
            ax.tick_params(axis='both', which='major', labelsize=16)

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
                    fontsize=16,
                    bbox=dict(facecolor='white', alpha=0.5))
    # 在循环绘制子图的部分添加以下代码：

    # 计算当前子图在批次内的行和列
    row_in_batch = plot_index // 5  # 每行5个子图
    col_in_batch = plot_index % 5  # 列号0-4
    letter = ['a', 'b', 'c'][row_in_batch]  # 每行对应一个字母
    number = col_in_batch + 1  # 列号转1-5

    # 添加子图标签
    label = f'({letter}{number})'
    ax.text(0.05, 0.95, label,
            transform=ax.transAxes,
            verticalalignment='top',
            horizontalalignment='left',
            fontsize=16,  # 调整为与您的字体比例协调
            weight='bold')
    # 如果有剩余未使用的子图，隐藏它们
    for i in range(end_index - start_index, len(axes)):
        fig.delaxes(axes[i])

    # 动态设置大图标题为 acture3 的当前阶段名称
    current_stage = acture3[batch // len(existing_threshold_columns) % len(acture3)]
    fig.suptitle(f'{current_stage} (DOY)', fontsize=30, weight='bold')

    # 添加大图的Y轴坐标（基于新的描述）
    y_labels = ['no processing', 'self-weighted double-logistic function fitting', 'polynomial fitting']
    for idx, label in enumerate(y_labels):
        fig.text(0.07, 0.8 - (idx * 0.3), label, va='center', rotation='vertical', fontsize=16, weight='bold')

    # 添加大图的X轴坐标（固定位置）
    x_ticks_positions = ['NDGI','NDPI','EVI2', 'EVI', 'NDVI']
    for idx, pos in enumerate(x_ticks_positions):
        fig.text(0.85 - (idx * 0.17), 0.07, str(pos), ha='center', fontsize=16, weight='bold')

    # 保存当前批次的大图到文件
    plt.savefig(f'D:\\GEE(PYTHON)\\YANZHEN\\pos\\POS_scatter_plots_withoutsjm_batchEPSG_{batch + 1}.png', dpi=600,
                bbox_inches='tight')
    plt.clf()
    plt.close(fig)