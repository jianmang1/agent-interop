import os
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import seaborn as sns  # 用于绘制核密度图

# 定义路径
raster_dir = r'D:\MODIS43A4_2024\GOSTOLOS'
output_dir = r'D:\MODIS43A4_2024\GOSTOLOS\output3'

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
        invalid_values = [0, 1,-9999]
        for value in invalid_values:
            data[data == value] = np.nan

        # 对于特定文件，设定固定的颜色条范围
        if raster_file == 'mean_values.tif':
            vmin, vmax = 0.2,0.8
        elif raster_file == 'rmse_values.tif':
            vmin, vmax = 0, 1
        elif raster_file == 'slope_values.tif':
            vmin, vmax = -0.02, 0.02
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
        colors = plt.cm.viridis(np.linspace(0, 1, len(bounds_cmap) - 1))
        cmap = LinearSegmentedColormap.from_list('custom_cmap', colors)
        norm = BoundaryNorm(bounds_cmap, cmap.N)

        # 将无效像元值（NaN）设置为透明
        transparent_color = np.array([[0, 0, 0, 0]])  # RGBA for fully transparent
        cmap.set_bad(transparent_color)  # 使用set_bad()来设置无效值的颜色为透明

        # 创建一个包含两个行的图形对象，其中 ax_map 使用 Cartopy 的投影
        fig = plt.figure(figsize=(12, 8), facecolor='white', constrained_layout=True)  # 调整 figsize 以适应新的布局

        # 使用 GridSpec 控制子图布局
        gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[2, 1], hspace=0.1)  # 设置高度比为 2:1

        # 地理空间可视化子图 (GeoAxes)
        ax_map = fig.add_subplot(gs[0], projection=ccrs.PlateCarree())
        ax_map.add_feature(cfeature.BORDERS, linestyle=':')
        ax_map.add_feature(cfeature.COASTLINE)
        ax_map.add_feature(cfeature.STATES, linestyle=':')
        ax_map.set_extent([bounds.left, bounds.right, bounds.bottom, bounds.top], crs=ccrs.PlateCarree())

        # 绘制栅格数据
        im = ax_map.imshow(data, cmap=cmap, norm=norm, extent=[bounds.left, bounds.right, bounds.bottom, bounds.top],
                           transform=ccrs.PlateCarree(), interpolation='none')  # 禁用插值

        # 调整颜色条的位置和长度
        cbar = fig.colorbar(im, ax=ax_map, orientation='horizontal', pad=0.02, shrink=0.8, extend='both')  # 调整颜色条的位置和大小
        cbar.set_label('Pixel Value')

        # 概率分布图子图 (普通 Axes)
        ax_dist = fig.add_subplot(gs[1])
        valid_data = data[np.isfinite(data)]  # 排除NaN和Inf

        # 设置直方图的分组数量为10
        bins = 10000
        kde_clip = (vmin, vmax) if raster_file in ['mean_values.tif', 'rmse_values.tif', 'slope_values.tif'] else None

        sns.histplot(valid_data, bins=bins, kde=True, stat='density', ax=ax_dist, color='skyblue',
                     kde_kws={"clip": kde_clip})

        if raster_file in ['mean_values.tif', 'rmse_values.tif', 'slope_values.tif']:
            ax_dist.set_xlim(vmin, vmax)


        # 确保两个子图的宽度一致
        # 获取当前的 bbox 并调整
        for ax in [ax_map, ax_dist]:
            ax.set_position([0.1, ax.get_position().y0, 0.8, ax.get_position().height])

        # 保存图像
        output_image = os.path.join(output_dir, f"{os.path.splitext(raster_file)[0]}.png")
        plt.savefig(output_image, bbox_inches='tight', dpi=300, transparent=False, facecolor=fig.get_facecolor())
        plt.close(fig)