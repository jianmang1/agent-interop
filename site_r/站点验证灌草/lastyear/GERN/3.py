import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据（假设路径和数据正确）
grass_mean = pd.read_csv('F:\站点\植物物候观测数据集20161202\\草本数据_每年均值.csv', encoding='gbk')
wood_mean = pd.read_csv('F:\站点\植物物候观测数据集20161202\\灌本数据_每年均值.csv', encoding='gbk')

sites_of_interest = [
    '北京站综合观测场上土壤生物水分采样地',
    '北京站综合观测场长期观测采样地',
    '北京站辅助观测场土壤生物水分采样地I',
    '北京站综合观测场土壤生物水分采样地',
    '北京站辅助观测场土壤生物水分采样地II',
    '北京站油松林辅助观测场I土壤生物水分采样地',
    '北京站站区调查点',
    '北京站落叶松林辅助观测场II土壤生物水分采样地',
    '北京森林站油松林辅助观测场I土壤生物水分采样地',
    '北京森林站综合观测场土壤生物水分采样地',
    '北京森林站站区调查点',
    '北京森林站落叶松林辅助观测场II土壤生物水分采样地',
    '策勒荒漠综合观测场土壤生物采样地',
    '策勒荒漠辅助观测场（四）土壤生物要素长期观测采样地',
    '固定沙地油蒿灌丛',
    '综合观测场',
    '鄂尔多斯站综合观测场水土生联合长期观测采样地',
    '阜康站荒漠综合观测场',
    '阜康站荒漠辅助观测场（1）土壤生物要素长期观测采样地',
    '阜康站荒漠辅助观测场（2）土壤生物要素长期观测采样地',
    '荒漠生态系统土壤生物采样地',
    '荒漠生态系统综合观测场土壤生物采样地',
    '临泽站荒漠生态系统综合观测场土壤生物采样地',
    '奈曼固定沙丘辅助观测场生物土壤长期采样地',
    '油蒿群落',
    '沙坡头站人工植被演替综合观测场生物土壤长期采样地',
    '沙坡头站天然植被演替辅助观测场生物土壤长期采样地'
]
pheno_columns = ['LOS', 'Budburst', 'Flower', 'Fruit', 'Coloration']

grass_filtered = grass_mean[grass_mean['站点'].isin(sites_of_interest)]
wood_filtered = wood_mean[wood_mean['站点'].isin(sites_of_interest)]


def plot_scatter_with_fit(df, title):
    fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(18, 8))
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



