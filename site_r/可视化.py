import os
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# 定义路径
raster_dir = r'D:\MODIS43A4_2024\POS'
output_dir = r'D:\MODIS43A4_2024\POS\output3'

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)

# 定义要可视化的栅格文件名
raster_files = [
    'mean_values.tif',
    'rmse_values.tif',
    'slope_values.tif',
    'p_values.tif'
]
for raster_file in raster_files:
    # 构建完整的栅格文件路径
    raster_path = os.path.join(raster_dir, raster_file)

    with rasterio.open(raster_path) as src:
        data = src.read(1)  # 假设每个文件只有一个波段
        transform = src.transform
        bounds = src.bounds
        crs = src.crs

        # 将无效值（包括原始nodata值和小于-10的值，以及值为0和-9999的像元）设置为NaN以便后续处理
        invalid_values = [0, -9999]
        for value in invalid_values:
            data[data == value] = np.nan

        # 对于 mean_values.tif 文件，设定固定的颜色条范围
        if raster_file == 'mean_values.tif':
            vmin, vmax = 120, 240
        else:
            valid_data = data[np.isfinite(data)]  # 排除NaN和Inf
            vmin, vmax = np.min(valid_data), np.max(valid_data)

        # 打印调试信息
        print(f"Processing {raster_file}:")
        print(f"  Data shape: {data.shape}")
        print(f"  Valid data min: {np.nanmin(data)}, max: {np.nanmax(data)}")
        print(f"  Colorbar range: vmin={vmin}, vmax={vmax}")

        # 定义边界和颜色映射
        bounds_cmap = np.linspace(vmin, vmax, 11)  # 10个等级
        colors = plt.cm.viridis(np.linspace(0, 1, len(bounds_cmap)-1))
        cmap = LinearSegmentedColormap.from_list('custom_cmap', colors)
        norm = BoundaryNorm(bounds_cmap, cmap.N)

        # 将无效像元值（NaN）设置为透明
        transparent_color = np.array([[0, 0, 0, 0]])  # RGBA for fully transparent
        cmap.set_bad(transparent_color)  # 使用set_bad()来设置无效值的颜色为透明

        # 可视化栅格
        fig, ax = plt.subplots(1, 1, figsize=(8, 6), subplot_kw={'projection': ccrs.PlateCarree()}, facecolor='white')

        # 添加中国地图
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.STATES, linestyle=':')
        ax.set_extent([bounds.left, bounds.right, bounds.bottom, bounds.top], crs=ccrs.PlateCarree())

        # 绘制栅格数据
        im = ax.imshow(data, cmap=cmap, norm=norm, extent=[bounds.left, bounds.right, bounds.bottom, bounds.top],
                       transform=ccrs.PlateCarree(), interpolation='none')  # 禁用插值

        # 调整颜色条的位置和长度
        cbar = fig.colorbar(im, ax=ax, orientation='horizontal', pad=0.04, shrink=1.0, extend='both')
        cbar.set_label('Pixel Value')

        plt.axis('off')  # 关闭坐标轴

        # 保存图像
        output_image = os.path.join(output_dir, f"{os.path.splitext(raster_file)[0]}.png")
        plt.savefig(output_image, bbox_inches='tight', dpi=300, transparent=False, facecolor=fig.get_facecolor())
        plt.close(fig)