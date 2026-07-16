import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.stats.multitest import multipletests
import os

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号'-'显示为方块的问题


# 1. 数据准备
def load_data():
    # 读取数据并添加类群标识
    grass = pd.read_csv('F:\站点\植物物候观测数据集20161202\草转换结果2.csv', encoding='gbk')
    wood = pd.read_csv('F:\站点\植物物候观测数据集20161202\筛选后的灌木数据.csv', encoding='gbk')
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
    if '年' not in df.columns:
        df['年'] = df['时间'].str.extract(r'(\d{4})')[0].astype(float)
    return df


# 3. 基础统计分析函数
def compare_phenology(df, pheno_col):
    # 按类群分组数据
    grass_data = df[df['CLASS'] == '草'][pheno_col].dropna()
    wood_data = df[df['CLASS'] == '木'][pheno_col].dropna()

    # 计算基本统计量
    stats_results = {
        'mean_diff': grass_data.mean() - wood_data.mean(),
        'effect_size': (grass_data.mean() - wood_data.mean()) / grass_data.std(),
        'p_value': stats.mannwhitneyu(grass_data, wood_data).pvalue
    }
    return stats_results


# 可视化函数
def plot_comparison(df, pheno_columns):
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))  # 创建一个2x2的子图布局
    axes = axes.flatten()  # 将axes数组展平方便迭代

    for ax, pheno_col in zip(axes, pheno_columns):
        sns.boxplot(x='CLASS', y=pheno_col, data=df, ax=ax)
        ax.set_title(f'{pheno_col}分布比较')
        ax.set_ylabel('DOY')

    plt.tight_layout()  # 自动调整子图参数,使之填充整个图像区域。
    plt.show()


# 时间趋势分析
def analyze_temporal_trend(df, pheno_columns):
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))  # 创建一个2x2的子图布局
    axes = axes.flatten()  # 将axes数组展平方便迭代

    for ax, pheno_col in zip(axes, pheno_columns):
        trends = df.groupby(['CLASS', '年'])[pheno_col].mean().unstack()
        trends.T.plot(ax=ax, title=f'{pheno_col}年际变化')
        ax.set_ylabel('儒略日')
        ax.legend(['草', '木'])  # 确保图例正确显示

    plt.tight_layout()  # 自动调整子图参数,使之填充整个图像区域。
    plt.show()


# 6. 站点差异分析
def analyze_site_differences(df, pheno_columns):
    site_results = {}
    for site in df['生态站代码'].unique():
        site_results[site] = {}
        site_df = df[df['生态站代码'] == site]

        for pheno_col in pheno_columns:
            grass_data = site_df[site_df['CLASS'] == '草'][pheno_col].dropna()
            wood_data = site_df[site_df['CLASS'] == '木'][pheno_col].dropna()

            if len(grass_data) > 5 and len(wood_data) > 5:  # 确保足够样本量
                _, p = stats.ttest_ind(grass_data, wood_data)
                site_results[site][f'{pheno_col}_mean_diff'] = grass_data.mean() - wood_data.mean()
                site_results[site][f'{pheno_col}_p_value'] = p
            else:
                site_results[site][f'{pheno_col}_mean_diff'] = np.nan
                site_results[site][f'{pheno_col}_p_value'] = np.nan

    # 将字典转换为DataFrame
    results_df = pd.DataFrame.from_dict(site_results, orient='index')
    return results_df


def analyze_phenology_correlations(df):
    """
    分析不同类群物候期之间的相关性差异
    使用pairplot展示关系分布，clustermap展示相关性模式
    """
    # 准备数据：分别提取草、木类群数据
    grass_df = df[df['CLASS'] == '草'].copy()
    wood_df = df[df['CLASS'] == '木'].copy()

    # 定义分析的物候期列（与之前保持一致）
    pheno_columns = [
        '叶芽开始膨大期', '叶芽开放期', '花芽开始膨大期',
        '花芽开放期', '开始展叶期', '展叶盛期',
        '花序或花蕾出现期', '开花始期', '开花盛期',
        '开花末期', '第二次开花期', '果实成熟期',
        '果实脱落开始期', '果实脱落末期', '叶开始变色期',
        '叶全部变色期', '开始落叶期', '落叶末期'
    ]

    # 简化列名便于显示
    short_names = {
        '萌动期（DOY）': '萌动期',
        '开花期（DOY）': '开花期',
        '果实或种子成熟期（DOY）': '成熟期',
        '黄枯期（DOY）': '黄枯期'
    }

    # 对两个类群分别进行分析
    for type_name, data in [('草本', grass_df), ('木本', wood_df)]:
        plt.figure(figsize=(10, 8))

        # 1. 绘制散点图矩阵
        print(f"\n{type_name}物候期散点图矩阵：")
        sns.pairplot(data[pheno_columns].dropna(),
                     plot_kws={'alpha': 0.5},
                     height=2.5)
        plt.suptitle(f'{type_name}物候期关系分布', y=1.02)
        plt.show()

        # 2. 计算相关系数矩阵
        corr_matrix = data[pheno_columns].corr(method='spearman')

        # 3. 绘制聚类热图
        plt.figure(figsize=(10, 8))
        cmap = sns.diverging_palette(220, 10, as_cmap=True)
        clustergrid = sns.clustermap(corr_matrix.rename(columns=short_names, index=short_names),
                                     cmap=cmap,
                                     annot=True,
                                     fmt=".2f",
                                     vmin=-1, vmax=1,
                                     figsize=(10, 10))
        clustergrid.ax_heatmap.set_title(f'{type_name}物候期相关性聚类图')
        plt.show()

        # 4. 打印强相关关系（|r| > 0.7）
        strong_corr = corr_matrix.unstack().sort_values(ascending=False)
        strong_corr = strong_corr[abs(strong_corr) > 0.7]
        strong_corr = strong_corr[strong_corr < 1]  # 排除自相关
        print(f"\n{type_name}强相关关系（|r|>0.7）：")
        print(strong_corr.reset_index().rename(columns={'level_0': '物候期1', 'level_1': '物候期2', 0: '相关系数'}))

def plot_phenology_difference_proportion(df, pheno_columns):
    """
    计算每个站点草本与灌木的物候差值，并绘制比例图。
    横坐标为“灌丛物候更早”和“草本物候更早”，纵坐标为对应的比例。
    """
    # 初始化结果存储
    site_diff_counts = []

    for site in df['生态站代码'].unique():
        site_df = df[df['生态站代码'] == site]

        # 初始化计数器
        wood_earlier_count = 0
        grass_earlier_count = 0

        for pheno_col in pheno_columns:
            grass_data = site_df[site_df['CLASS'] == '草'][pheno_col].dropna()
            wood_data = site_df[site_df['CLASS'] == '木'][pheno_col].dropna()

            if len(grass_data) > 0 and len(wood_data) > 0:
                # 计算草本和灌木的均值差异
                mean_diff = grass_data.mean() - wood_data.mean()

                if mean_diff > 0:  # 灌木物候更早
                    wood_earlier_count += 1
                elif mean_diff < 0:  # 草本物候更早
                    grass_earlier_count += 1

        # 存储站点的结果
        total_comparisons = wood_earlier_count + grass_earlier_count
        if total_comparisons > 0:
            site_diff_counts.append({
                'site': site,
                'wood_earlier_ratio': wood_earlier_count / total_comparisons,
                'grass_earlier_ratio': grass_earlier_count / total_comparisons
            })

    # 将结果转换为DataFrame
    diff_counts_df = pd.DataFrame(site_diff_counts)

    # 绘制比例图
    plt.figure(figsize=(10, 6))

    # 定义横坐标标签
    categories = ['灌丛物候更早', '草本物候更早']
    bar_width = 0.35

    # 计算平均比例
    avg_wood_earlier_ratio = diff_counts_df['wood_earlier_ratio'].mean()
    avg_grass_earlier_ratio = diff_counts_df['grass_earlier_ratio'].mean()

    # 绘制柱状图
    plt.bar(categories, [avg_wood_earlier_ratio, avg_grass_earlier_ratio], color=['skyblue', 'lightgreen'])

    # 添加数值标注
    for i, value in enumerate([avg_wood_earlier_ratio, avg_grass_earlier_ratio]):
        plt.text(i, value + 0.02, f'{value:.2f}', ha='center', fontsize=10)

    # 添加标题和标签
    plt.title('各站点草本与灌木物候期差异比例')
    plt.ylabel('比例')
    plt.ylim(0, 1)

    plt.show()


def main_analysis():
    df = load_data()
    df = preprocess(df)

    pheno_columns = [
        '萌动期（DOY）',
        '开花期（DOY）',
        '果实或种子成熟期（DOY）',
        '黄枯期（DOY）'
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
    combined_results.to_csv('D:\glass_vswd\combined_analysis_results.csv', encoding='gbk')

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