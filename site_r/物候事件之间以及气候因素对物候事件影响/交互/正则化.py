import pandas as pd
import numpy as np
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler
from itertools import combinations


def load_climate_data(path):
    df = pd.read_csv(path, encoding='gbk')
    long_format_data = {
        'site': [],
        'year': [],
        'doy': [],
        'value': []
    }

    for index, row in df.iterrows():
        site = row[0]
        year = row[1]
        longitude = row[2]
        latitude = row[3]
        climate_data = row[4:]

        for doy, value in enumerate(climate_data, start=1):
            if pd.notna(value) and value != -9999:
                long_format_data['site'].append(site)
                long_format_data['year'].append(year)
                long_format_data['doy'].append(doy)
                long_format_data['value'].append(value)
            elif value == -9999:
                long_format_data['site'].append(site)
                long_format_data['year'].append(year)
                long_format_data['doy'].append(doy)
                long_format_data['value'].append(np.nan)

    df_long = pd.DataFrame(long_format_data)
    df_long = df_long.dropna(subset=['value']).astype({'doy': int})
    return df_long


# 加载物候数据并预处理
def load_phenology_data(path, phase_columns):
    try:
        df = pd.read_csv(path, encoding='gbk')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(path, encoding='gb18030')
        except UnicodeDecodeError:
            raise ValueError("Failed to decode the file with gbk and gb18030 encodings.")
    df = df.melt(id_vars=['site', 'species', 'year'],
                 value_vars=phase_columns,
                 var_name='phase', value_name='doy')
    return df

# 主分析函数
def main():
    # 1. 加载数据（保持不变）
    temp_df = load_climate_data('F:/站点/中国地面/clime/temp.csv')
    precip_df = load_climate_data('F:/站点/中国地面/clime/Preci.csv')

    phase_columns = ['开始展叶期', '展叶盛期', '花序或花蕾出现期', '开花始期',
                     '开花盛期', '开花末期', '果实成熟期', '果实脱落开始期',
                     '果实脱落末期', '叶开始变色期', '叶全部变色期']

    pheno_df = load_phenology_data('F:/站点/中国地面/clime/草本数据_with_LOS_and_LOS_half.csv', phase_columns)

    # 异常值处理（保持不变）
    def remove_outliers(group):
        mean = group.mean()
        std = group.std()
        return group[(group >= mean - 2 * std) & (group <= mean + 2 * std)]

    pheno_df['doy'] = pheno_df.groupby(['site', 'species', 'phase'])['doy'].transform(remove_outliers)
    pheno_df = pheno_df.dropna()

    # 3. 主分析循环
    results = []

    # 获取所有唯一的站点-物种组合
    site_species = pheno_df[['site', 'species']].drop_duplicates()

    for idx, (site, species) in site_species.iterrows():
        site_data = pheno_df[(pheno_df['site'] == site) &
                             (pheno_df['species'] == species)]

        # 获取所有物候阶段组合
        phases = site_data['phase'].unique()
        for phase1, phase2 in combinations(phases, 2):
            # 获取配对数据
            df1 = site_data[site_data['phase'] == phase1][['year', 'doy']]
            df2 = site_data[site_data['phase'] == phase2][['year', 'doy']]
            merged = pd.merge(df1, df2, on='year', suffixes=('_early', '_late'))

            # 过滤有效数据
            merged = merged.dropna()
            merged = merged[merged['doy_late'] > merged['doy_early']]
            if len(merged) < 3:
                continue

            # 提取气候数据
            temp_list = []
            precip_list = []
            for _, row in merged.iterrows():
                year = row['year']
                doy_e = int(row['doy_early'])
                doy_l = int(row['doy_late'])

                # 获取温度数据
                temp = temp_df[(temp_df['site'] == site) &
                               (temp_df['year'] == year) &
                               (temp_df['doy'] >= doy_e) &
                               (temp_df['doy'] <= doy_l)]['value'].mean()

                # 获取降水数据
                precip = precip_df[(precip_df['site'] == site) &
                                   (precip_df['year'] == year) &
                                   (precip_df['doy'] >= doy_e) &
                                   (precip_df['doy'] <= doy_l)]['value'].sum()

                temp_list.append(temp)
                precip_list.append(precip)

            merged['temp'] = temp_list
            merged['precip'] = precip_list
            merged = merged.dropna()  # 去除缺失值

            # 添加交互项
            merged['doy_temp'] = merged['doy_early'] * merged['temp']
            merged['doy_precip'] = merged['doy_early'] * merged['precip']
            merged['temp_precip'] = merged['temp'] * merged['precip']
            merged['doy_temp_precip'] = merged['doy_early'] * merged['temp'] * merged['precip']

            # 标准化所有变量（解决共线性）
            scaler = StandardScaler()
            merged_scaled = scaler.fit_transform(merged[['doy_early', 'temp', 'precip',
                                                         'doy_temp', 'doy_precip', 'temp_precip', 'doy_temp_precip']])
            X = merged_scaled[:, :7]  # 自变量：所有特征
            y = merged_scaled[:, 0]  # 因变量：doy_late

            # 使用岭回归（RidgeCV 自动选择 alpha）
            model = RidgeCV(alphas=[0.1, 1.0, 10.0], scoring='neg_mean_squared_error')
            model.fit(X, y)

            # 提取标准化后的回归系数（替代偏相关系数）
            coefficients = model.coef_
            intercept = model.intercept_

            # 保存结果
            results.append({
                'site': site,
                'species': species,
                'phase_early': phase1,
                'phase_late': phase2,

                # 主效应
                'doy_early_coeff': coefficients[0],  # doy_early 对应的系数
                'temp_coeff': coefficients[1],  # temp 对应的系数
                'precip_coeff': coefficients[2],  # precip 对应的系数

                # 交互项
                'doy_temp_coeff': coefficients[3],
                'doy_precip_coeff': coefficients[4],
                'temp_precip_coeff': coefficients[5],
                'doy_temp_precip_coeff': coefficients[6]
            })
    # 保存结果
    result_df = pd.DataFrame(results)
    result_df.to_csv('F:/站点/中国地面/clime/交互/clim_carryover_effect_ridge.csv', index=False, encoding='gbk')
    print("Analysis complete with Ridge Regression. Results saved to file.")

if __name__ == '__main__':
    main()