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
import matplotlib.font_manager as fm

# 定义路径
RASTER_DIR = Path(r'D:\MODIS43A4_2024\masked_without_tibet\EOS2')
OUTPUT_DIR = RASTER_DIR / 'output3'
CHINA_SHAPEFILE = r'D:\数据\边界\中国1：400万基础数据\国界线.shp'

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 定义要可视化的栅格文件名及其对应的固定颜色条范围
RASTER_FILES = {
    'mean_values.tif': {'vmin': 230, 'vmax': 300},
    'std_values.tif': {'vmin': 0, 'vmax': 60},
    'slope_values.tif': {'vmin': -2.5, 'vmax': 2.5},
    'p_values.tif': {'vmin': 0, 'vmax': 1}
}

font_path = r'C:\Windows\Fonts\times.ttf'  # Times New Roman字体文件路径，请根据实际情况调整
prop = fm.FontProperties(fname=font_path)
def plot_raster_with_histogram(raster_path, output_dir, china_shapefile, xlabel, vmin=None, vmax=None):
    with rasterio.open(raster_path) as src:
        data = src.read(1)
        transform = src.transform
        bounds = src.bounds
        crs = src.crs

        # 将无效值设置为NaN以便后续处理
        invalid_values = [0, 1, -9999]
        for value in invalid_values:
            data[data == value] = np.nan

        # 如果没有提供vmin和vmax，则从数据中计算
        if vmin is None or vmax is None:
            valid_data = data[np.isfinite(data)]
            vmin, vmax = np.nanmin(valid_data), np.nanmax(valid_data)

        # 定义边界和颜色映射
        cmap = plt.get_cmap('viridis')
        cmap.set_bad(color='white')  # 设置无效像元值为白色

        fig = plt.figure(figsize=(80/25.4, (80/25.4)*1.2), facecolor='white', constrained_layout=True)  # 根据85mm宽调整尺寸85/25.4
        gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[2, 1], hspace=0)

        ax_map = fig.add_subplot(gs[0], projection=ccrs.PlateCarree())
        setup_map(ax_map, bounds, china_shapefile)
        im = ax_map.imshow(data, cmap=cmap, norm=plt.Normalize(vmin, vmax),
                           extent=[bounds.left, bounds.right, bounds.bottom, bounds.top],
                           transform=ccrs.PlateCarree(), interpolation='nearest')

        scale_bar(ax_map, bounds, 1000, 'km')

        # 在 plot_raster_with_histogram 函数中调整颜色条长度
        cbar = fig.colorbar(im, ax=ax_map, orientation='horizontal', pad=0.02, shrink=1,extend='both')  # 调整shrink值以拉伸颜色条
        cbar.ax.set_xticks(np.linspace(vmin, vmax, 11))  # 设置期望的刻度数量
        for tick in cbar.ax.get_xticklabels():
            tick.set_fontproperties(prop)
            tick.set_fontsize(8)  # 设置字体大小为8pt

        ax_dist = fig.add_subplot(gs[1])
        plot_histogram(ax_dist, data, vmin, vmax, xlabel=xlabel)  # 确保传递xlabel参数

        # 保存图像
        output_image = OUTPUT_DIR / f"{raster_path.stem}.png"
        plt.savefig(output_image, bbox_inches='tight', dpi=600, transparent=False, facecolor=fig.get_facecolor())
        plt.close(fig)


def setup_map(ax, bounds, china_shapefile):
    # 添加地理特征
    shape_feature = ShapelyFeature(Reader(china_shapefile).geometries(),
                                   ccrs.PlateCarree(), edgecolor='black', facecolor='none', linewidth=2)
    ax.add_feature(shape_feature)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.STATES, linestyle=':')
    ax.set_extent([bounds.left, bounds.right, bounds.bottom, bounds.top], crs=ccrs.PlateCarree())

    # 手动添加经纬度标签，经度为80到130，跨度10，纬度为25到50，跨度5
    xticks = np.arange(80, 131, 10)  # 经度从80到130，每10度一个标签
    yticks = np.arange(25, 51, 5)    # 纬度从25到50，每5度一个标签

    for lon in xticks:
        ax.text(lon, bounds.bottom - 0.5, f'{lon}°E', transform=ccrs.PlateCarree(),
                horizontalalignment='center', verticalalignment='top',
                fontproperties=prop, fontsize=8, color='black')
    for lat in yticks:
        ax.text(bounds.left - 0.3, lat, f'{lat}°N', transform=ccrs.PlateCarree(),
                horizontalalignment='right', verticalalignment='center',
                fontproperties=prop, fontsize=8, color='black')

    # 可选：如果需要网格线，可以在此处添加
    ax.gridlines(draw_labels=False, linewidth=1, color='gray', alpha=0.5, linestyle='--')


def plot_histogram(ax, data, vmin, vmax, xlabel):
    valid_data = data[np.isfinite(data)]
    bins = np.linspace(vmin, vmax, 11)

    sns.histplot(valid_data, bins=bins, kde=False, stat='count', ax=ax, color='skyblue')

    counts, bin_edges = np.histogram(valid_data, bins=bins)
    cumulative_counts = np.cumsum(counts) / np.sum(counts)

    ax2 = ax.twinx()
    ax2.plot(bin_edges[1:], cumulative_counts, color="red", lw=2, label='Cumulative Frequency')

    ax.set_ylim(0, 1e7)
    ax.set_yticks(np.arange(0, 1.1e7, 0.2e7))
    ax.set_xlim(vmin, vmax)

    # 设置轴标签和刻度字体为Times New Roman
    ax.set_xlabel(xlabel, fontproperties=prop, fontsize=8)
    ax.set_ylabel("Frequency/pixel number", fontproperties=prop, fontsize=8)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(prop)
        label.set_fontsize(8)

    ax2.set_ylim(0, 1)
    ax2.set_yticks(np.arange(0, 1.2, 0.2))
    ax2.set_ylabel('Cumulative Frequency', fontsize=8, color='red', fontproperties=prop)
    for label in ax2.get_yticklabels():
        label.set_fontproperties(prop)
        label.set_fontsize(8)
        label.set_color('red')  # 确保右侧y轴标签颜色与轴颜色一致

    ax.tick_params(axis='both', which='major', labelsize=8)
    ax2.tick_params(axis='y', colors='red', labelsize=8)


def scale_bar(ax, bounds, length_km, units):
    # 将长度转换为经度差，并确保不超出地图范围
    length_deg = min(length_km / 111, bounds.right - bounds.left - 0.05 * (bounds.right - bounds.left))

    # 调整 x 坐标以确保在右下角
    x_start = bounds.right - 0.05 * (bounds.right - bounds.left) - length_deg
    y_start = bounds.bottom + 0.05 * (bounds.top - bounds.bottom)
    x_end = x_start + length_deg

    line = plt.Line2D([x_start, x_end], [y_start, y_start], color='black', lw=2, transform=ax.transData)
    ax.add_line(line)

    text_x = (x_start + x_end) / 2
    # 使用 fontproperties 来设置字体为Times New Roman
    ax.text(text_x, y_start, f'{length_km} {units}', fontsize=8, ha='center', va='bottom',
            fontproperties=prop,  # 应用字体属性
            transform=ax.transData)

for raster_file, params in RASTER_FILES.items():
    raster_path = RASTER_DIR / raster_file
    xlabel = {'mean_values.tif': 'Mean EOS (DOY)',
              'std_values.tif': 'Std Values',
              'slope_values.tif': 'EOS trend (Days/year)',
              'p_values.tif': 'P Values'}[raster_file]
    plot_raster_with_histogram(raster_path, OUTPUT_DIR, CHINA_SHAPEFILE, xlabel=xlabel, **params)