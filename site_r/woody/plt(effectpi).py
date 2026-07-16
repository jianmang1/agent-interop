import pandas as pd
import matplotlib.pyplot as plt

# 加载Excel文件
file_path = 'F:\个人\effectpi\ioa.xlsx'  # 这里请确保文件路径正确
sheet_name = 'Sheet1'
data = pd.read_excel(file_path, sheet_name=sheet_name)

# 绘制柱状图
fig, ax1 = plt.subplots()

color = 'tab:blue'
ax1.set_xlabel('Year (MCD12Q2)')
ax1.set_ylabel('MCD12Q2', color=color)
ax1.bar(data['MCD12Q2'], data['pen1'], color=color, label='MCD12Q2')
ax1.tick_params(axis='y', labelcolor=color)

# 创建第二个y轴
ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('MCD43A4', color=color)
ax2.plot(data['MCD12Q2'], data['pen2'], color=color, linestyle='-', marker='o', label='MCD43A4')
ax2.tick_params(axis='y', labelcolor=color)

# 添加标题
plt.title('MCD12Q2 and MCD43A4 values over years')

# 显示图例
fig.tight_layout()
ax1.legend(loc='upper left')
ax2.legend(loc='upper right')

# 显示图表
plt.show()