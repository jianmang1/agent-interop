import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.stats.multitest import multipletests
from scipy.stats import ttest_ind, mannwhitneyu

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号'-'显示为方块的问题

# 1. 数据准备
def load_data():
    # 读取Excel文件
    neighbor_df = pd.read_excel(r'D:\MODIS43A4_2024\CLCD\neighbor_output_all_years.xlsx')
    center_df = pd.read_excel(r'D:\MODIS43A4_2024\CLCD\center_output_all_years.xlsx')

    # 添加类群标识
    neighbor_df['CLASS'] = '邻域'
    center_df['CLASS'] = '中心'

    # 合并两个DataFrame
    df = pd.concat([neighbor_df, center_df], ignore_index=True)
    return df


# 2. 数据预处理
def preprocess(df):
    pheno_columns = ['SOS_value', 'POS_value', 'EOS_value', 'LOS_value', 'GUP_value', 'GDP_value']
    df[pheno_columns] = df[pheno_columns].apply(pd.to_numeric, errors='coerce')
    return df, pheno_columns


# 3. 基础统计分析函数
def compare_phenology(df, pheno_col):
    # 分组数据
    grass_data = df[df['CLASS'] == '邻域'][pheno_col].dropna()
    wood_data = df[df['CLASS'] == '中心'][pheno_col].dropna()

    # 检查正态性（Shapiro-Wilk检验）
    _, p_grass = stats.shapiro(grass_data)
    _, p_wood = stats.shapiro(wood_data)

    # 根据正态性选择检验方法
    if p_grass > 0.05 and p_wood > 0.05:  # 数据近似正态
        t_stat, p_value = stats.ttest_ind(grass_data, wood_data, equal_var=True)
        effect_size = (grass_data.mean() - wood_data.mean()) / np.sqrt(
            (grass_data.std() ** 2 + wood_data.std() ** 2) / 2
        )
        test_name = 't-test'
    else:  # 非正态，使用Mann-Whitney U检验
        u_stat, p_value = stats.mannwhitneyu(grass_data, wood_data, alternative='two-sided')
        effect_size = u_stat / (len(grass_data) * len(wood_data))  # 效应量r
        test_name = 'Mann-Whitney U'

    return {
        'test': test_name,
        'p_value': p_value,
        'mean_diff': grass_data.mean() - wood_data.mean(),
        'effect_size': effect_size
    }


# 4. 箱形图可视化
def plot_difference_boxplot(df, pheno_columns):
    fig, ax = plt.subplots(figsize=(16, 8))
    positions = range(len(pheno_columns))

    boxplot_data = []

    for col in pheno_columns:
        neighbor_data = df[df['CLASS'] == '邻域'][col].dropna()
        center_data = df[df['CLASS'] == '中心'][col].dropna()

        _, p_value = ttest_ind(neighbor_data, center_data, equal_var=False)

        significance = None
        if p_value < 0.001:
            significance = '***'
        elif p_value < 0.01:
            significance = '**'
        elif p_value < 0.05:
            significance = '*'

        boxplot_data.append({
            'phenology': col,
            'neighbor_data': neighbor_data,
            'center_data': center_data,
            'p_value': p_value,
            'significance': significance
        })

    for i, data in enumerate(boxplot_data):
        ax.boxplot([data['neighbor_data']], positions=[positions[i] - 0.2],
                   widths=0.35, patch_artist=True, showfliers=False,
                   boxprops=dict(facecolor='#2C5C8A'), labels=['邻域'])

        ax.boxplot([data['center_data']], positions=[positions[i] + 0.2],
                   widths=0.35, patch_artist=True, showfliers=False,
                   boxprops=dict(facecolor='#CC6633'), labels=['中心'])

        max_val = max(data['neighbor_data'].max(), data['center_data'].max())
        if data['significance']:
            ax.text(positions[i], max_val + 0.5, data['significance'],
                    ha='center', fontsize=12, color='red')

    ax.set_xlabel('物候指标')
    ax.set_ylabel('数值')
    ax.set_xticks(positions)
    ax.set_xticklabels(pheno_columns, rotation=45, ha='right')
    plt.legend(handles=[
        plt.Rectangle((0, 0), 1, 1, color='#2C5C8A'),
        plt.Rectangle((0, 0), 1, 1, color='#CC6633')
    ], labels=['邻域像元', '中心像元'], loc='upper left')
    plt.tight_layout()
    plt.title('中心 vs 邻域像元物候差异箱型图')
    plt.show()
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
    final_df.to_csv('D:\MODIS43A4_2024\CLCD\年变化_analysis_results.csv', encoding='gbk')

# 6. 站点差异分析
def analyze_site_differences(df, pheno_columns):
    # 使用 row 和 col 的组合作为唯一标识
    df['站点'] = df['row'].astype(str) + '_' + df['col'].astype(str)

    site_results = {}

    for site_id in df['站点'].unique():
        site_df = df[df['站点'] == site_id]

        # 只有一个类群（草或木）也跳过
        if len(site_df['CLASS'].unique()) < 2:
            continue

        grass_data = site_df[site_df['CLASS'] == '邻域']
        wood_data = site_df[site_df['CLASS'] == '中心']

        site_results[site_id] = {}

        for pheno_col in pheno_columns:
            val1 = grass_data[pheno_col].values
            val2 = wood_data[pheno_col].values

            if len(val1) == 0 or len(val2) == 0:
                site_results[site_id][f'{pheno_col}_mean_diff'] = np.nan
                site_results[site_id][f'{pheno_col}_p_value'] = np.nan
                site_results[site_id][f'{pheno_col}_effect_size'] = np.nan
                continue

            try:
                # 使用 Mann-Whitney U 检验
                stat, p = mannwhitneyu(val1, val2, alternative='two-sided')

                # 计算效应量 r
                n1, n2 = len(val1), len(val2)
                mu = n1 * n2 / 2
                var = n1 * n2 * (n1 + n2 + 1) / 12
                Z = (stat - mu) / np.sqrt(var)
                effect_size = Z / np.sqrt(n1 + n2)

                mean_diff = val1.mean() - val2.mean()

                site_results[site_id][f'{pheno_col}_mean_diff'] = mean_diff
                site_results[site_id][f'{pheno_col}_p_value'] = p
                site_results[site_id][f'{pheno_col}_effect_size'] = effect_size

            except Exception as e:
                print(f"Error processing {site_id}, {pheno_col}: {e}")
                site_results[site_id][f'{pheno_col}_mean_diff'] = np.nan
                site_results[site_id][f'{pheno_col}_p_value'] = np.nan
                site_results[site_id][f'{pheno_col}_effect_size'] = np.nan

    results_df = pd.DataFrame.from_dict(site_results, orient='index')
    return results_df


def analyze_phenology_correlations(df):
    """
    分析不同类群物候期之间的相关性差异
    使用pairplot展示关系分布，clustermap展示相关性模式
    """
    # 准备数据：分别提取草、木类群数据
    grass_df = df[df['CLASS'] == '邻域'].copy()
    wood_df = df[df['CLASS'] == '中心'].copy()

    # 定义分析的物候期列（与之前保持一致）
    pheno_columns = ['SOS_value', 'POS_value', 'EOS_value', 'LOS_value', 'GUP_value', 'GDP_value']


    # 简化列名便于显示
    short_names = {
        'SOS_value': 'SOS',
        'POS_value': 'POS',
        'EOS_value': 'EOS',
        'LOS_value': 'LOS',
        'GUP_value': 'GUP',
        'GDP_value': 'GDP',
    }

    # 对两个类群分别进行分析
    for type_name, data in [('邻域', grass_df), ('中心', wood_df)]:
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
            grass_data = site_df[site_df['CLASS'] == '邻域'][pheno_col].dropna()
            wood_data = site_df[site_df['CLASS'] == '中心'][pheno_col].dropna()

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

    # 添加数值标注
    for i, (wood_val, grass_val) in enumerate(zip(wood_earlier_values, grass_earlier_values)):
        ax.text(i, wood_val + grass_val / 2, f'{wood_val:.2f}\n{grass_val:.2f}', ha='center', va='center', fontsize=9)

    # 设置横坐标标签
    ax.set_xlabel('物候期')
    ax.set_xticks(index)
    ax.set_xticklabels(pheno_columns, rotation=45, ha='right')

    # 设置纵坐标标签
    ax.set_ylabel('比例')
    ax.set_ylim(0, 1)

    # 添加标题和图例
    ax.set_title('各站点草本与灌木物候期差异比例')
    ax.legend()

    plt.tight_layout()
    plt.show()


def main_analysis():
    df = load_data()
    df, pheno_columns = preprocess(df)

    # 手动指定物候列
    pheno_columns = ['SOS_value', 'POS_value', 'EOS_value', 'LOS_value', 'GUP_value', 'GDP_value']

    # 全局差异分析：中心 vs 邻域
    results = []
    for col in pheno_columns:
        res = compare_phenology(df, col)
        res['pheno'] = col
        results.append(res)

    results_df = pd.DataFrame(results)
    _, p_adjusted, _, _ = multipletests(results_df['p_value'], method='fdr_bh')
    results_df['p_adjusted'] = p_adjusted

    # 导出全局差异分析结果到CSV
    output_path = r'D:\MODIS43A4_2024\CLCD\CLCD_global_analysis_results.csv'
    results_df.to_csv(output_path, index=False, encoding='gbk')

    # 输出全局差异分析结果
    print("全局差异分析结果:")
    print(results_df[['pheno', 'mean_diff', 'effect_size', 'p_value', 'p_adjusted']])
    print(f"结果已保存至: {output_path}")

    # 可视化：箱形图
    print("\n绘制中心 vs 邻域物候期差值箱形图...")
    plot_difference_boxplot(df, pheno_columns)

    # 可选：多子图展示每个物候指标分布
    plot_comparison(df, pheno_columns)

    # 时间趋势分析（若函数定义中没有使用“站点”字段）
    analyze_temporal_trend(df, pheno_columns)

    # 新增相关性分析
    print("\n正在进行物候期相关性分析...")
    analyze_phenology_correlations(df)

    # 新增物候差值比例图（如果该函数也未依赖“站点”字段）
    if 'plot_phenology_difference_proportion' in globals():
        print("\n绘制中心 vs 邻域物候期差异比例图...")
        plot_phenology_difference_proportion(df, pheno_columns)


if __name__ == '__main__':
    main_analysis()

if __name__ == '__main__':
    main_analysis()



