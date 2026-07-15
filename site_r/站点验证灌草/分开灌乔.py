import pandas as pd

# 读取分类标准文件
classify_path = r'F:\站点\植物物候观测数据集20161202\新建文件夹\ai植物分类结果com.csv'
df_classify = pd.read_csv(classify_path, encoding='gbk')

# 预处理列名和内容
df_classify.columns = df_classify.columns.str.strip()
df_classify['类型'] = df_classify['类型'].str.strip()
df_classify['植物种名'] = df_classify['植物种名'].str.strip()

# 同时提取灌、草物种列表
shrub_species = df_classify[df_classify['类型'] == '灌']['植物种名'].unique()
tree_species = df_classify[df_classify['类型'] == '乔']['植物种名'].unique()

# 读取待处理数据
data_path = r'F:\站点\植物物候观测数据集20161202\新建文件夹\\木转换结果2.csv'
df_data = pd.read_csv(data_path, encoding='gbk')
df_data.columns = df_data.columns.str.strip()
df_data['植物种名'] = df_data['植物种名'].str.strip()

# 双重筛选
shrub_data = df_data[df_data['植物种名'].isin(shrub_species)]
tree_data = df_data[df_data['植物种名'].isin(tree_species)]

# 提取未分入灌、草的物种数据
other_species = df_data[
    ~df_data['植物种名'].isin(shrub_species) &
    ~df_data['植物种名'].isin(tree_species)
]

# 分别保存
shrub_output = r'F:\站点\植物物候观测数据集20161202\新建文件夹\\筛选后的灌木数据.csv'
tree_output = r'F:\站点\植物物候观测数据集20161202\新建文件夹\\筛选后的乔本数据.csv'

shrub_data.to_csv(shrub_output, index=False, encoding='gbk')
tree_data.to_csv(tree_output, index=False, encoding='gbk')


print(f"筛选完成：\n"
      f"- 灌木数据：{len(shrub_data)}条 -> {shrub_output}\n"
      f"- 其他数据：{len(tree_data)}条 -> {tree_data}")