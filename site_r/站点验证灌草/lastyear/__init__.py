import pandas as pd

# 定义物候期列名
pheno_columns = [
    '开始展叶期', '展叶盛期',
    '花序或花蕾出现期', '开花始期', '开花盛期',
    '开花末期', '果实成熟期',
    '果实脱落开始期', '果实脱落末期', '叶开始变色期',
    '叶全部变色期'
]

# 读取 CSV 文件
grass = pd.read_csv('F:\\站点\\中国地面\\草本数据_with_LOS_and_LOS_half.csv', encoding='gbk')
wood = pd.read_csv('F:\\站点\\中国地面\\灌本数据_with_LOS_and_LOS_half.csv', encoding='gbk')

# 检查数据是否正确加载
print("草本数据前几行：")
print(grass.head())
print("\n灌本数据前几行：")
print(wood.head())

# 定义一个函数来处理每个数据集
def calculate_mean_phenology(df, pheno_columns):
    # 确保年份和站点列为字符串类型（如果需要）
    df['年份'] = df['年份'].astype(str)
    df['站点'] = df['站点'].astype(str)

    # 分组：按站点和年份计算 LOS 和物候期的均值
    grouped = df.groupby(['站点', '年份']).agg({
        'LOS': 'mean',  # 计算 LOS 的均值
        **{col: 'mean' for col in pheno_columns}  # 计算每个物候期的均值
    }).reset_index()

    return grouped

# 对草本数据和灌本数据分别计算
grass_mean = calculate_mean_phenology(grass, pheno_columns)
wood_mean = calculate_mean_phenology(wood, pheno_columns)

# 输出结果到 CSV 文件
grass_mean.to_csv('F:\\站点\\中国地面\\草本数据_每年均值.csv', index=False, encoding='gbk')
wood_mean.to_csv('F:\\站点\\中国地面\\灌本数据_每年均值.csv', index=False, encoding='gbk')

print("计算完成，结果已保存到文件！")