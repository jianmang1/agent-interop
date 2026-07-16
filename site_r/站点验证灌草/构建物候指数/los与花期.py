import pandas as pd

# 文件路径
grass_file = 'F:\\站点\\中国地面\\草本数据_with_LOS_and_LOS_half.csv'
wood_file = 'F:\\站点\\中国地面\\灌本数据_with_LOS_and_LOS_half.csv'

# 读取CSV文件
grass = pd.read_csv(grass_file, encoding='gbk')
wood = pd.read_csv(wood_file, encoding='gbk')


# 定义一个函数来计算新列
def calculate_new_columns(df):
    # 花期列名
    flower_start_col = '开花始期'
    flower_peak_col = '开花盛期'
    flower_end_col = '开花末期'
    leaf_start_col = '开始展叶期'
    los_col = 'LOS'

    # 新列名
    new_col_start = '花期始-展叶期/LOS'
    new_col_peak = '花期盛-展叶期/LOS'
    new_col_end = '花期末-展叶期/LOS'

    # 初始化新列为NaN
    df[new_col_start] = None
    df[new_col_peak] = None
    df[new_col_end] = None

    # 遍历每一行进行计算
    for index, row in df.iterrows():
        # 检查是否为空值
        if pd.notnull(row[flower_start_col]) and pd.notnull(row[leaf_start_col]) and pd.notnull(row[los_col]):
            df.at[index, new_col_start] = (row[flower_start_col] - row[leaf_start_col]) / row[los_col]
        if pd.notnull(row[flower_peak_col]) and pd.notnull(row[leaf_start_col]) and pd.notnull(row[los_col]):
            df.at[index, new_col_peak] = (row[flower_peak_col] - row[leaf_start_col]) / row[los_col]
        if pd.notnull(row[flower_end_col]) and pd.notnull(row[leaf_start_col]) and pd.notnull(row[los_col]):
            df.at[index, new_col_end] = (row[flower_end_col] - row[leaf_start_col]) / row[los_col]


# 对草本数据和灌本数据分别计算新列
calculate_new_columns(grass)
calculate_new_columns(wood)

# 保存更新后的数据到CSV文件
grass.to_csv(grass_file, index=False, encoding='gbk')
wood.to_csv(wood_file, index=False, encoding='gbk')

print("计算完成并已保存结果！")