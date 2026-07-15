
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import matplotlib.font_manager as fm

# 尝试加载SimHei字体
try:
    simhei_font = fm.FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf')
except IOError:
    print("Error: Could not find the SimHei font file.")
    exit()

# 设置matplotlib使用SimHei字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取Excel文件
file_path = 'F:\\个人\\SOS_CLASS\\2\\wdsosclass_results.xlsx'
xls = pd.ExcelFile(file_path)

# 获取所有工作表的名字
sheet_names = xls.sheet_names

# 定义二级分类编号到名称的映射
classification_map = {
    11: '水田',
    12: '旱地',
    21: '有林地',
    22: '灌木林地',
    23: '疏林地',
    24: '其他林地',
    31: '高覆盖度草地',
    32: '中覆盖度草地',
    33: '低覆盖度草地',
    41: '河渠',
    42: '湖泊',
    43: '水库/坑塘',
    44: '冰川永久积雪',
    45: '海涂',
    46: '滩地',
    51: '城镇',
    52: '农村居民点',
    53: '工交建设用地',
    61: '沙地',
    62: '戈壁',
    63: '盐碱地',
    64: '沼泽地',
    65: '裸土地',
    66: '裸岩石砾地',
    67: '其他未利用地'
}

# 定义一级分类到颜色的映射
color_map = {
    '耕地': 'blue',
    '林地': 'green',
    '草地': 'yellow',
    '水域': 'cyan',
    '城乡、工矿居民用地': 'red',
    '未利用土地': 'gray'
}

# 创建一个新的图形
fig = plt.figure(figsize=(15, 10))
ax = fig.add_subplot(111, projection='3d')

# 遍历每个工作表
for i, sheet in enumerate(sheet_names):
    # 读取工作表数据
    df = pd.read_excel(xls, sheet)

    # 检查数据是否符合预期格式
    if 'Year' not in df.columns:
        print(f"警告：工作表 '{sheet}' 中没有 'Year' 列")
        continue

    # 提取年份和EVI值
    years = df['Year'].values
    evi_columns = ['Min EVI', 'Q1 EVI', 'Median EVI', 'Q3 EVI', 'Max EVI']
    evi_values = df[evi_columns].values

    # 根据工作表名称确定二级分类编号
    classification_number = int(sheet.split('_')[1])
    classification_name = classification_map[classification_number]

    # 确定一级分类名称
    if classification_number in [11, 12]:
        primary_classification = '耕地'
    elif classification_number in [21, 22, 23, 24]:
        primary_classification = '林地'
    elif classification_number in [31, 32, 33]:
        primary_classification = '草地'
    elif classification_number in [41, 42, 43, 44, 45, 46]:
        primary_classification = '水域'
    elif classification_number in [51, 52, 53]:
        primary_classification = '城乡、工矿居民用地'
    elif classification_number in [61, 62, 63, 64, 65, 66, 67]:
        primary_classification = '未利用土地'
    else:
        primary_classification = '未知'

    # 获取对应的颜色
    color = color_map.get(primary_classification, 'black')

    # 计算每个年份的位置偏移量，以便于在同一个x坐标上显示多个柱型图
    positions = np.arange(len(years)) + (i - len(sheet_names) / 2) * 0.1

    # 绘制柱型图
    for j, year in enumerate(years):
        # 对于每个年份，获取对应的EVI值
        min_evi, q1_evi, median_evi, q3_evi, max_evi = evi_values[j, :]

        # 绘制柱型图
        ax.bar3d(positions[j], i, min_evi, 0.05, 0.8, q3_evi - q1_evi, color=color, shade=True)

        # 绘制箱形图的其他要素
        ax.plot([positions[j], positions[j]], [i, i], [min_evi, q1_evi], color='black')  # 最小值到第一四分位数
        ax.plot([positions[j], positions[j]], [i, i], [q3_evi, max_evi], color='black')  # 第三四分位数到最大值
        ax.plot([positions[j], positions[j]], [i - 0.4, i + 0.4], [median_evi, median_evi], color='red')  # 中位数

# 设置轴标签
ax.set_xlabel('Years')
ax.set_ylabel('Land Cover Classes')
ax.set_zlabel('EVI Values')

# 设置y轴刻度为地物分类
ax.set_yticks(np.arange(len(sheet_names)))
ax.set_yticklabels([classification_map[int(sheet.split('_')[1])] for sheet in sheet_names])

# 设置x轴刻度为年份
ax.set_xticks(np.arange(len(years)))
ax.set_xticklabels(years)

plt.show()