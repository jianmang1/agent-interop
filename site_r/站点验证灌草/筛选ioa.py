import pandas as pd

# 读取第一个文件并筛选灌木物种
file1_path = 'F:\\站点\\中国地面\\1963-2012\\ioa站点.csv'
df_ai = pd.read_csv(file1_path, encoding='gbk')  # 根据实际编码调整

# 确保列名正确，处理可能的空格
df_ai.columns = df_ai.columns.str.strip()
shrub_species = df_ai.loc[df_ai['类型'].str.strip() == '灌', '站点'].unique()

# 读取第二个文件并筛选匹配项
file2_path = r'F:\站点\中国地面\筛选后的木本数据.csv'
df_wood = pd.read_csv(file2_path, encoding='gbk')
df_wood.columns = df_wood.columns.str.strip()

# 清理植物种名前后的空格
df_wood['站点'] = df_wood['站点'].str.strip()
filtered_wood = df_wood[df_wood['站点'].isin(shrub_species)]

# 保存结果
output_path = r'F:\站点\中国地面\筛选后的木本数据(ioa).csv'
filtered_wood.to_csv(output_path, index=False, encoding='gbk')

print(f"筛选完成，共保留{len(filtered_wood)}条记录。结果已保存至：{output_path}")