import pandas as pd
import numpy as np
import statsmodels.api as sm
import pingouin as pg
from itertools import combinations

# 加载气候数据
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
    # 1. 加载数据
    temp_df = load_climate_data('F:\站点\植物物候观测数据集20161202\CLIME\\temp.csv')
    precip_df = load_climate_data('F:\站点\植物物候观测数据集20161202\CLIME\Preci.csv')

    phase_columns = ['Budburst','Flower','Fruit','Coloration']

    pheno_df = load_phenology_data('F:/站点/植物物候观测数据集20161202/CLIME/wd.csv', phase_columns)

    # 异常值处理
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
            merged = merged.dropna()

            if len(merged) < 3:
                continue

            # 统计分析
            try:
                # 标准化数据
                merged_std = merged.copy()
                for col in ['doy_late', 'doy_early', 'temp', 'precip']:
                    merged_std[col + '_std'] = (merged_std[col] - merged_std[col].mean()) / merged_std[col].std()

                # 模型1: doy_late ~ doy_early + temp + precip
                X1 = sm.add_constant(merged_std[['doy_early_std', 'temp_std', 'precip_std']])
                y1 = merged_std['doy_late_std']
                model1 = sm.OLS(y1, X1).fit()
                beta_ph = model1.params['doy_early_std']  # 敏感性：doy_early 的标准化系数

                # 模型2: doy_late ~ temp + doy_early + precip
                X2 = sm.add_constant(merged_std[['temp_std', 'doy_early_std', 'precip_std']])
                y2 = merged_std['doy_late_std']
                model2 = sm.OLS(y2, X2).fit()
                beta_temp = model2.params['temp_std']  # 敏感性：temp 的标准化系数

                # 模型3: doy_late ~ precip + doy_early + temp
                X3 = sm.add_constant(merged_std[['precip_std', 'doy_early_std', 'temp_std']])
                y3 = merged_std['doy_late_std']
                model3 = sm.OLS(y3, X3).fit()
                beta_precip = model3.params['precip_std']  # 敏感性：precip 的标准化系数

                # 保存结果
                results.append({
                    'site': site,
                    'species': species,
                    'phase_early': phase1,
                    'phase_late': phase2,
                    'sensitivity_ph': beta_ph,
                    'sensitivity_temp': beta_temp,
                    'sensitivity_precip': beta_precip,
                    'rsquared': model1.rsquared
                })
            except Exception as e:
                print(f"An error occurred during analysis for site {site}, species {species}: {e}")
                continue

    # 保存结果
    result_df = pd.DataFrame(results)
    result_df.to_csv('F:\站点\植物物候观测数据集20161202\CLIME\clim_carryover_effect_wd2.csv', index=False, encoding='gbk')

if __name__ == '__main__':
    main()