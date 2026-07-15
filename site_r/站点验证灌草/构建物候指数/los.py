import pandas as pd
import numpy as np

# 读取草本数据和灌本数据
grass = pd.read_csv('F:\\站点\\中国地面\\筛选后的草本数据(ioa)2.csv', encoding='gbk')
wood = pd.read_csv('F:\\站点\\中国地面\\筛选后的灌本数据(ioa)2.csv', encoding='gbk')

# 定义一个函数用于计算 LOS
def calculate_los(row):
    # 检查是否任意一列为 NaN
    if pd.isna(row['叶全部变色期']) or pd.isna(row['开始展叶期']):
        return np.nan
    # 计算 LOS
    return row['叶全部变色期'] - row['开始展叶期']

# 对草本数据和灌本数据分别计算 LOS 列
grass['LOS'] = grass.apply(calculate_los, axis=1)
wood['LOS'] = wood.apply(calculate_los, axis=1)

# 定义一个函数用于计算 LOS/2
def calculate_los_half(row):
    # 检查 LOS 是否为空
    if pd.isna(row['LOS']):
        return np.nan
    # 计算 LOS/2 列
    return row['开始展叶期'] + row['LOS'] / 2

# 对草本数据和灌本数据分别计算 LOS/2 列
grass['LOS/2'] = grass.apply(calculate_los_half, axis=1)
wood['LOS/2'] = wood.apply(calculate_los_half, axis=1)

# 输出结果以检查
print(grass.head())
print(wood.head())

# 如果需要保存结果到新的 CSV 文件
grass.to_csv('F:\\站点\\中国地面\\草本数据_with_LOS_and_LOS_half.csv', index=False, encoding='gbk')
wood.to_csv('F:\\站点\\中国地面\\灌本数据_with_LOS_and_LOS_half.csv', index=False, encoding='gbk')