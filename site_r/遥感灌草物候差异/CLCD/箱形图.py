import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.stats.multitest import multipletests
from scipy.stats import ttest_ind

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# 1. 数据加载
def load_data():
    # 读取Excel文件
    df = pd.read_excel('D:/MODIS43A4_2024/combined_output_2021.xlsx')

    # 定义物候期列表
    pheno_list = ['SOS', 'POS', 'EOS', 'LOS', 'GUP', 'GDP']

    # 初始化存储容器
    all_data = pd.DataFrame()

    for pheno in pheno_list:
        # 处理灌木数据（_value）
        shrub = df[['row', 'col', f'{pheno}_value']].copy()
        shrub['CLASS'] = '灌木'
        shrub['Subclass'] = 'shrub'
        shrub['物候期'] = pheno
        shrub.rename(columns={f'{pheno}_value': 'Value'}, inplace=True)

        # 处理草本数据（只处理_4）
        grass = df[['row', 'col', f'{pheno}_4']].copy()
        grass['CLASS'] = '草本'
        grass['Subclass'] = 'grass_4'
        grass['物候期'] = pheno
        grass.rename(columns={f'{pheno}_4': 'Value'}, inplace=True)

        all_data = pd.concat([all_data, shrub, grass], ignore_index=True)

    return all_data


# 2. 数据预处理
def preprocess(df):
    # 转换数值类型并处理缺失值
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    # 过滤0值和缺失值
    df = df[(df['Value'] != 0) & (df['Value'].notna())]
    return df


# 3. 统计分析函数（灌木 vs 每个草本子类）
def compare_phenology(df, pheno, subclass):
    pheno_df = df[(df['物候期'] == pheno) &
                  ((df['CLASS'] == '灌木') |
                   ((df['CLASS'] == '草本') & (df['Subclass'] == subclass)))]

    # 分组数据
    shrub_data = pheno_df[pheno_df['CLASS'] == '灌木']['Value']
    grass_data = pheno_df[pheno_df['CLASS'] == '草本']['Value']

    # 正态性检验
    _, p_shrub = stats.shapiro(shrub_data)
    _, p_grass = stats.shapiro(grass_data)

    # 选择检验方法
    if p_shrub > 0.05 and p_grass > 0.05:
        t_stat, p_value = ttest_ind(shrub_data, grass_data, equal_var=False)
        effect_size = (shrub_data.mean() - grass_data.mean()) / np.sqrt(
            (shrub_data.std() ** 2 + grass_data.std() ** 2) / 2)
        test_name = 't-test'
    else:
        u_stat, p_value = stats.mannwhitneyu(shrub_data, grass_data)
        effect_size = u_stat / (len(shrub_data) * len(grass_data))
        test_name = 'Mann-Whitney U'

    return {
        '物候期': pheno,
        '草本子类': subclass,
        '检验方法': test_name,
        'p值': p_value,
        '均值差': shrub_data.mean() - grass_data.mean(),
        '效应量': effect_size
    }


# 4. 可视化函数
def plot_difference_boxplot(df):
    # 设置颜色映射
    palette = {
        '灌木': '#CC6633',
        'grass_4': '#2C5C8A'
    }

    # 创建分类变量和顺序控制
    df['Category'] = np.where(df['CLASS'] == '灌木', '灌木', df['Subclass'])
    hue_order = ['灌木', 'grass_4']

    # 创建画布
    plt.figure(figsize=(16, 8))
    ax = plt.gca()

    # 绘制箱线图
    sns.boxplot(x='物候期', y='Value', hue='Category', data=df,
                palette=palette, showfliers=False, width=0.8, hue_order=hue_order)

    # 获取x轴坐标信息
    n_pheno = len(df['物候期'].unique())  # 物候期数量
    n_groups = len(hue_order)  # 每组分类数量

    # 计算每个箱体的中心坐标
    positions = []
    for pheno_idx in range(n_pheno):
        # 每个物候期起始位置
        base = pheno_idx
        # 每组偏移量（根据seaborn默认偏移逻辑）
        offsets = np.linspace(-0.3, 0.3, n_groups)
        for offset in offsets:
            positions.append(base + offset)

    # 添加显著性标记
    subclasses = ['grass_4']
    for pheno_idx, pheno in enumerate(df['物候期'].unique()):
        for subclass_idx, subclass in enumerate(subclasses, start=1):
            # 计算当前分类在hue_order中的位置
            group_idx = subclass_idx  # 灌木是0，草本子类从1开始

            # 获取对应箱体的位置索引
            pos_index = pheno_idx * n_groups + group_idx

            # 执行统计检验
            res = compare_phenology(df, pheno, subclass)

            # 获取当前箱体的y_max值
            current_data = df[(df['物候期'] == pheno) &
                              (df['Category'] == subclass)]['Value']
            shrub_data = df[(df['物候期'] == pheno) &
                            (df['Category'] == '灌木')]['Value']
            y_max_current = current_data.max()
            y_max_shrub = shrub_data.max()
            y_max = max(y_max_current, y_max_shrub)

            # 增加一个固定的偏移量以避免重叠
            y_offset = -10

            # 添加星号标记
            if res['p值'] < 0.001:
                marker = '***'
            elif res['p值'] < 0.01:
                marker = '**'
            elif res['p值'] < 0.05:
                marker = '*'
            else:
                continue

            # 获取准确坐标位置
            x_pos = positions[pos_index]
            ax.text(x_pos, y_max + y_offset, marker,
                    ha='center', va='bottom',
                    fontsize=12, color='red')

    plt.title('灌木与草本各子类物候期比较（***p<0.001, **p<0.01, *p<0.05）')
    plt.ylabel('发生时间（DOY）')
    plt.xlabel('物候期类型')
    plt.legend(title='植被类别')
    plt.tight_layout()
    plt.show()


# 主分析流程
def main_analysis():
    # 数据准备
    df = load_data()
    df = preprocess(df)
    print(f"有效数据量：{len(df)}条")

    # 全局统计分析
    pheno_list = df['物候期'].unique()
    subclasses = ['grass_4']
    results = []

    for pheno in pheno_list:
        for subclass in subclasses:
            res = compare_phenology(df, pheno, subclass)
            results.append(res)

    results_df = pd.DataFrame(results)

    # 多重检验校正（按物候期分组）
    results_df['校正后p值'] = results_df.groupby('物候期')['p值'].transform(
        lambda x: multipletests(x, method='fdr_bh')[1])

    # 输出结果
    print("全局统计分析结果：")
    print(results_df.sort_values(['物候期', '草本子类']))

    # 可视化
    print("\n生成箱线图...")
    plot_difference_boxplot(df)

    # 保存结果
    results_df.to_excel('分析结果汇总.xlsx', index=False)


if __name__ == '__main__':
    main_analysis()