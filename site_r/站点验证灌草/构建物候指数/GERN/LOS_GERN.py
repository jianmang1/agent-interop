import pandas as pd
import numpy as np

# 读取草本数据和灌本数据
grass = pd.read_csv('F:\站点\植物物候观测数据集20161202\\gl.csv', encoding='gbk')
wood = pd.read_csv('F:\站点\植物物候观测数据集20161202\\wd.csv', encoding='gbk')

# 定义一个函数用于计算 LOS Budburst	Flower	Fruit	Coloration
def calculate_los(row):
    # 检查是否任意一列为 NaN
    if pd.isna(row['Coloration']) or pd.isna(row['Budburst']):
        return np.nan
    # 计算 LOS
    return row['Coloration'] - row['Budburst']

# 对草本数据和灌本数据分别计算 LOS 列
grass['LOS'] = grass.apply(calculate_los, axis=1)
wood['LOS'] = wood.apply(calculate_los, axis=1)

# 定义一个函数用于计算 LOS/2
def calculate_los_half(row):
    # 检查 LOS 是否为空
    if pd.isna(row['LOS']):
        return np.nan
    # 计算 LOS/2 列
    return row['Budburst'] + row['LOS'] / 2

# 对草本数据和灌本数据分别计算 LOS/2 列
grass['LOS/2'] = grass.apply(calculate_los_half, axis=1)
wood['LOS/2'] = wood.apply(calculate_los_half, axis=1)

# 输出结果以检查
print(grass.head())
print(wood.head())

# 如果需要保存结果到新的 CSV 文件
grass.to_csv('F:\站点\植物物候观测数据集20161202\\glwith_LOS.csv', index=False, encoding='gbk')
wood.to_csv('F:\站点\植物物候观测数据集20161202\\wdwith_LOS.csv', index=False, encoding='gbk')