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
   '开始展叶期', '展叶盛期'
]

grass_filtered = grass_mean[grass_mean['站点'].isin(sites_of_interest)]
wood_filtered = wood_mean[wood_mean['站点'].isin(sites_of_interest)]


def plot_scatter_with_fit(df, title):
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 12))
    num_phenos = len(pheno_columns)

    colors = plt.cm.tab10.colors  # 使用tab10调色板

    for i, pheno in enumerate(pheno_columns):
        ax = axes[i]
        all_x, all_y = [], []

        for j, site in enumerate(sites_of_interest):
            site_data = df[df['站点'] == site]
            valid_data = site_data[['lastyear_LOS', pheno]].dropna()
            valid_data = valid_data[np.isfinite(valid_data).all(axis=1)]

            if not valid_data.empty:
                x = valid_data['lastyear_LOS']
                y = valid_data[pheno]
                all_x.extend(x)
                all_y.extend(y)

                # 控制图例显示
                ax.scatter(x, y, label=site, color=colors[j], alpha=0.7)

                # 拟合曲线
                slope, intercept, r_value, _, _ = linregress(x, y)
                fit_line_x = np.linspace(min(x), max(x), 100)
                fit_line_y = slope * fit_line_x + intercept
                ax.plot(fit_line_x, fit_line_y, color=colors[j], linestyle='--',
                        label=f'{site} Fit ($R^2$={r_value ** 2:.2f}, slope={slope:.2f})')

        ax.set_title(f'{title} - {pheno}')
        ax.set_ylabel(pheno)

        # 控制图例显示
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))  # 调整位置避免遮挡

    # 设置x轴标签
    for ax in axes[-1:]:
        ax.set_xlabel('lastyear_LOS')

    plt.tight_layout()
    plt.show()


# 绘制图表
plot_scatter_with_fit(grass_filtered, '草本数据')
plot_scatter_with_fit(wood_filtered, '灌木数据')



