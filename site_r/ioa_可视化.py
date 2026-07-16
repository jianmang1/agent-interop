import os
from pathlib import Path
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D  # 导入 Line2D
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io.shapereader import Reader  # 导入 Reader
from cartopy.feature import ShapelyFeature
import pandas as pd

# 读取站点CSV文件
site_csv_path = Path(r'F:\个人\allsite1.csv')
sites_df = pd.read_csv(site_csv_path)
# 定义路径
RASTER_PATH = Path(r'D:\数据\AI\Global-AI_ET0_v3_annual\output_cropped.tif')
OUTPUT_DIR = RASTER_PATH.parent / 'output_visualization'
NATIONAL_BOUNDARY_SHAPEFILE = r'D:\数据\边界\中国1：400万基础数据\国界线.shp'
PROVINCIAL_BOUNDARY_SHAPEFILE = r'D:\数据\边界\中国1：400万基础数据\国界与省界线.shp'

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

def plot_raster_with_china_background(raster_path, output_dir, national_boundary_shapefile, provincial_boundary_shapefile):
    with rasterio.open(raster_path) as src:
        data = src.read(1).astype(np.float32)  # 将数据转换为浮点类型
        transform = src.transform
        bounds = src.bounds
        crs = src.crs

        # 将无效值设置为NaN以便后续处理
        invalid_values = [0]  # 根据实际情况添加更多无效值
        for value in invalid_values:
            data[data == value] = np.nan

        # 创建一个掩码来应用颜色
        mask_2000 = data < 2000
        mask_6500 = (data >= 2000) & (data < 6500)
        mask_other = ~np.isfinite(data)  # 不符合条件或像元值为0或其他无效值

        # 创建一个与原始数据相同大小的零矩阵来保存颜色信息
        color_data = np.zeros(data.shape + (4,), dtype=np.uint8)  # RGBA

        # 应用颜色
        color_data[mask_2000] = [255, 69, 0, 255]  # 深橙色 (RGB: 255, 69, 0)
        color_data[mask_6500] = [255, 165, 0, 255]  # 浅橙色 (RGB: 255, 165, 0)
        color_data[mask_other] = [255, 255, 255, 255]  # 白色 (RGB: 255, 255, 255)

        # 将图像转换为符合 cartopy 的格式
        image_extent = (bounds.left, bounds.right, bounds.bottom, bounds.top)

        import matplotlib as mpl

        # 设置全局字体为Times New Roman，如果仅针对特定元素应用，则需单独设置
        mpl.rc('font', family='Times New Roman')

        # 创建图形, 设置宽度为170mm，注意matplotlib的尺寸是以英寸为单位240=170mm
        width_in_inches = 120 / 25.4  # 将毫米转换为英寸
        # 假设我们想要保持一个宽高比，比如原来的宽高比是12:8=3:2
        height_in_inches = width_in_inches * (2 / 3)
        fig, ax = plt.subplots(figsize=(width_in_inches, height_in_inches),
                               subplot_kw={'projection': ccrs.PlateCarree()})

        # 添加经纬度标签，并设置字体和大小
        gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                          linewidth=1, color='gray', alpha=0.5, linestyle='--')
        gl.xlabels_top = False  # 不显示顶部的x轴标签
        gl.ylabels_right = False  # 不显示右侧的y轴标签

        # 设置经纬度标签的字体为Times New Roman，大小为8pt
        gl.xlabel_style = {'size': 6, 'family': 'Times New Roman'}  # x轴标签的样式
        gl.ylabel_style = {'size': 6, 'family': 'Times New Roman'}  # y轴标签的样式
        ...
        # 添加站点位置到地图，并设置zorder为较高值以确保位于最上层
        ax.scatter(sites_df['Longitude'], sites_df['Latitude'], color='Yellow', s=2, transform=ccrs.PlateCarree(),
                   label='Sites', marker='^', zorder=10)  # 添加zorder参数

        for _, row in sites_df.iterrows():
            # 计算一个新的y坐标，将文本放置在点的上方一点
            y_offset = 0.05  # 调整这个值以改变向上移动的距离，单位为经纬度
            ax.text(row['Longitude'], row['Latitude'] + y_offset, row['Site'],
                    transform=ccrs.PlateCarree(), fontsize=6, ha='center',
                    color='Yellow', fontdict={'family': 'Times New Roman'},
                    va='bottom',  # 垂直对齐方式设为底部，使得文本位于点的正上方
                    zorder=10)  # 确保文本位于最上层

        # 如果有中国的国界形状文件，可以加载并添加到地图中
        if national_boundary_shapefile and os.path.exists(national_boundary_shapefile):
            national_boundary_feature = ShapelyFeature(
                Reader(national_boundary_shapefile).geometries(),
                ccrs.PlateCarree(), edgecolor='black', facecolor='none', linewidth=2, linestyle='--',
                label='National Boundaries'
            )
            ax.add_feature(national_boundary_feature)

        if provincial_boundary_shapefile and os.path.exists(provincial_boundary_shapefile):
            provincial_boundary_feature = ShapelyFeature(
                Reader(provincial_boundary_shapefile).geometries(),
                ccrs.PlateCarree(), edgecolor='lightgray', facecolor='none', linewidth=0.5, label='Provincial Boundaries'
            )
            ax.add_feature(provincial_boundary_feature)

        # 设置地图范围
        ax.set_extent([bounds.left, bounds.right, bounds.bottom, bounds.top], crs=ccrs.PlateCarree())

        # 显示带有颜色映射的栅格数据
        im = ax.imshow(color_data, origin='upper', extent=image_extent, transform=ccrs.PlateCarree())

        # 添加图例说明
        legend_elements = [
            Patch(facecolor=[255 / 255, 69 / 255, 0 / 255], edgecolor='none', label='Arid'),
            Patch(facecolor=[255 / 255, 165 / 255, 0 / 255], edgecolor='none', label='Semi-arid'),
        ]
        # 更新图例元素，使站点图标与scatter匹配
        legend_elements.append(
            Line2D([0], [0], marker='^', color='w', markerfacecolor='yellow', markersize=10, label='Sites',
                   linestyle='None')
        )

        # 设置图例字体为Times New Roman，大小为8
        font = {'family': 'Times New Roman',
                'size': 8}
        # 将图例放置在左下角，并应用字体设置
        ax.legend(handles=legend_elements, loc='lower left', bbox_to_anchor=(0.2, 0.02), prop=font)
        # 添加比例尺
        def add_scale_bar(ax, length_km, units, fontsize, location='lower right'):
            # 计算长度对应的经度差，并确保不超出地图范围
            length_deg = min(length_km / 111, abs(bounds.right - bounds.left) * 0.1)
            x_start = bounds.left + (bounds.right - bounds.left) * 0.05
            y_start = bounds.bottom + (bounds.top - bounds.bottom) * 0.05
            x_end = x_start + length_deg

            line = plt.Line2D([x_start, x_end], [y_start, y_start], color='black', lw=2, transform=ax.transData)
            ax.add_line(line)

            text_x = (x_start + x_end) / 2
            # 设置比例尺文本的字体、大小和颜色，这里仅使用fontdict中的'size'而不额外指定fontsize
            ax.text(text_x, y_start, f'{length_km} {units}', ha='center', va='bottom',
                    transform=ax.transData, fontdict={'family': 'Times New Roman', 'size': fontsize}, color='black')

        # 调用add_scale_bar函数添加比例尺，注意这里将fontsize设置为8以符合要求
        add_scale_bar(ax, 1000, 'km', 8)

        # 保存图像
        output_image = output_dir / f"{raster_path.stem}.png"
        plt.savefig(output_image, bbox_inches='tight', dpi=600, transparent=False, facecolor='white')
        plt.close(fig)

# 调用函数进行绘图
plot_raster_with_china_background(RASTER_PATH, OUTPUT_DIR, NATIONAL_BOUNDARY_SHAPEFILE, PROVINCIAL_BOUNDARY_SHAPEFILE)