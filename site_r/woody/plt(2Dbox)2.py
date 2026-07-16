import pandas as pd
import matplotlib.pyplot as plt
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
file_path = 'F:\\个人\\SOS_CLASS\\2\\glsosclass_results.xlsx'
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
fig, axes = plt.subplots(nrows=len(sheet_names), ncols=1, figsize=(15, 5 * len(sheet_names)), sharex=True)

# 如果只有一个子图，将其转换为列表以便迭代
if len(sheet_names) == 1:
    axes = [axes]

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

    # 绘制箱形图
    for j, year in enumerate(years):
        # 对于每个年份，获取对应的EVI值
        min_evi, q1_evi, median_evi, q3_evi, max_evi = evi_values[j, :]

        # 绘制箱形图
        box_data = [min_evi, q1_evi, median_evi, q3_evi, max_evi]
        box = axes[i].boxplot([box_data], positions=[j], widths=0.6, patch_artist=True)

        # 设置箱形图的颜色
        for patch in box['boxes']:
            patch.set_facecolor(color)

        # 添加中位数线
        for median in box['medians']:
            median.set_color('red')

        # 添加最小值和最大值线
        for whisker in box['whiskers']:
            whisker.set_color('black')

        # 添加帽线
        for cap in box['caps']:
            cap.set_color('black')

        # 添加离群点
        for flier in box['fliers']:
            flier.set_markerfacecolor('black')

    # 设置子图标题
    axes[i].set_title(f'{classification_name} ({primary_classification})', fontproperties=simhei_font)
    axes[i].set_ylabel('EVI Values', fontproperties=simhei_font)

# 设置x轴标签
plt.xlabel('Years', fontproperties=simhei_font)
plt.xticks(np.arange(len(years)), years, fontproperties=simhei_font)

# 调整布局
plt.tight_layout()

plt.show()