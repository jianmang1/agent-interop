import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.stats.multitest import multipletests
import os
from scipy.stats import ttest_ind

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号'-'显示为方块的问题


# 1. 数据准备
def load_data():
    # 读取数据并添加类群标识
    grass = pd.read_csv(r'F:\站点\中国地面\筛选后的草本数据(ioa)2.csv', encoding='gbk')
    wood = pd.read_csv(r'F:\站点\中国地面\筛选后的灌木数据(ioa)2.csv', encoding='gbk')
    grass['CLASS'] = '草'
    wood['CLASS'] = '木'
    df = pd.concat([grass, wood], ignore_index=True)
    return df


# 2. 数据预处理
def preprocess(df):
    # 转换日期列为数值类型（假设儒略日列已存在）
    pheno_columns = [
        '叶芽开始膨大期', '叶芽开放期', '花芽开始膨大期',
        '花芽开放期', '开始展叶期', '展叶盛期',
        '花序或花蕾出现期', '开花始期', '开花盛期',
        '开花末期', '第二次开花期', '果实成熟期',
        '果实脱落开始期', '果实脱落末期', '叶开始变色期',
        '叶全部变色期', '开始落叶期', '落叶末期'
    ]

    # 处理缺失值
    df[pheno_columns] = df[pheno_columns].apply(pd.to_numeric, errors='coerce')

    # 添加年份列（假设存在年列）
    if '年份' not in df.columns:
        df['年份'] = df['时间'].str.extract(r'(\d{4})')[0].astype(float)
    return df


# 3. 比较物候期
def compare_phenology(df, column):
    grass_values = df[df['CLASS'] == '草'][column].dropna()
    wood_values = df[df['CLASS'] == '木'][column].dropna()

    mean_diff = grass_values.mean() - wood_values.mean()
    effect_size = cohen_d(grass_values, wood_values)
    t_stat, p_value = ttest_ind(grass_values, wood_values, nan_policy='omit')

    return {'mean_diff': mean_diff, 'effect_size': effect_size, 't_stat': t_stat, 'p_value': p_value}


# 4. 计算Cohen's d效应量
def cohen_d(x, y):
    nx = len(x)
    ny = len(y)
    dof = nx + ny - 2
    return (np.mean(x) - np.mean(y)) / np.sqrt(((nx-1)*np.std(x, ddof=1) ** 2 + (ny-1)*np.std(y, ddof=1) ** 2) / dof)


# 5. 站点差异分析
def analyze_site_differences(df, columns):
    site_results = {}
    for col in columns:
        site_df = df.pivot_table(values=col, index='站点', columns='CLASS', aggfunc='mean').dropna()
        site_df['diff'] = site_df['草'] - site_df['木']
        site_df['significant'] = [ttest_ind(df[(df['站点'] == s) & (df['CLASS'] == '草')][col],
                                           df[(df['站点'] == s) & (df['CLASS'] == '木')][col]).pvalue < 0.05
                                 for s in site_df.index]
        site_results[col] = site_df[['diff', 'significant']]
    return pd.concat(site_results.values(), keys=site_results.keys(), axis=1)


# 6. 绘制比较图
def plot_comparison(df, columns):
    fig, axes = plt.subplots(nrows=len(columns), ncols=1, figsize=(12, 8 * len(columns)), sharex=True)
    for ax, col in zip(axes, columns):
        sns.boxplot(data=df, x='CLASS', y=col, ax=ax)
        add_significance_lines(ax, col)
        ax.set_title(f'{col} 物候期对比')
        ax.set_ylabel('')
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()


# 7. 添加显著性标记
def add_significance_lines(ax, column):
    stat = ttest_ind(df[df['CLASS'] == '草'][column], df[df['CLASS'] == '木'][column])
    y_max = max(ax.get_ylim())
    hline_offset = 0.02
    star_height = y_max + hline_offset
    bar_width = 0.05
    text_y_pos = star_height + hline_offset
    if stat.pvalue < 0.001:
        stars = '***'
    elif stat.pvalue < 0.01:
        stars = '**'
    elif stat.pvalue < 0.05:
        stars = '*'
    else:
        stars = ''

    ax.plot([bar_width, 1-bar_width], [star_height, star_height], color='black', lw=1)
    ax.text(0.5, text_y_pos, stars, ha='center', va='bottom', fontsize=12)


# 8. 时间趋势分析
def analyze_temporal_trend(df, columns):
    trends = {}
    for col in columns:
        trend_grass = stats.linregress(df[df['CLASS'] == '草']['年份'], df[df['CLASS'] == '草'][col])
        trend_wood = stats.linregress(df[df['CLASS'] == '木']['年份'], df[df['CLASS'] == '木'][col])
        trends[col] = {'grass_slope': trend_grass.slope, 'wood_slope': trend_wood.slope,
                       'grass_pvalue': trend_grass.pvalue, 'wood_pvalue': trend_wood.pvalue}
    return pd.DataFrame(trends)


# 9. 相关性分析
def analyze_phenology_correlations(df):
    correlations = df.corr().loc[pheno_columns, pheno_columns]
    mask = np.triu(np.ones_like(correlations, dtype=bool))
    plt.figure(figsize=(12, 10))
    sns.heatmap(correlations, annot=True, fmt=".2f", cmap='coolwarm', mask=mask, square=True)
    plt.title('物候期相关性热力图')
    plt.show()


# 10. 绘制物候差值比例图
def plot_phenology_difference_proportion(df, columns):
    differences = {col: df[df['CLASS'] == '草'][col].mean() - df[df['CLASS'] == '木'][col].mean() for col in columns}
    diff_series = pd.Series(differences).sort_values()
    diff_series.plot(kind='barh', figsize=(10, 8), colormap='viridis')
    plt.title('草本与灌木物候期差异比例')
    plt.xlabel('天数差异')
    plt.ylabel('物候期')
    plt.axvline(0, color='red', linestyle='--')
    plt.show()


def main_analysis():
    df = load_data()
    df = preprocess(df)

    # 定义需要分析的站点列表，即既有草又有灌
    sites_of_interest = ['长春', '民勤', '哈尔滨', '牡丹江', '盖州', '沈阳', '伊春', '北京', '银川']
    df = df[df['站点'].isin(sites_of_interest)]

    # 调用函数进行分
    pheno_columns = [
        '叶芽开始膨大期', '叶芽开放期', '花芽开始膨大期',
        '花芽开放期', '开始展叶期', '展叶盛期',
        '花序或花蕾出现期', '开花始期', '开花盛期',
        '开花末期', '第二次开花期', '果实成熟期',
        '果实脱落开始期', '果实脱落末期', '叶开始变色期',
        '叶全部变色期', '开始落叶期', '落叶末期'
    ]

    # 全局差异分析
    results = []
    for col in pheno_columns:
        res = compare_phenology(df, col)
        res['pheno'] = col
        results.append(res)

    results_df = pd.DataFrame(results)
    _, p_adjusted, _, _ = multipletests(results_df['p_value'], method='fdr_bh')
    results_df['p_adjusted'] = p_adjusted

    # 站点差异分析
    site_results_df = analyze_site_differences(df, pheno_columns)

    # 将全局差异分析结果转换为宽表形式以便于合并
    global_results_wide = results_df.set_index('pheno').add_prefix('global_')

    # 合并全局差异分析结果和站点差异分析结果
    combined_results = pd.concat([global_results_wide, site_results_df], axis=1)

    # 导出为CSV
    combined_results.to_csv(r'D:\glass_vswd\中国地面combined_analysis_results.csv', encoding='gbk')

    print("全局差异分析结果:")
    print(results_df[['pheno', 'mean_diff', 'effect_size', 'p_value', 'p_adjusted']])

    # 调用修改后的可视化函数
    plot_comparison(df, pheno_columns)

    # 调用修改后的时间趋势分析函数
    analyze_temporal_trend(df, pheno_columns)

    # 输出站点差异分析结果
    print("\n站点差异分析结果:")
    print(site_results_df)

    # 新增相关性分析
    print("\n正在进行物候期相关性分析...")
    analyze_phenology_correlations(df)

    # 新增物候差值比例图
    print("\n绘制草本与灌木物候期差异比例图...")
    plot_phenology_difference_proportion(df, pheno_columns)


if __name__ == '__main__':
    main_analysis()



