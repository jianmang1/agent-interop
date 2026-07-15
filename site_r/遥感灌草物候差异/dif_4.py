import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 读取 Excel 文件
file_path = r'D:\MODIS43A4_2024\combined_output2.xlsx'
df = pd.read_excel(file_path)

# 确保相关列存在
columns_to_check = [
    'sos_31', 'sos_32', 'sos_33', 'sos_61', 'sos_62', 'sos_63', 'sos_64', 'sos_65', 'sos_66',
    'pos_31', 'pos_32', 'pos_33', 'pos_61', 'pos_62', 'pos_63', 'pos_64', 'pos_65', 'pos_66',
    'eos_31', 'eos_32', 'eos_33', 'eos_61', 'eos_62', 'eos_63', 'eos_64', 'eos_65', 'eos_66',
]

if not all(col in df.columns for col in columns_to_check):
    raise ValueError(f"Excel 文件必须包含以下列: {columns_to_check}")

# 定义图例映射
legend_mapping = {
    '_value': '灌木',
    '_31': '高覆盖度草地',
    '_32': '中覆盖度草地',
    '_33': '低覆盖度草地',
    '_61': '沙地',
    '_62': '戈壁',
    '_63': '盐碱地',
    '_64': '沼泽地',
    '_65': '裸地',
    '_66': '裸岩石砾地'
}

print("数据列:", columns_to_check)

# 提取需要分析的列，并过滤掉值为 0 的数据
data = df[columns_to_check].replace(0, np.nan)
print("数据预览:")
print(data.head())

# 如果数据为空，则提示错误
if data.empty:
    raise ValueError("所有数据均为 0 或无效，请检查输入文件")

# 定义颜色列表
colors = plt.cm.tab20(np.linspace(0, 1, len(columns_to_check)))

# 分组绘制图表 - 按照 sos, pos, eos 分组
groups = ['sos', 'pos', 'eos']
for group_name in groups:
    plt.figure(figsize=(15, 8))

    # 获取当前组的列
    current_group_cols = [col for col in columns_to_check if col.startswith(group_name)]

    # 为当前组绘制核密度估计曲线
    for idx, col in enumerate(current_group_cols):
        # 根据列名确定类型
        suffix = col.split('_', 1)[1]  # 获取后缀部分
        for key, value in legend_mapping.items():
            if suffix == key[1:]:  # 去掉下划线前缀进行匹配
                label_name = f"{group_name}_{suffix} ({value})"
                break
        else:
            label_name = col

        sns.kdeplot(data[col], label=label_name, linewidth=2, color=colors[idx % len(colors)])

    # 设置图表标题和标签
    phase_name = {"sos": "生长季开始期", "pos": "生长季峰值期", "eos": "生长季结束期"}[group_name]
    plt.title(f'{phase_name}数据分布密度曲线', fontsize=16)
    plt.xlabel('数值', fontsize=12)
    plt.ylabel('密度', fontsize=12)
    plt.legend(title="植被类型", fontsize=10, title_fontsize=12, bbox_to_anchor=(1.05, 1), loc='upper left')

    # 显示网格
    plt.grid(alpha=0.3)

    # 调整布局以适应图例
    plt.tight_layout()
    plt.show()

# 整体对比图 - 将所有数据绘制在一个图中
plt.figure(figsize=(20, 12))

# 定义不同阶段的颜色分组
phase_colors = {'sos': '#1f77b4', 'pos': '#ff7f0e', 'eos': '#2ca02c'}

for idx, col in enumerate(columns_to_check):
    # 获取阶段和类型
    phase = col.split('_')[0]
    suffix = col.split('_', 1)[1]

    # 根据后缀获取中文名称
    type_name = ""
    for key, value in legend_mapping.items():
        if suffix == key[1:]:
            type_name = value
            break

    label_name = f"{phase.upper()}_{type_name}"
    color = phase_colors.get(phase, '#000000')

    sns.kdeplot(data[col], label=label_name, linewidth=1.5, alpha=0.7, color=color)

plt.title('所有物候期数据分布密度曲线对比', fontsize=16)
plt.xlabel('数值', fontsize=12)
plt.ylabel('密度', fontsize=12)
plt.legend(title="物候期_植被类型", fontsize=9, title_fontsize=10, bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
