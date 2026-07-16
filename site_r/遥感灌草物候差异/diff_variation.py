import pandas as pd
import numpy as np
from scipy.stats import ttest_ind, pearsonr


# 读取 Excel 文件
file_path = r'D:\MODIS43A4_2024\combined_output.xlsx'
df = pd.read_excel(file_path)

# 定义前缀列表（假设数据包含 sos, pos, los, eos, stp）
prefixes = ['sos', 'pos', 'los', 'eos', 'stp']

# 提取每组的值列
group_columns = {}
for prefix in prefixes:
    group_columns[prefix] = [col for col in df.columns if col.startswith(f'{prefix}_')]

# 1. 组内分析
def group_analysis(df, group_cols):
    """计算每组的描述性统计量"""
    group_data = df[group_cols].dropna()
    stats = group_data.describe().T  # 计算均值、标准差等
    stats['range'] = stats['max'] - stats['min']  # 计算极差
    stats['cv'] = stats['std'] / stats['mean']  # 计算变异系数

    # 计算组内相关性
    corr_matrix = group_data.corr()
    return stats, corr_matrix


# 2. 组间分析
def inter_group_analysis(df, prefixes):
    """比较不同组之间的差异"""
    results = {}
    for i in range(len(prefixes)):
        for j in range(i + 1, len(prefixes)):
            prefix1, prefix2 = prefixes[i], prefixes[j]
            col1, col2 = f'{prefix1}_value', f'{prefix2}_value'
            if col1 in df.columns and col2 in df.columns:
                t_stat, p_value = ttest_ind(df[col1].dropna(), df[col2].dropna())
                results[(prefix1, prefix2)] = {'t-stat': t_stat, 'p-value': p_value}
    return results


# 执行分析
# 组内分析
for prefix, cols in group_columns.items():
    stats, corr_matrix = group_analysis(df, cols)
    print(f"\n{prefix} 组内统计分析:")
    print(stats)
    print(f"{prefix} 组内相关性矩阵:")
    print(corr_matrix)

# 组间分析
inter_group_results = inter_group_analysis(df, prefixes)
print("\n组间差异分析 (t 检验):")
for (prefix1, prefix2), result in inter_group_results.items():
    print(f"{prefix1} vs {prefix2}: t-stat={result['t-stat']:.4f}, p-value={result['p-value']:.4f}")