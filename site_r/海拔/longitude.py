import os
import pandas as pd
import numpy as np
from scipy.stats import linregress

# 设置工作目录和文件路径
base_path = r"D:\海拔\1"
output_file = os.path.join(base_path, "slope_sd_results_combined.csv")

# 初始化结果存储列表
results = []

# 定义需要处理的数据集
datasets = [
    {"prefix": "eos", "variable": "EOS"},
    {"prefix": "sos", "variable": "SOS"},
    {"prefix": "pos", "variable": "POS"}

]

# 遍历每个数据集
for dataset in datasets:
    prefix = dataset["prefix"]
    variable = dataset["variable"]

    # 遍历从 2001 到 2024 的所有文件
    for year in range(2001, 2025):
        file_name = f"{prefix}_{year}_data.csv"
        file_path = os.path.join(base_path, file_name)

        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"文件 {file_name} 不存在，跳过。")
            continue

        # 读取 CSV 文件
        try:
            data = pd.read_csv(file_path)
        except Exception as e:
            print(f"读取文件 {file_name} 时出错：{e}")
            continue

        # 确保数据包含必要的列
        if variable not in data.columns or 'longitude' not in data.columns:
            print(f"文件 {file_name} 缺少必要的列（{variable} 或 longitude），跳过。")
            continue

        # 清理数据：删除空值，并确保数据类型正确
        # 清理数据：删除空值、确保数据类型正确，并删除 data[variable] 值为 1 的行
        data = data.dropna(subset=[variable, 'longitude'])  # 删除 variable 和 DEM 列中的空值
        data[variable] = pd.to_numeric(data[variable], errors='coerce')  # 确保变量列是数值类型
        data['longitude'] = pd.to_numeric(data['longitude'], errors='coerce')  # 确保 DEM 列是数值类型
        data = data[(data[variable].notnull()) & (data['longitude'].notnull())]  # 删除转换后仍为空值的行

        # 检查数据量是否足够
        if len(data) < 2:
            print(f"文件 {file_name} 数据量不足，跳过。")
            continue

        # 处理 DEM 数据（除以 1000）
        dem = data['longitude']
        var_data = data[variable]

        # 计算线性回归的斜率和截距
        try:
            slope, intercept, r_value, p_value, std_err = linregress(dem, var_data)
        except Exception as e:
            print(f"计算线性回归时出错（文件 {file_name}）：{e}")
            continue

        # 计算残差的标准差（SD）
        predicted_var = slope * dem + intercept
        residuals = var_data - predicted_var
        sd = np.std(residuals, ddof=1)  # 使用样本标准差

        # 将结果添加到列表中
        results.append({
            'Dataset': prefix.upper(),
            'Year': year,
            'Slope': slope,
            'SD': sd
        })

# 将结果导出为 CSV 文件
if results:
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_file, index=False)
    print(f"结果已成功导出到 {output_file}")
else:
    print("没有处理任何文件，未生成输出文件。")