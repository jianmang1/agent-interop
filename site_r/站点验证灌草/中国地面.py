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
    grass = pd.read_csv('F:\\站点\\中国地面\\筛选后的草本数据(ioa)2.csv', encoding='gbk')
    wood = pd.read_csv('F:\\站点\\中国地面\\筛选后的灌本数据(ioa)2.csv', encoding='gbk')
    grass['CLASS'] = '草'
    wood['CLASS'] = '木'
    df = pd.concat([grass, wood], ignore_index=True)
    print(df)

    return df


# 2. 数据预处理
def preprocess(df):
    # 转换日期列为数值类型（假设儒略日列已存在）
    pheno_columns = [
        '开始展叶期', '展叶盛期',
        '花序或花蕾出现期', '开花始期', '开花盛期',
        '开花末期', '果实成熟期',
        '果实脱落开始期', '果实脱落末期', '叶开始变色期',
        '叶全部变色期'
    ]

    # 处理缺失值
    df[pheno_columns] = df[pheno_columns].apply(pd.to_numeric, errors='coerce')

    # 添加年份列（假设存在年列）
    if '年份' not in df.columns:
        df['年份'] = df['时间'].str.extract(r'(\d{4})')[0].astype(float)
    return df


def compare_phenology(df, pheno_col):
    grass_data = df[df['CLASS'] == '草'][pheno_col].dropna()
    wood_data = df[df['CLASS'] == '木'][pheno_col].dropna()

    # 【修改点】不再检查正态性，统一使用 Mann-Whitney U 检验
    # 这样保证和绘图函数的逻辑完全一致
    u_stat, p_value = stats.mannwhitneyu(grass_data, wood_data, alternative='two-sided')

    # 计算效应量 (使用秩双列相关系数 r)
    n1, n2 = len(grass_data), len(wood_data)
    z_score = (u_stat - (n1 * n2) / 2) / np.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12)
    effect_size = z_score / np.sqrt(n1 + n2)

    return {
        'test': 'Mann-Whitney U',  # 明确标记测试方法
        'p_value': p_value,
        'mean_diff': grass_data.mean() - wood_data.mean(),
        'effect_size': effect_size
    }


# 修改 2: 让绘图函数使用外部传入的校正后 P 值 (避免重复计算和不一致)
def plot_difference_boxplot(df, pheno_columns, p_values_dict=None):
    """
    p_values_dict: 一个字典，key是物候期列名，value是校正后的p值 (来自 main_analysis 的计算结果)
    """
    boxplot_data = []

    # 如果没有传入校正后的P值，则现场计算原始P值 (兼容旧调用)
    use_external_p = p_values_dict is not None

    for col in pheno_columns:
        grass_data = df[df['CLASS'] == '草'][col].dropna()
        wood_data = df[df['CLASS'] == '木'][col].dropna()

        if use_external_p:
            p_value = p_values_dict.get(col, 1.0)
        else:
            _, p_value = stats.mannwhitneyu(grass_data, wood_data, alternative='two-sided')

        # 显著性标记逻辑 (建议基于校正后的P值，或者明确标注这是未校正的)
        # 这里为了严谨，我们假设传入的是校正后的P值
        if p_value < 0.001:
            significance = '***'
        elif p_value < 0.01:
            significance = '**'
        elif p_value < 0.05:
            significance = '*'
        else:
            significance = ''  # 不显著不显示，或者显示 'ns'

        boxplot_data.append({
            'phenology': col,
            'grass_data': grass_data,
            'wood_data': wood_data,
            'p_value': p_value,
            'significance': significance
        })

    # 绘制箱形图
    fig, ax = plt.subplots(figsize=(14, 8))
    positions = range(len(pheno_columns))  # 每个物候期一个位置，但每个位置上有两个箱形图

    for i, data in enumerate(boxplot_data):
        grass_data = data['grass_data']
        wood_data = data['wood_data']

        # 绘制草本的箱形图（深蓝色）
        bp_grass = ax.boxplot([grass_data], positions=[positions[i] - 0.2],
                              widths=0.35, patch_artist=True, showfliers=False,
                              boxprops=dict(facecolor='#2C5C8A'))  # Pantone 7696C

        # 绘制灌木的箱形图（暖橙色）
        bp_wood = ax.boxplot([wood_data], positions=[positions[i] + 0.2],
                             widths=0.35, patch_artist=True, showfliers=False,
                             boxprops=dict(facecolor='#CC6633'))  # Pantone 7579C

        # 添加显著性标记
        if data['significance']:  # 只有显著性标记存在时才显示
            ax.text(positions[i],
                    max(grass_data.max(), wood_data.max()) + 0.5,
                    data['significance'], ha='center', fontsize=20, color='red')

    # 设置图形标题和标签
    ax.set_xlabel('物候期', fontsize=24)
    ax.set_ylabel('日期 DOY', fontsize=24)
    # 2. 设置刻度标签和刻度线样式 (让坐标轴刻度变大)
    ax.tick_params(axis='both', which='major', labelsize=20, width=2, length=8)
    # 如果是次要刻度也想变大，可以添加: ax.tick_params(axis='both', which='minor', labelsize=18, width=1.5, length=6)

    # 3. 设置X轴刻度
    ax.set_xticks(positions)
    ax.set_xticklabels(pheno_columns, rotation=45, ha='right', fontsize=20) # X轴标签也显式设大一点


    # 显示图例
    from matplotlib.patches import Patch
    plt.legend(handles=[Patch(facecolor='#2C5C8A', label='草本'),
                        Patch(facecolor='#CC6633', label='灌木')],
               loc='upper left',
           fontsize=24)

    # 显示图形
    plt.show()
# 可视化函数
def plot_comparison(df, pheno_columns):
    num_plots = len(pheno_columns)
    rows = int(np.ceil(num_plots / 2))
    fig, axes = plt.subplots(rows, 2, figsize=(15, 5 * rows))  # 创建子图布局
    axes = axes.flatten()  # 将axes数组展平方便迭代

    for ax, pheno_col in zip(axes, pheno_columns):
        sns.boxplot(x='CLASS', y=pheno_col, data=df, ax=ax)
        ax.set_title(f'{pheno_col}分布比较')
        ax.set_ylabel('DOY')

    # 移除多余的子图
    for i in range(num_plots, len(axes)):
        fig.delaxes(axes[i])

    plt.tight_layout()  # 自动调整子图参数,使之填充整个图像区域。
    plt.show()


def analyze_temporal_trend(df, pheno_columns):
    results = {}

    for pheno_col in pheno_columns:
        trends = df.groupby(['CLASS', '年份'])[pheno_col].mean().unstack()

        # 计算年际变化值
        yearly_changes = trends.diff(axis=1)

        # 存储结果
        results[pheno_col] = {
            'Yearly Trends': trends,
            'Yearly Changes': yearly_changes
        }

    # 将结果转换为适合导出的DataFrame格式
    export_data = []
    for pheno_col, data in results.items():
        yearly_trends = data['Yearly Trends'].reset_index()
        yearly_changes = data['Yearly Changes'].reset_index()

        yearly_trends_melted = yearly_trends.melt(id_vars='CLASS', var_name='Year', value_name=f'{pheno_col}_Trend')
        yearly_changes_melted = yearly_changes.melt(id_vars='CLASS', var_name='Year', value_name=f'{pheno_col}_Change')

        merged_data = pd.merge(yearly_trends_melted, yearly_changes_melted, on=['CLASS', 'Year'])
        export_data.append(merged_data)

    final_df = pd.concat(export_data, axis=1)
    final_df.to_csv('F:\\站点\\中国地面\\\\年变化_analysis_results.csv', encoding='gbk')

# 6. 站点差异分析
def analyze_site_differences(df, pheno_columns):
    site_results = {}

    for site in df['站点'].unique():
        site_results[site] = {}
        site_df = df[df['站点'] == site]

        for pheno_col in pheno_columns:
            # 提取草类和木本植物的数据
            grass_data = site_df[site_df['CLASS'] == '草'][pheno_col].dropna()
            wood_data = site_df[site_df['CLASS'] == '木'][pheno_col].dropna()

            n_grass = len(grass_data)
            n_wood = len(wood_data)

            if n_grass > 0 and n_wood > 0:  # 确保有数据
                try:
                    # 使用Mann-Whitney U检验（非参数检验）
                    stat, p = stats.mannwhitneyu(grass_data, wood_data, alternative='two-sided')

                    # 计算效应量（基于Z值）
                    n1, n2 = n_grass, n_wood
                    mu = n1 * n2 / 2
                    var = n1 * n2 * (n1 + n2 + 1) / 12
                    sigma = np.sqrt(var)
                    Z = (stat - mu) / sigma
                    effect_size = Z / np.sqrt(n1 + n2)  # 范围在-1到1之间，符号表示差异方向

                    # 计算均值差
                    mean_diff = grass_data.mean() - wood_data.mean()

                    # 记录结果
                    site_results[site][f'{pheno_col}_mean_diff'] = mean_diff
                    site_results[site][f'{pheno_col}_p_value'] = p
                    site_results[site][f'{pheno_col}_effect_size'] = effect_size
                except ValueError:
                    # 如果无法计算U检验（例如样本量不足），则填充NaN
                    site_results[site][f'{pheno_col}_mean_diff'] = np.nan
                    site_results[site][f'{pheno_col}_p_value'] = np.nan
                    site_results[site][f'{pheno_col}_effect_size'] = np.nan
            else:
                # 样本量不足时填充NaN
                site_results[site][f'{pheno_col}_mean_diff'] = np.nan
                site_results[site][f'{pheno_col}_p_value'] = np.nan
                site_results[site][f'{pheno_col}_effect_size'] = np.nan

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
        '开始展叶期', '展叶盛期',
        '花序或花蕾出现期', '开花始期', '开花盛期',
        '开花末期', '果实成熟期',
        '果实脱落开始期', '果实脱落末期', '叶开始变色期',
        '叶全部变色期'
    ]

    # 简化列名便于显示
    short_names = {
        '开始展叶期': '展叶开始',
        '展叶盛期': '展叶盛期',
        '花序或花蕾出现期': '花蕾出现',
        '开花始期': '开花始期',
        '开花盛期': '开花盛期',
        '开花末期': '开花末期',
        '果实成熟期': '果实成熟',
        '果实脱落开始期': '果落开始',
        '果实脱落末期': '果落末期',
        '叶开始变色期': '叶变色开始',
        '叶全部变色期': '叶全变色'
    }

    # 对两个类群分别进行分析
    for type_name, data in [('草本', grass_df), ('木本', wood_df)]:
        plt.figure(figsize=(12, 10))

        # 1. 绘制散点图矩阵
        print(f"\n{type_name}物候期散点图矩阵：")
        g = sns.pairplot(data[pheno_columns].dropna(),
                         plot_kws={'alpha': 0.5},
                         diag_kind='kde',
                         markers='+')
        g.map_lower(sns.regplot, scatter=False)
        plt.suptitle(f'{type_name}物候期关系分布', y=1.02)
        plt.show()

        # 2. 计算相关系数矩阵并按指定顺序排列
        corr_matrix = data[pheno_columns].corr(method='spearman')[pheno_columns]

        # 3. 绘制聚类热图并按指定顺序排列
        plt.figure(figsize=(12, 12))
        cmap = sns.diverging_palette(220, 10, as_cmap=True)
        clustergrid = sns.clustermap(corr_matrix.rename(columns=short_names, index=short_names),
                                     cmap=cmap,
                                     annot=True,
                                     fmt=".2f",
                                     vmin=-1, vmax=1,
                                     figsize=(12, 12),
                                     row_cluster=False, col_cluster=False)
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
    计算每个站点草本与灌木的物候差值，并绘制堆叠比例图。
    横坐标为各个物候期，纵坐标为对应的比例。
    """
    # 初始化结果存储
    pheno_diff_counts = {pheno_col: {'wood_earlier_ratio': [], 'grass_earlier_ratio': []} for pheno_col in pheno_columns}

    for site in df['站点'].unique():
        site_df = df[df['站点'] == site]

        for pheno_col in pheno_columns:
            grass_data = site_df[site_df['CLASS'] == '草'][pheno_col].dropna()
            wood_data = site_df[site_df['CLASS'] == '木'][pheno_col].dropna()

            if len(grass_data) > 0 and len(wood_data) > 0:
                # 计算草本和灌木的均值差异
                mean_diff = grass_data.mean() - wood_data.mean()

                if mean_diff > 0:  # 灌木物候更早
                    pheno_diff_counts[pheno_col]['wood_earlier_ratio'].append(1)
                    pheno_diff_counts[pheno_col]['grass_earlier_ratio'].append(0)
                elif mean_diff < 0:  # 草本物候更早
                    pheno_diff_counts[pheno_col]['wood_earlier_ratio'].append(0)
                    pheno_diff_counts[pheno_col]['grass_earlier_ratio'].append(1)
                else:  # 物候相同
                    pheno_diff_counts[pheno_col]['wood_earlier_ratio'].append(0.5)
                    pheno_diff_counts[pheno_col]['grass_earlier_ratio'].append(0.5)

    # 计算平均比例
    avg_ratios = {}
    for pheno_col in pheno_columns:
        total_sites = len(pheno_diff_counts[pheno_col]['wood_earlier_ratio'])
        avg_ratios[pheno_col] = {
            'wood_earlier_ratio': sum(pheno_diff_counts[pheno_col]['wood_earlier_ratio']) / total_sites,
            'grass_earlier_ratio': sum(pheno_diff_counts[pheno_col]['grass_earlier_ratio']) / total_sites
        }

    # 绘制堆叠柱状图
    fig, ax = plt.subplots(figsize=(12, 8))
    bar_width = 0.8
    index = range(len(pheno_columns))

    wood_earlier_values = [avg_ratios[col]['wood_earlier_ratio'] for col in pheno_columns]
    grass_earlier_values = [avg_ratios[col]['grass_earlier_ratio'] for col in pheno_columns]

    ax.bar(index, wood_earlier_values, bar_width, label='灌丛物候更早', color='skyblue')
    ax.bar(index, grass_earlier_values, bar_width, bottom=wood_earlier_values, label='草本物候更早', color='lightgreen')

    # 添加数值标注（只标注其中一个）
    for i, (wood_val, grass_val) in enumerate(zip(wood_earlier_values, grass_earlier_values)):
        ax.text(i, wood_val / 2, f'{wood_val:.2f}', ha='center', va='center', fontsize=9)

    # 设置横坐标标签
    ax.set_xlabel('物候期', fontsize=20)
    ax.set_xticks(index)
    ax.set_xticklabels(pheno_columns, rotation=45, ha='right', fontsize=20)  # x轴标签大小改为20

    # 设置纵坐标标签
    ax.set_ylabel('灌木早于草本物候期的站点占比', fontsize=20)
    ax.set_ylim(0, 1)

    # 添加标题和图例
    ax.set_title('各站点草本与灌木物候期差异比例', fontsize=20)
    ax.legend()

    plt.tight_layout()
    plt.show()



def main_analysis():
    df = load_data()
    df = preprocess(df)

    # 定义需要分析的站点列表，即既有草又有灌哈尔滨
    # 牡丹江
    # 银川
    # 民勤
    # 泰安
    # 北京
    # 长春
    sites_of_interest = ['泰安', '民勤', '哈尔滨', '银川', '牡丹江', '北京', '长春']
    df = df[df['站点'].isin(sites_of_interest)]

    # 调用函数进行分
    pheno_columns = [
        '开始展叶期', '展叶盛期',
        '花序或花蕾出现期', '开花始期', '开花盛期',
        '开花末期', '果实成熟期',
        '果实脱落开始期', '果实脱落末期', '叶开始变色期',
        '叶全部变色期'
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
   # combined_results.to_csv('F:\\站点\\中国地面\\\\中国地面combined_analysis_results.csv', encoding='gbk')

    print("全局差异分析结果:")
    print(results_df[['pheno', 'mean_diff', 'effect_size', 'p_value', 'p_adjusted']])
    print("\n绘制草本与灌木物候期差值箱形图...")
    plot_difference_boxplot(df, pheno_columns)
    # 调用修改后的可视化函数
    #plot_comparison(df, pheno_columns)

    # 调用修改后的时间趋势分析函数
    #analyze_temporal_trend(df, pheno_columns)

    # 输出站点差异分析结果
    print("\n站点差异分析结果:")
    print(site_results_df)

    # 新增相关性分析
    print("\n正在进行物候期相关性分析...")
    #analyze_phenology_correlations(df)

    # 新增物候差值比例图
    print("\n绘制草本与灌木物候期差异比例图...")
    plot_phenology_difference_proportion(df, pheno_columns)


if __name__ == '__main__':
    main_analysis()



