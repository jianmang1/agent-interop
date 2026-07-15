import os
from pathlib import Path
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from cartopy.io.shapereader import Reader
from cartopy.feature import ShapelyFeature
import seaborn as sns
import cartopy.crs as ccrs
import cartopy.feature as cfeature
# 定义路径
RASTER_DIR = Path(r'D:\MOD12Q2\vs')
OUTPUT_DIR = RASTER_DIR / 'output'
CHINA_SHAPEFILE = r'D:\数据\边界\中国1：400万基础数据\国界线.shp'

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 定义要可视化的栅格文件名及其对应的固定颜色条范围
RASTER_FILES = {
    'mask_applied_masked_all_SOS_DOY_2023.tif': {'vmin': 0, 'vmax': 360},
    'mask_applied_masked_all_POS_DOY_2023.tif': {'vmin': 0, 'vmax': 360},
    'mask_applied_masked_all_EOS_DOY_2023.tif': {'vmin': 0, 'vmax': 360},
    'SOS_MCD12Q2_2023_masked.tif': {'vmin': 0, 'vmax': 360},
    'POS_MCD12Q2_2023_masked.tif': {'vmin': 0, 'vmax': 360},
    'EOS_MCD12Q2_2023_masked.tif': {'vmin': 0, 'vmax': 360},
}

import matplotlib as mpl

# 设置全局字体
mpl.rcParams['font.family'] = 'Times New Roman'
mpl.rcParams['font.size'] = 16


def plot_raster_with_histogram(raster_path, output_dir, china_shapefile, vmin=None, vmax=None):
    # 根据需要调整图像大小（宽约170mm，即6.69英寸）
    fig_width_inch = 6.69  # 调整为适合的比例
    fig_height_inch = fig_width_inch * (2 / 3)  # 假设高度是宽度的2/3
    fig = plt.figure(figsize=(fig_width_inch, fig_height_inch), facecolor='white', constrained_layout=True)

    gs = fig.add_gridspec(nrows=1, ncols=1)  # 只需一个子图，因为我们去除了直方图

    with rasterio.open(raster_path) as src:
        data = src.read(1)
        transform = src.transform
        bounds = src.bounds
        crs = src.crs

        # 将无效值设置为NaN以便后续处理
        invalid_values = [0, 1,365, -9999]
        for value in invalid_values:
            data[data == value] = np.nan

        # 如果没有提供vmin和vmax，则从数据中计算
        if vmin is None or vmax is None:
            valid_data = data[np.isfinite(data)]
            vmin, vmax = np.nanmin(valid_data), np.nanmax(valid_data)

        # 定义边界和颜色映射
        colors = plt.cm.viridis(np.linspace(0, 1, 10))
        cmap = plt.get_cmap('viridis')
        cmap.set_bad(color='white')  # 设置无效像元值为白色

        ax_map = fig.add_subplot(gs[0], projection=ccrs.PlateCarree())
        setup_map(ax_map, bounds, china_shapefile)
        im = ax_map.imshow(data, cmap=cmap, norm=plt.Normalize(vmin, vmax),
                           extent=[bounds.left, bounds.right, bounds.bottom, bounds.top],
                           transform=ccrs.PlateCarree(), interpolation='nearest')

        # 添加比例尺
        scale_bar(ax_map, bounds, 1000, 'km', fontsize=24)

        # 移除颜色条相关的代码
        # cbar = fig.colorbar(im, ax=ax_map, orientation='horizontal', pad=0.02, shrink=0.8, extend='both')

        # 移除直方图相关的代码
        # ax_dist = fig.add_subplot(gs[1])
        # plot_histogram(ax_dist, data, vmin, vmax)

        # 保存图像时注意dpi设置，以保证输出质量
        output_image = output_dir / f"{raster_path.stem}.png"
        plt.savefig(output_image, bbox_inches='tight', dpi=600, transparent=False, facecolor=fig.get_facecolor())
        plt.close(fig)


def setup_map(ax, bounds, china_shapefile):
    # 添加中国的国界线
    shape_feature = ShapelyFeature(Reader(china_shapefile).geometries(),
                                   ccrs.PlateCarree(), edgecolor='black', facecolor='none', linewidth=2)
    ax.add_feature(shape_feature)

    # 设置地图范围
    ax.set_extent([bounds.left, bounds.right, bounds.bottom, bounds.top], crs=ccrs.PlateCarree())

# 比例尺函数保持不变
def scale_bar(ax, bounds, length_km, units, fontsize):
    # 将长度转换为经度差，并确保不超出地图范围
    length_deg = min(length_km / 111, bounds.right - bounds.left - 0.05 * (bounds.right - bounds.left))

    # 调整 x 坐标以确保在右下角
    x_start = bounds.right - 0.05 * (bounds.right - bounds.left) - length_deg
    y_start = bounds.bottom + 0.05 * (bounds.top - bounds.bottom)
    x_end = x_start + length_deg

    line = plt.Line2D([x_start, x_end], [y_start, y_start], color='black', lw=2, transform=ax.transData)
    ax.add_line(line)

    text_x = (x_start + x_end) / 2
    ax.text(text_x, y_start, f'{length_km} {units}', fontsize=fontsize, ha='center', va='bottom',
            transform=ax.transData)
# 主循环
for raster_file, params in RASTER_FILES.items():
    raster_path = RASTER_DIR / raster_file
    plot_raster_with_histogram(raster_path, OUTPUT_DIR, CHINA_SHAPEFILE, **params)