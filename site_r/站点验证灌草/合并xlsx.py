import os
import pandas as pd

# 指定文件夹路径
folder_path = r'F:\站点\中国地面\中国地面观测物候数据\提交的44个站点08年前数据\提交的44个站点08年前数据'

# 获取文件夹中所有的xlsx文件
xlsx_files = [f for f in os.listdir(folder_path) if f.endswith('.xlsx')]

# 创建一个空的DataFrame来存储合并后的数据
merged_data = pd.DataFrame()

# 循环遍历每个xlsx文件并读取内容
for file in xlsx_files:
    file_path = os.path.join(folder_path, file)
    # 读取Excel文件的内容
    data = pd.read_excel(file_path)
    # 将当前文件的数据追加到merged_data中
    merged_data = pd.concat([merged_data, data], ignore_index=True)

# 将合并后的数据保存到新的Excel文件中
output_file_path = os.path.join(folder_path, 'merged_data.xlsx')
merged_data.to_excel(output_file_path, index=False)

print(f"所有文件已成功合并并保存到 {output_file_path}")



