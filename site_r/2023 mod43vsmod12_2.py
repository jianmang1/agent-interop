import rasterio
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from matplotlib import ticker
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import numpy as np  # 导入 numpy 模块

# 设置 Nature 风格参数（手动配置）
plt.rcParams.update({
    'font.family': 'Times New Roman',  # 字体
    'font.size': 12,  # 字号
    'axes.linewidth': 1.5,  # 坐标轴线宽
    'xtick.major.width': 1.5,
    'ytick.major.width': 1.5,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'axes.titlesize': 14,
    'axes.labelsize': 14,
    'legend.fontsize': 12,
})

# 文件路径列表
file_paths = [
    r"D:\MOD12Q2\dif\difsos2.tif",
    r"D:\MOD12Q2\dif\difeos2.tif",
    r"D:\MOD12Q2\dif\diflos2.tif",
]

# 创建画布和子图
fig, axes = plt.subplots(1, 3, figsize=(18, 6), subplot_kw={
    'projection': ccrs.PlateCarree()
}, constrained_layout=True)

# 全局颜色映射和颜色条参数
cmap = plt.get_cmap('coolwarm')  # 尝试使用不同的颜色映射
vmin, vmax = -20, 20  # 调整 vmin 和 vmax 的范围以更好地展示稀疏的点
norm = plt.Normalize(vmin=vmin, vmax=vmax)

# 读取并绘图
images = []
for i, path in enumerate(file_paths):
    with rasterio.open(path) as src:
        data = src.read(1)
        transform = src.transform
        x = transform[2] + transform[0] * np.arange(data.shape[1])
        y = transform[5] + transform[4] * np.arange(data.shape[0])

    # 绘制图像
    im = axes[i].pcolormesh(x, y, data, cmap=cmap, norm=norm, transform=ccrs.PlateCarree())
    images.append(im)

    # 添加地理信息
    axes[i].coastlines(resolution='10m', color='black', linewidth=0.8)
    axes[i].set_title(path.split("\\")[-1].replace(".tif", ""), fontsize=14)

    # 设置经纬度网格
    gl = axes[i].gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 10, 'color': 'gray'}
    gl.ylabel_style = {'size': 10, 'color': 'gray'}

# 添加颜色条
cbar_ax = fig.add_axes([0.1, 0.05, 0.8, 0.03])  # [left, bottom, width, height]
cbar = fig.colorbar(images[0], cax=cbar_ax, orientation='horizontal', extend='both')
cbar.set_label('Difference Value', fontsize=12)
cbar.ax.tick_params(labelsize=10)

plt.show()



