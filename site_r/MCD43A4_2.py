import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression

# 设置matplotlib使用Times New Roman字体及字体大小
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 8

# 定义计算函数
def calculate_stats(valid_data, x_col, y_col):
    # 删除包含 NaN 或 inf 的行
    valid_data = valid_data.replace([np.inf, -np.inf], np.nan).dropna(subset=[x_col, y_col])

    if valid_data.empty:
        raise ValueError("No valid data after removing NaN and inf values.")

    r, p_value = pearsonr(valid_data[x_col], valid_data[y_col])
    rmse = np.sqrt(mean_squared_error(valid_data[x_col], valid_data[y_col]))
    n = len(valid_data)
    return {'R': r, 'P': p_value, 'RMSE': rmse, 'N': n}

# 定义绘图函数
def plot_subplot(ax, df, x_col, y_col, title, stats, legend_title=None, legend_text='', show_site_legend=False, equal_axes=False):
    # 删除包含 NaN 或 inf 的行
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=[x_col, y_col])

    if df.empty:
        raise ValueError("No valid data after removing NaN and inf values.")

    sns.scatterplot(data=df, x=x_col, y=y_col, hue='Site', palette='viridis', s=30, ax=ax)  # 调整散点大小
    if show_site_legend:
        ax.legend(title=legend_title, title_fontsize=8, fontsize=8, loc='upper center', bbox_to_anchor=(0.5, -0.1),
                  ncol=3, frameon=False)  # 固定图例位置
    else:
        ax.legend([], [], frameon=False)  # 清除图例
        if legend_title is not None:
            ax.text(1.1, 0.5, legend_title, transform=ax.transAxes, fontsize=8, verticalalignment='center',
                    horizontalalignment='left')  # 添加自定义图例标题

    # 处理P值显示格式
    if stats['P'] < 0.001:
        p_display = "p < 0.001"
    elif stats['P'] < 0.01:
        p_display = "p < 0.01"
    elif stats['P'] < 0.05:
        p_display = "p < 0.05"
    else:
        p_display = f"p: {stats['P']:.3f}"

    text_str = f"R: {stats['R']:.2f}\n{p_display}\nRMSE: {stats['RMSE']:.2f}\nN: {stats['N']}"
    ax.text(0.05, 0.95, text_str, transform=ax.transAxes, fontsize=8, verticalalignment='top',
            bbox=dict(facecolor='white', alpha=0.5, boxstyle='square,pad=0', edgecolor='none'))

    x = df[x_col].values.reshape(-1, 1)
    y = df[y_col].values
    model = LinearRegression().fit(x, y)
    y_pred = model.predict(x)
    ax.plot(x, y_pred, color='red', label='Fit Line', linewidth=1)

    lims = [np.min([0, 0]), np.max([360, 360])]
    ax.plot(lims, lims, 'k--', label='1:1 Line', linewidth=1)

    if equal_axes:
        ax.set_xlim(lims)
        ax.set_ylim(lims)

    ax.set_title(title, fontsize=8)
    ax.tick_params(labelsize=8)
    ax.set_xlabel('')  # 移除x轴标题
    ax.set_ylabel('')  # 移除y轴标题

# 创建画布，宽度为170mm（约6.69英寸），高度保持不变
fig, axs = plt.subplots(1, 3, figsize=(6.69, 2.8))

# 第一个子图
df1 = pd.read_csv(r'F:\pythonforR\sos3\sossite.csv')
valid_data1 = df1[['Budburst', 'filtercubic_SoS_threshold_NDPI_1']]
stats1 = calculate_stats(valid_data1, 'Budburst', 'filtercubic_SoS_threshold_NDPI_1')
plot_subplot(axs[0], df1, 'Budburst', 'filtercubic_SoS_threshold_NDPI_1', 'SOS', stats1, legend_title=None, show_site_legend=False)
fig.text(0.15, 0.29, 'Budburst (DOY)', fontsize=8, horizontalalignment='left')  # 调整x坐标值以匹配子图的位置
axs[0].set_xlim(50, 150)
axs[0].set_ylim(50, 150)
axs[0].set_xticks(np.arange(50, 160, 50))
axs[0].set_yticks(np.arange(50, 160, 50))


# 第三个子图
df2 = pd.read_csv(r'F:\pythonforR\EoS_yanzhen4\1.csv')
valid_data2 = df2[['EOS', 'EoS_filterdoublelogistic_threshold_EVI2_7']]
stats2 = calculate_stats(valid_data2, 'EOS', 'EoS_filterdoublelogistic_threshold_EVI2_7')
plot_subplot(axs[1], df2, 'EOS', 'EoS_filterdoublelogistic_threshold_EVI2_7', 'EOS', stats2, legend_title='Leaf colouring (DOY)', show_site_legend=True)
axs[1].set_xlim(200, 350)
axs[1].set_ylim(200, 350)
axs[1].set_xticks(np.arange(200, 351, 50))
axs[1].set_yticks(np.arange(200, 351, 50))

# 第二个子图
df3 = pd.read_csv(r'F:\pythonforR\LOS\1.csv')
valid_data3 = df3[['LOS', 'fit_LOS']]
stats3 = calculate_stats(valid_data3, 'LOS', 'fit_LOS')
plot_subplot(axs[2], df3, 'LOS', 'fit_LOS', 'LOS', stats3, legend_title=None, show_site_legend=False)
fig.text(0.85, 0.29, 'LOS (DOY)', fontsize=8, horizontalalignment='right')  # 调整x坐标值以匹配子图的位置
axs[2].set_xlim(100, 250)
axs[2].set_ylim(100, 250)
axs[2].set_xticks(np.arange(100, 251, 50))
axs[2].set_yticks(np.arange(100, 251, 50))

# 设置大图的x轴和y轴标题
fig.supylabel('MCD43A4  Extracted (DOY)', fontsize=8, y=0.65)  # 调整y轴标题的位置

# 调整布局
plt.tight_layout(rect=[0, 0.08, 1, 1])  # 留出更多空间给图例
plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.4, wspace=0.25)

# 保存图像，指定路径和文件名以及dpi=600
output_path = 'D:\\GEE(PYTHON)\\site_r\\mcd43a4.png'  # 更换为实际需要保存的位置和文件名
plt.savefig(output_path, dpi=600, bbox_inches='tight')

# 显示图形
plt.show()



