import os
from pathlib import Path
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
from cartopy.feature import ShapelyFeature
from cartopy.io.shapereader import Reader
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

# 读取站点CSV文件
site_csv_path = Path(r'F:\个人\allsite1.csv')
sites_df = pd.read_csv(site_csv_path)

# 定义路径
RASTER_PATH = Path(r'D:\数据\AI\Global-AI_ET0_v3_annual\output_cropped.tif')
OUTPUT_DIR = RASTER_PATH.parent / 'output_visualization'
NATIONAL_BOUNDARY_SHAPEFILE = r'D:\数据\边界\中国1：400万基础数据\国界线.shp'
PROVINCIAL_BOUNDARY_SHAPEFILE = r'D:\数据\边界\中国1：400万基础数据\国界与省界线.shp'

os.makedirs(OUTPUT_DIR, exist_ok=True)

def plot_raster_with_china_background(raster_path, output_dir, national_boundary_shapefile, provincial_boundary_shapefile):
    with rasterio.open(raster_path) as src:
        data = src.read(1).astype(np.float32)
        transform = src.transform
        bounds = src.bounds
        crs = src.crs

        # 处理无效值和超出范围的值
        data[data == 0] = np.nan  # 将 0 设置为 NaN
        data[data > 6500] = np.nan  # 将大于 6500 的值设置为 NaN

        # 创建自定义渐变色
        light_orange = (255/255, 69/255, 0/255)   # 深橙色
        deep_orange = (255/255, 165/255, 0/255) # 浅橙色
        custom_cmap = LinearSegmentedColormap.from_list('custom_orange', [deep_orange, light_orange])
        custom_cmap.set_bad(color='white')  # 设置无效值为白色

        # 设置归一化范围
        norm = plt.Normalize(vmin=0, vmax=6500)

        # 创建图形
        plt.rc('font', family='Times New Roman')
        width_in = 170 / 25.4  # 170mm转英寸
        height_in = width_in * (8/12)
        fig, ax = plt.subplots(figsize=(width_in, height_in),
                             subplot_kw={'projection': ccrs.PlateCarree()})

        # 设置地图范围（经度和纬度）
        map_extent = [73, 136, 18, 54]  # 调整为中国大陆的范围 [lon_min, lon_max, lat_min, lat_max]
        ax.set_extent(map_extent, crs=ccrs.PlateCarree())

        # 添加栅格数据
        im = ax.imshow(data, origin='upper', extent=(bounds.left, bounds.right, bounds.bottom, bounds.top),
                       transform=ccrs.PlateCarree(), cmap=custom_cmap, norm=norm)

        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax, orientation='vertical', shrink=0.6, pad=0.03)
        cbar.set_label('AI', fontsize=8)
        cbar.ax.tick_params(labelsize=8)

        # 添加站点
        ax.scatter(sites_df['Longitude'], sites_df['Latitude'],
                 color='black', s=6, marker='^', zorder=10,
                 transform=ccrs.PlateCarree(), label='Sites')

        # 添加站点标签
        for _, row in sites_df.iterrows():
            ax.text(row['Longitude'], row['Latitude']+0.05, row['Site'],
                   fontsize=6, ha='center', va='bottom',
                   transform=ccrs.PlateCarree(), color='black')

        # 添加边界
        for shapefile, style in zip([national_boundary_shapefile, provincial_boundary_shapefile],
                                  [{'edgecolor':'black', 'linewidth':1, 'linestyle':'--'},
                                   {'edgecolor':'gray', 'linewidth':0.5}]):
            if os.path.exists(shapefile):
                ax.add_feature(ShapelyFeature(Reader(shapefile).geometries(),
                                            ccrs.PlateCarree(), **style))

        # 添加网格和比例尺
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
        gl.xlabel_style = {'size': 8}
        gl.ylabel_style = {'size': 8}

        # 仅显示左上两边的刻度
        gl.top_labels = True  # 显示顶部刻度
        gl.right_labels = False  # 隐藏右侧刻度
        gl.left_labels = True  # 显示左侧刻度
        gl.bottom_labels = False  # 隐藏底部刻度

        # 创建图例
        legend_elements = [Line2D([0], [0], marker='^', color='w', markerfacecolor='black',
                                markersize=8, label='Sites', linestyle='None')]
        ax.legend(handles=legend_elements, loc='lower left',
                prop={'size':8}, bbox_to_anchor=(0.15, 0.05))

        # 保存结果
        plt.savefig(output_dir/f'{raster_path.stem}_gradient.png',
                  dpi=600, bbox_inches='tight', facecolor='white')
        plt.close()

# 执行绘图
plot_raster_with_china_background(RASTER_PATH, OUTPUT_DIR, NATIONAL_BOUNDARY_SHAPEFILE, PROVINCIAL_BOUNDARY_SHAPEFILE)