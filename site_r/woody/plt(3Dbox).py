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
file_path = 'F:\\个人\\allsos_class_results.xlsx'
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

# 创建一个新的图形
fig, ax = plt.subplots(figsize=(15, 10))

# 准备热图数据矩阵
heat_data = []
years = None
for sheet in sheet_names:
    # 读取工作表数据
    df = pd.read_excel(xls, sheet)

    # 检查数据是否符合预期格式
    if 'Year' not in df.columns:
        print(f"警告：工作表 '{sheet}' 中没有 'Year' 列")
        continue

    # 如果这是第一个工作表，设置years变量
    if years is None:
        years = df['Year'].values

    # 提取EVI值的中位数列
    evi_median = df['Median EVI'].values

    # 添加到热图数据矩阵
    heat_data.append(evi_median)

# 转置热图数据矩阵以匹配时间轴和类别轴
heat_data = np.array(heat_data).T

# 绘制热图
cax = ax.imshow(heat_data, cmap='coolwarm', aspect='auto')

# 设置颜色条
cbar = fig.colorbar(cax)
cbar.set_label('EVI Median Value')

# 设置x轴标签
ax.set_xticks(np.arange(len(sheet_names)))
ax.set_xticklabels([classification_map[int(sheet.split('_')[1])] for sheet in sheet_names], rotation=90)

# 设置y轴标签
ax.set_yticks(np.arange(len(years)))
ax.set_yticklabels(years)

# 设置标题和轴标签
ax.set_title('各年份不同地类EVI中位数值热图')
ax.set_xlabel('地类')
ax.set_ylabel('年份')

plt.tight_layout()
plt.show()