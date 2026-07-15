import pandas as pd
import numpy as np
from scipy.stats import ttest_ind
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from libpysal.weights import Queen
from esda.moran import Moran_Local
from sklearn.linear_model import LinearRegression
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW

# 读取 Excel 文件
file_path = r'D:\MODIS43A4_2024\combined_output1.xlsx'
df = pd.read_excel(file_path)

# 定义前缀列表（假设数据包含 sos, pos, los, eos, stp）
prefixes = ['sos', 'pos', 'eos']

# 提取每组的值列
group_columns = {}
for prefix in prefixes:
    group_columns[prefix] = [col for col in df.columns if col.startswith(f'{prefix}_')]

# 创建输出 Excel 文件
output_file = r'D:\MODIS43A4_2024\analysis_results1.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:

    # 1. 描述性统计
    def descriptive_stats(df, group_cols):
        stats_list = []
        for col in group_cols:
            valid_data = df[col][df[col] != 0]
            stats = valid_data.describe()
            stats['range'] = stats['max'] - stats['min']
            stats['cv'] = stats['std'] / stats['mean'] if stats['mean'] != 0 else np.nan
            stats['column'] = col
            stats_list.append(stats)
        return pd.DataFrame(stats_list).set_index('column')

    for prefix, cols in group_columns.items():
        stats_df = descriptive_stats(df, cols)
        stats_df.to_excel(writer, sheet_name=f'{prefix}_descriptive_stats')

    # 2. 相关性分析
    def correlation_matrix(df, group_cols):
        valid_data = df[group_cols].replace(0, np.nan)
        corr_matrix = valid_data.corr(method='pearson').dropna(how='all').dropna(axis=1, how='all')
        return corr_matrix

    for prefix, cols in group_columns.items():
        corr_df = correlation_matrix(df, cols)
        corr_df.to_excel(writer, sheet_name=f'{prefix}_correlation')

    # 3. 组间差异分析
    def inter_group_analysis(df, group_cols):
        results = {}
        for i in range(len(group_cols)):
            for j in range(i + 1, len(group_cols)):
                col1, col2 = group_cols[i], group_cols[j]
                valid_col1 = df[col1][df[col1] != 0]
                valid_col2 = df[col2][df[col2] != 0]
                t_stat, p_value = ttest_ind(valid_col1.dropna(), valid_col2.dropna())
                results[(col1, col2)] = {'t-stat': t_stat, 'p-value': p_value}
        return pd.DataFrame.from_dict(results, orient='index')

    for prefix, cols in group_columns.items():
        inter_group_results = inter_group_analysis(df, cols)
        inter_group_results.to_excel(writer, sheet_name=f'{prefix}_inter_group_analysis')

    # 4. 主成分分析 (PCA)
    def pca_analysis(df, prefixes):
        pca_data = pd.concat([df[[f'{prefix}_value' for prefix in prefixes]],
                              df[[f'{prefix}_31' for prefix in prefixes]],
                              df[[f'{prefix}_32' for prefix in prefixes]],
                              df[[f'{prefix}_33' for prefix in prefixes]]], axis=1).replace(0, np.nan).dropna()

        pca = PCA(n_components=2)
        principal_components = pca.fit_transform(pca_data)
        explained_variance = pca.explained_variance_ratio_

        pca_df = pd.DataFrame(principal_components, columns=['PC1', 'PC2'])
        variance_df = pd.DataFrame({'explained_variance': explained_variance})
        return pca_df, variance_df

    pca_df, variance_df = pca_analysis(df, prefixes)
    pca_df.to_excel(writer, sheet_name='pca_components')
    variance_df.to_excel(writer, sheet_name='pca_explained_variance')

    # 5. 聚类分析 (K-Means)
    def kmeans_clustering(df, prefixes, n_clusters=3):
        cluster_data = pd.concat([df[[f'{prefix}_value' for prefix in prefixes]],
                                  df[[f'{prefix}_31' for prefix in prefixes]],
                                  df[[f'{prefix}_32' for prefix in prefixes]],
                                  df[[f'{prefix}_33' for prefix in prefixes]]], axis=1).replace(0, np.nan).dropna()

        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(cluster_data)
        cluster_df = pd.DataFrame({'cluster': clusters})
        return cluster_df

    cluster_df = kmeans_clustering(df, prefixes)
    cluster_df.to_excel(writer, sheet_name='kmeans_clusters')

    # 6. 空间自相关分析 (Moran's I)
    def morans_i_analysis(df, w, column):
        values = df[column][df[column] != 0].values
        moran_local = Moran_Local(values, w)
        local_moran_df = pd.DataFrame({
            'local_moran': moran_local.Is,
            'p_value': moran_local.p_sim
        })
        global_moran = Moran(values, w)
        global_moran_df = pd.DataFrame({
            'global_moran': [global_moran.I],
            'p_value': [global_moran.p_sim]
        })
        return local_moran_df, global_moran_df

    w = Queen.from_dataframe(df[['row', 'col']])
    for prefix in prefixes:
        local_moran_df, global_moran_df = morans_i_analysis(df, w, f'{prefix}_value')
        local_moran_df.to_excel(writer, sheet_name=f'{prefix}_local_moran')
        global_moran_df.to_excel(writer, sheet_name=f'{prefix}_global_moran')

    # 7. 地理加权回归 (GWR)
    def gwr_analysis(df, dependent_col, independent_cols):
        coords = list(zip(df['row'], df['col']))
        y = df[dependent_col][df[dependent_col] != 0].values.reshape((-1, 1))
        X = df[independent_cols].replace(0, np.nan).dropna().values

        bw = Sel_BW(coords, y, X).search()
        model = GWR(coords, y, X, bw=bw).fit()
        params = pd.DataFrame(model.params, columns=[f'beta_{i}' for i in range(X.shape[1])])
        return params

    gwr_params = gwr_analysis(df, 'sos_value', ['pos_value', 'los_value', 'eos_value', 'stp_value'])
    gwr_params.to_excel(writer, sheet_name='gwr_parameters')

print(f"分析结果已保存至: {output_file}")



