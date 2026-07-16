import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 读取 Excel 文件
file_path = r'D:\MODIS43A4_2024\combined_output_2001.xlsx'
df = pd.read_excel(file_path)

# 确保相关列存在
columns_to_check = [
    'sos_value', 'sos_4',
    'pos_value', 'pos_4',
    'eos_value', 'eos_4'
]

if not all(col in df.columns for col in columns_to_check):
    raise ValueError(f"Excel 文件必须包含以下列: {columns_to_check}")

# 提取需要分析的列，并过滤掉值为 0 和 1 的数据
data = df[columns_to_check].replace([0, 1], np.nan).dropna()

# 如果数据为空，则提示错误
if data.empty:
    raise ValueError("所有数据均为 0 或 1 或无效，请检查输入文件")

# 可视化分布曲线
plt.figure(figsize=(15, 8))

# 定义颜色映射
color_map = {
    'sos_value': 'brown',
    'pos_value': 'brown',
    'eos_value': 'brown',
    'sos_4': 'lightgreen',
    'pos_4': 'lightgreen',
    'eos_4': 'lightgreen'
}

# 使用 Seaborn 的 kdeplot 绘制核密度估计曲线
for i in range(0, len(columns_to_check), 6):
    group_columns = columns_to_check[i:i+6]
    for col in group_columns:
        sns.kdeplot(data[col], label=col, linewidth=2, color=color_map[col])

    # 设置图表标题和标签
    plt.title(f'Density of intergroup data distribution curve (Group {i//4 + 1})', fontsize=16)
    plt.xlabel('value', fontsize=12)
    plt.ylabel('Data distribution curve', fontsize=12)
    plt.legend(title="class", fontsize=10, title_fontsize=12)

    # 显示网格
    plt.grid(alpha=0.3)

    # 显示图表
    plt.tight_layout()
    plt.show()



