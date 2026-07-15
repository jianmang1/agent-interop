import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据（假设路径和数据正确）
grass_mean = pd.read_csv('F:\\站点\\中国地面\\草本数据_每年均值.csv', encoding='gbk')
wood_mean = pd.read_csv('F:\\站点\\中国地面\\灌本数据_每年均值.csv', encoding='gbk')

sites_of_interest = ['泰安', '民勤', '哈尔滨', '银川', '牡丹江', '北京', '长春']
pheno_columns = [
    'LOS', '开始展叶期', '展叶盛期',
    '花序或花蕾出现期', '开花始期', '开花盛期',
    '开花末期', '果实成熟期',
    '果实脱落开始期', '果实脱落末期', '叶开始变色期',
    '叶全部变色期'
]

grass_filtered = grass_mean[grass_mean['站点'].isin(sites_of_interest)]
wood_filtered = wood_mean[wood_mean['站点'].isin(sites_of_interest)]


def plot_scatter_with_fit(df, title):
    fig, axes = plt.subplots(nrows=4, ncols=3, figsize=(15, 20))
    num_phenos = len(pheno_columns)

    for i, pheno in enumerate(pheno_columns):
        ax = axes[i // 3, i % 3]
        all_x, all_y = [], []

        for site in sites_of_interest:
            site_data = df[df['站点'] == site]
            valid_data = site_data[['lastyear_LOS', pheno]].dropna()
            valid_data = valid_data[np.isfinite(valid_data).all(axis=1)]

            if not valid_data.empty:
                x = valid_data['lastyear_LOS']
                y = valid_data[pheno]
                all_x.extend(x)
                all_y.extend(y)

                # 控制图例显示
                if i == num_phenos - 1:  # 最后一张小图显示站点图例
                    ax.scatter(x, y, label=site, alpha=0.7)
                else:
                    ax.scatter(x, y, label='_nolegend_', alpha=0.7)  # 其他小图不显示站点图例

        # 拟合曲线
        if len(all_x) > 1:
            slope, intercept, r_value, _, _ = linregress(all_x, all_y)
            fit_line_x = np.linspace(min(all_x), max(all_x), 100)
            fit_line_y = slope * fit_line_x + intercept
            ax.plot(fit_line_x, fit_line_y, color='red', linestyle='--',
                    label=f'Fit ($R^2$={r_value ** 2:.2f}, slope={slope:.2f})')

        ax.set_title(f'{title} - {pheno}')
        ax.set_ylabel(pheno)

        # 控制图例显示
        if i == num_phenos - 1:  # 最后一张小图显示站点和拟合曲线图例
            ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))  # 调整位置避免遮挡
        else:  # 其他小图仅显示拟合曲线图例
            handles, labels = ax.get_legend_handles_labels()
            fit_handle = [h for h, l in zip(handles, labels) if 'Fit' in l]
            fit_label = [l for l in labels if 'Fit' in l]
            ax.legend(fit_handle, fit_label, loc='upper right')

    # 移除多余子图
    if num_phenos < axes.size:
        for i in range(num_phenos, axes.size):
            fig.delaxes(axes.flatten()[i])

    # 设置x轴标签
    for ax in axes[-1, :]:
        ax.set_xlabel('lastyear_LOS')

    plt.tight_layout()
    plt.show()


# 绘制图表
plot_scatter_with_fit(grass_filtered, '草本数据')
plot_scatter_with_fit(wood_filtered, '灌木数据')



