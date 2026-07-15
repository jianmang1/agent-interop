import pandas as pd

# 假设数据存储在一个名为 'data.csv' 的 CSV 文件中
# 读取CSV文件
df = pd.read_csv('F:\\站点\\中国地面\\筛选后的灌本数据(ioa).csv', encoding='gbk')

# 按照 '年份', '站点', '植物种名' 列进行排序
df_sorted = df.sort_values(by=['年份', '站点', '植物种名'])

# 去除重复的行，只保留第一个出现的实例
df_unique = df_sorted.drop_duplicates(subset=['年份', '站点', '植物种名'], keep='first')

# 将结果保存到一个新的CSV文件中
df_unique.to_csv('F:\站点\中国地面\筛选后的灌本数据(ioa)2.csv',encoding='gbk')

print("去重后的数据已保存到 unique_data.csv")



