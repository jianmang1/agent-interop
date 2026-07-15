import pandas as pd
from datetime import datetime

# 读取CSV文件
df = pd.read_csv('F:\站点\植物物候观测数据集20161202\木本植物物候观测数据集2.csv', encoding='gbk')
# 指定生态站代码列表
station_codes = ['BJF', 'NMG', 'HBG', 'LZD', 'NMD', 'SPD', 'CLD', 'ESD', 'FKD']

# 筛选指定生态站代码的行
filtered_df = df[df['生态站代码'].isin(station_codes)]

# 定义日期列名 芽开放期（月/日/年）	展叶期（月/日/年）	开花始期（月/日/年）	开花盛期（月/日/年）	果实或种子成熟期（月/日/年）	叶秋季变色期（月/日/年）	落叶期（月/日/年）
date_columns = [
    '芽开放期（月/日/年）',
    '展叶期（月/日/年）',
    '开花始期（月/日/年）',
    '果实或种子成熟期（月/日/年）',
    '叶秋季变色期（月/日/年）',
    '落叶期（月/日/年）'
]

# 将日期转换为年积日（儒略日）
def date_to_julian(date_str):
    if pd.isna(date_str) or date_str.strip() == '':
        return None
    try:
        date = datetime.strptime(date_str, '%m/%d/%Y')
        return date.timetuple().tm_yday
    except:
        return None

# 对每个日期列应用转换
for col in date_columns:
    julian_col = f'{col}（儒略日）'
    filtered_df[julian_col] = filtered_df[col].apply(date_to_julian)

# 导出结果到CSV
filtered_df.to_csv('F:\站点\植物物候观测数据集20161202\木转换结果.csv', index=False, encoding='utf-8-sig')

print("木转换完成，结果已保存为 转换结果.csv")