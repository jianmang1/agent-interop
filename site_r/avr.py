import pandas as pd

# 读取Excel文件
file_path = 'F:\个人\class_cov\新建文件夹\新建文件夹\新建文件夹.xlsx'
xlsx = pd.ExcelFile(file_path)

# 存储结果的列表
results = []

# 遍历每个工作表
for sheet_name in xlsx.sheet_names:
    df = pd.read_excel(xlsx, sheet_name=sheet_name)
    mean_grassland_cover = df['Mean Grassland Cover'].mean()
    results.append({"工作表": sheet_name, "Mean Grassland Cover 平均值": mean_grassland_cover})

# 将结果转换为DataFrame
results_df = pd.DataFrame(results)

# 打印结果
print(results_df)

# 将结果导出到Excel
results_df.to_excel('mean_grassland_cover_averages.xlsx', index=False)

print("数据已导出到 mean_grassland_cover_averages.xlsx")