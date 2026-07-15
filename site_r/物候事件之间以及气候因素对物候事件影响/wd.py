import pandas as pd
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
import pingouin as pg
from itertools import combinations


# 加载气候数据
def load_climate_data(path):
    df = pd.read_csv(path, encoding='gbk')
    # 初始化长格式数据字典
    long_format_data = {
        'site': [],
        'year': [],
        'doy': [],
        'value': []
    }

    # 遍历每一行数据
    for index, row in df.iterrows():
        site = row[0]  # 第一列为站点名称
        year = row[1]  # 第二列为年份
        longitude = row[2]  # 第三列为经度
        latitude = row[3]  # 第四列为纬度

        # 提取气候数据部分（从第5列开始）
        climate_data = row[4:]

        # 将每日气候数据转换为长格式
        for doy, value in enumerate(climate_data, start=1):
            if pd.notna(value) and value != -9999:  # 检查是否为有效值
                long_format_data['site'].append(site)
                long_format_data['year'].append(year)
                long_format_data['doy'].append(doy)
                long_format_data['value'].append(value)
            elif value == -9999:
                # 如果值为-9999，则替换为NaN
                long_format_data['site'].append(site)
                long_format_data['year'].append(year)
                long_format_data['doy'].append(doy)
                long_format_data['value'].append(np.nan)

    # 转换为DataFrame
    df_long = pd.DataFrame(long_format_data)

    # 过滤掉包含NaN的行
    df_long = df_long.dropna(subset=['value']).astype({'doy': int})
    print(df_long)
    return df_long


# 加载物候数据并预处理
def load_phenology_data(path, phase_columns):
    try:
        df = pd.read_csv(path, encoding='gbk')  # 尝试使用gbk编码
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(path, encoding='gb18030')  # 如果gbk失败，尝试使用gb18030编码
        except UnicodeDecodeError:
            raise ValueError("Failed to decode the file with gbk and gb18030 encodings.")
    df = df.melt(id_vars=['site', 'species', 'year'],
                 value_vars=phase_columns,
                 var_name='phase', value_name='doy')
    return df


# 主分析函数
def main():
    # 1. 加载数据
    temp_df = load_climate_data('F:/站点/中国地面/clime/temp.csv')
    precip_df = load_climate_data('F:/站点/中国地面/clime/Preci.csv')

    phase_columns = ['开始展叶期', '展叶盛期', '花序或花蕾出现期', '开花始期',
                     '开花盛期', '开花末期', '果实成熟期', '果实脱落开始期',
                     '果实脱落末期', '叶开始变色期', '叶全部变色期']

    pheno_df = load_phenology_data('F:/站点/中国地面/clime/灌木数据_with_LOS_and_LOS_half.csv', phase_columns)

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
                # 偏相关分析
                corr_ph = pg.partial_corr(data=merged, x='doy_late', y='doy_early',
                                          covar=['temp', 'precip'])
                corr_temp = pg.partial_corr(data=merged, x='doy_late', y='temp',
                                            covar=['doy_early', 'precip'])
                corr_precip = pg.partial_corr(data=merged, x='doy_late', y='precip',
                                              covar=['doy_early', 'temp'])

                # 回归分析
                X = sm.add_constant(merged[['doy_early', 'temp']])
                model = sm.OLS(merged['doy_late'], X)
                result = model.fit()

                # 保存结果
                results.append({
                    'site': site,
                    'species': species,
                    'phase_early': phase1,
                    'phase_late': phase2,
                    'partial_corr_ph': corr_ph['r'].values[0],
                    'partial_corr_temp': corr_temp['r'].values[0],
                    'partial_corr_precip': corr_precip['r'].values[0],
                    'rsquared': result.rsquared
                })
            except Exception as e:
                print(f"An error occurred during analysis for site {site}, species {species}: {e}")
                continue

    # 保存结果
    print(results)

    result_df = pd.DataFrame(results)
    result_df.to_csv('F:/站点/中国地面/clime/clim_carryover_effect_wd.csv', index=False, encoding='gbk')
if __name__ == '__main__':
    main()