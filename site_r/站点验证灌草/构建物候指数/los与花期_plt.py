import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.font_manager import FontProperties

# 使用支持中文的字体（请确保路径正确）
font_path = 'C:/Windows/Fonts/simhei.ttf'  # 替换为您的系统中实际存在的中文字体路径
font = FontProperties(fname=font_path)

# 文件路径
grass_file = 'F:\\站点\\中国地面\\草本数据_with_LOS_and_LOS_half.csv'
wood_file = 'F:\\站点\\中国地面\\灌本数据_with_LOS_and_LOS_half.csv'

# 指定站点
sites_of_interest = ['泰安', '民勤', '哈尔滨', '银川', '牡丹江', '北京', '长春']

# 读取CSV文件
grass = pd.read_csv(grass_file, encoding='gbk')
wood = pd.read_csv(wood_file, encoding='gbk')

# 定义新列名
new_cols = ['花期始-展叶期/LOS', '花期盛-展叶期/LOS', '花期末-展叶期/LOS']


# 计算指定站点的平均值
def calculate_site_averages(df, sites):
    site_data = {}
    for site in sites:
        site_rows = df[df['站点'] == site]
        if not site_rows.empty:
            averages = site_rows[new_cols].mean()
            site_data[site] = averages
    return site_data


# 获取草本和灌木数据的站点平均值
grass_averages = calculate_site_averages(grass, sites_of_interest)
wood_averages = calculate_site_averages(wood, sites_of_interest)

# 绘制柱状图
fig, ax = plt.subplots(figsize=(15, 7))

# 设置柱状图宽度和位置
bar_width = 0.05
r = range(len(sites_of_interest))

# 绘制
for i, col in enumerate(new_cols):
    grass_values = [grass_averages[site][col] if site in grass_averages else 0 for site in sites_of_interest]
    wood_values = [wood_averages[site][col] if site in wood_averages else 0 for site in sites_of_interest]

    # 草本数据
    ax.bar([p + i * 2 * bar_width for p in r], grass_values, width=bar_width,
           label=f'草本-{col}' if i == 0 else "", color='#2C5C8A', alpha=0.7)
    # 灌木数据
    ax.bar([p + i * 2 * bar_width + bar_width for p in r], wood_values, width=bar_width,
           label=f'灌木-{col}' if i == 0 else "", color='#CC6633', alpha=0.7)

# 设置横坐标标签
ax.set_xticks([p + 1.5 * bar_width for p in r])
ax.set_xticklabels(sites_of_interest, fontproperties=font)

# 设置图例
legend_handles = [
    Patch(facecolor='#2C5C8A', label='草本'),
    Patch(facecolor='#CC6633', label='灌木')
]
plt.legend(handles=legend_handles, loc='upper left', prop=font)

# 设置标题和轴标签
ax.set_title('各花期在生长季长度上的比例', fontproperties=font)
ax.set_xlabel('站点', fontproperties=font)
ax.set_ylabel('比例', fontproperties=font)

# 显示图表
plt.tight_layout()
plt.show()