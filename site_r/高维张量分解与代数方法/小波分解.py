import rasterio
import numpy as np
import pywt
import matplotlib.pyplot as plt
from scipy.interpolate import NearestNDInterpolator

# 读取遥感数据并处理无效值
file_path = r'D:\MODIS43A4_2024\LOS\mean_values.tif'
with rasterio.open(file_path) as src:
    data = src.read(1)
    data[data == -9999] = np.nan

# 最近邻插值填补缺失值
rows, cols = np.indices(data.shape)
valid_mask = ~np.isnan(data)
interpolator = NearestNDInterpolator(
    np.column_stack((rows[valid_mask], cols[valid_mask])),
    data[valid_mask]
)
data_filled = interpolator(rows, cols)

# 多尺度小波分解
wavelet = 'sym5'  # 使用对称小波减少边界效应
level = 4         # 分解层级
coeffs = pywt.wavedec2(data_filled, wavelet, mode='periodization', level=level)

# 计算多尺度能量特征
energy_dict = {'Approximation': []}
for direction in ['Horizontal', 'Vertical', 'Diagonal']:
    energy_dict[direction] = []

for i, coeff in enumerate(coeffs):
    if i == 0:
        energy_dict['Approximation'].append(np.mean(coeff**2))
    else:
        for j, direction in enumerate(['Horizontal', 'Vertical', 'Diagonal']):
            energy_dict[direction].append(np.mean(coeff[j]**2))

# 可视化能量分布
plt.figure(figsize=(12, 6))
x = range(1, level+1)
plt.plot(x, energy_dict['Horizontal'], 'ro-', label='Horizontal Detail')
plt.plot(x, energy_dict['Vertical'], 'gs-', label='Vertical Detail')
plt.plot(x, energy_dict['Diagonal'], 'b^-', label='Diagonal Detail')
plt.xticks(x, [f'Level {i}' for i in x])
plt.ylabel('Normalized Energy')
plt.title('Multiscale Spatial Feature Energy Distribution')
plt.legend()
plt.grid(True)
plt.show()

# 创建多尺度特征图谱
fig, axes = plt.subplots(level+2, 3, figsize=(18, 6*(level+2)))

# 原始数据可视化
axes[0, 1].imshow(data_filled, cmap='viridis')
axes[0, 1].set_title('Original Data (Interpolated)')
for ax in [axes[0,0], axes[0,2]]:
    ax.axis('off')

# 各尺度特征可视化
visualization_levels = {
    'Approximation': {'cmap': 'plasma', 'title': 'Structural Pattern'},
    'Horizontal': {'cmap': 'coolwarm', 'title': 'East-West Features'},
    'Vertical': {'cmap': 'PiYG', 'title': 'North-South Features'},
    'Diagonal': {'cmap': 'PRGn', 'title': 'Diagonal Features'}
}

for lvl in range(1, level+1):
    current_coeff = coeffs[lvl]
    for idx, (detail, params) in enumerate(visualization_levels.items()):
        if detail == 'Approximation':
            continue
        ax = axes[lvl, idx-1]
        img = current_coeff[idx-1] if detail != 'Approximation' else coeffs[0]
        ax.imshow(img, cmap=params['cmap'],
                 vmin=np.percentile(img, 5),
                 vmax=np.percentile(img, 95))
        ax.set_title(f'{params["title"]} Level {lvl}')
        ax.axis('off')

plt.tight_layout()
plt.show()