import os
import pandas as pd

# 指定文件夹路径
folder_path = r'F:\站点\中国地面\中国地面观测物候数据\2014年观测报表\2014年观测报表'

# 获取文件夹中所有的xls和xlsx文件
file_extensions = ('.xlsx', '.xls')
files = [f for f in os.listdir(folder_path) if f.lower().endswith(file_extensions)]

# 创建临时文件路径
temp_folder_path = os.path.join(folder_path, 'temp_merge')
os.makedirs(temp_folder_path, exist_ok=True)

# 临时文件名
temp_wood_file = os.path.join(temp_folder_path, 'temp_wood_data.xlsx')
temp_grass_file = os.path.join(temp_folder_path, 'temp_grass_data.xlsx')

# 初始化临时文件
pd.DataFrame().to_excel(temp_wood_file, index=False, header=False)
pd.DataFrame().to_excel(temp_grass_file, index=False, header=False)

# 循环遍历每个文件并读取内容
for file in files:
    file_path = os.path.join(folder_path, file)
    # 确定文件类型并选择合适的引擎
    engine = 'openpyxl' if file.lower().endswith('.xlsx') else 'xlrd'

    try:
        # 使用ExcelFile读取工作表列表
        xls = pd.ExcelFile(file_path, engine=engine)
        sheet_names = xls.sheet_names

        # 检查是否存在“木本植物”工作表并合并
        if '木本植物' in sheet_names:
            wood_data = pd.read_excel(xls, '木本植物', header=None, engine=engine)
            # 过滤掉所有列都为空的行
            wood_data = wood_data.dropna(how='all')
            # 将文件名作为一行放在数据的上方
            file_name_row = pd.DataFrame([[file]], columns=[0])
            wood_data_with_filename = pd.concat([file_name_row, wood_data], ignore_index=True)
            # 将当前文件的数据追加到临时文件中
            with pd.ExcelWriter(temp_wood_file, mode='a', if_sheet_exists='overlay') as writer:
                wood_data_with_filename.to_excel(writer, index=False, header=False,
                                                 startrow=pd.read_excel(temp_wood_file).shape[0])

        # 检查是否存在“草本植物”工作表并合并
        if '草本植物' in sheet_names:
            grass_data = pd.read_excel(xls, '草本植物', header=None, engine=engine)
            # 过滤掉所有列都为空的行
            grass_data = grass_data.dropna(how='all')
            # 将文件名作为一行放在数据的上方
            file_name_row = pd.DataFrame([[file]], columns=[0])
            grass_data_with_filename = pd.concat([file_name_row, grass_data], ignore_index=True)
            # 将当前文件的数据追加到临时文件中
            with pd.ExcelWriter(temp_grass_file, mode='a', if_sheet_exists='overlay') as writer:
                grass_data_with_filename.to_excel(writer, index=False, header=False,
                                                  startrow=pd.read_excel(temp_grass_file).shape[0])
    except Exception as e:
        print(f"无法处理文件 {file}: {e}")

# 将临时文件重命名为最终输出文件
output_file_path_wood = os.path.join(folder_path, 'merged_wood_data.xlsx')
output_file_path_grass = os.path.join(folder_path, 'merged_grass_data.xlsx')

os.rename(temp_wood_file, output_file_path_wood)
os.rename(temp_grass_file, output_file_path_grass)

print(f"木本植物数据已成功合并并保存到 {output_file_path_wood}")
print(f"草本植物数据已成功合并并保存到 {output_file_path_grass}")



