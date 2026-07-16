import matplotlib.pyplot as plt
import numpy as np

# 设置字体为Nature常用的字体（如Arial或Times New Roman）
plt.rcParams['font.family'] = 'Arial'  # 或 'Times New Roman'
plt.rcParams['font.size'] = 12         # 主字体大小
plt.rcParams['axes.linewidth'] = 1.5   # 坐标轴线宽

# 创建画布和轴（调整颜色条尺寸）
fig, ax = plt.subplots(figsize=(12, 0.1))  # 水平颜色条，高度较矮

# 定义颜色映射范围
norm = plt.Normalize(0, 365)
cmap = plt.get_cmap('viridis')

# 创建颜色条
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])  # 仅用于颜色条

# 添加颜色条到轴中
cbar = fig.colorbar(sm, cax=ax, orientation='horizontal',
                    ticks=np.arange(0, 366, 60))  # 每60单位一个刻度

# 自定义颜色条样式
cbar.ax.set_xlabel('Days of the Year (0–365)', fontsize=8, weight='bold')  # 标签
cbar.ax.tick_params(labelsize=12, width=1.5, length=0)  # 刻度样式
cbar.outline.set_linewidth(1.5)  # 颜色条边框线宽

# 移除顶部和右侧边框（保持简洁）
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 保存图像（可选，确保高分辨率）
plt.savefig('viridis_colorbar_nature_style.png', dpi=300, bbox_inches='tight')

# 显示图形
plt.show()