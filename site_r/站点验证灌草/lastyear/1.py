import pandas as pd

# 读取草本和灌木数据
grass_mean = pd.read_csv('F:\\站点\\中国地面\\草本数据_每年均值.csv', encoding='gbk')
wood_mean = pd.read_csv('F:\\站点\\中国地面\\灌本数据_每年均值.csv', encoding='gbk')


# 定义一个函数动态计算 lastyear_LOS
def add_lastyear_los(df):
    # 创建一个新的列 lastyear_LOS，默认值为 NaN
    df['lastyear_LOS'] = None

    # 按站点分组处理
    for site_id, group in df.groupby('站点'):
        # 将分组数据按年份排序
        group = group.sort_values(by='年份')

        # 遍历每一行，查找上一年的 LOS
        for i, row in group.iterrows():
            current_year = row['年份']
            previous_year = current_year - 1

            # 查找上一年的数据
            previous_row = group[group['年份'] == previous_year]

            if not previous_row.empty:
                # 如果找到上一年的数据，则填充其 LOS 值
                df.at[i, 'lastyear_LOS'] = previous_row.iloc[0]['LOS']

    return df


# 添加 lastyear_LOS 列
grass_mean = add_lastyear_los(grass_mean)
wood_mean = add_lastyear_los(wood_mean)

# 保存更新后的数据
grass_mean.to_csv('F:\\站点\\中国地面\\草本数据_每年均值.csv', index=False, encoding='gbk')
wood_mean.to_csv('F:\\站点\\中国地面\\灌本数据_每年均值.csv', index=False, encoding='gbk')