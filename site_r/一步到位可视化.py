import os
import rasterio
from rasterio.mask import mask
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm

# 定义路径
shapefile_path = r'F:\个人\ioa-20241031T012330Z-001\ioa1\merged_result.shp'
raster_dir = r'D:\MODIS43A4_2024\SOS\500m(unmask0)'
output_dir = r'D:\MODIS43A4_2024\SOS\500m(unmask0)\output2'

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)

# 读取Shapefile
shapefile = gpd.read_file(shapefile_path)
shapes = [feature["geometry"] for feature in shapefile.__geo_interface__['features']]

# 定义要处理的栅格文件名
raster_files = ['mean_values.tif', 'rmse_values.tif', 'slope_values.tif', 'p_values.tif']

for raster_file in raster_files:
    # 构建完整的栅格文件路径
    raster_path = os.path.join(raster_dir, raster_file)

    with rasterio.open(raster_path) as src:
        # 裁剪栅格
        out_image, out_transform = mask(src, shapes, crop=True)
        out_meta = src.meta.copy()

        # 更新元数据
        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform})

        # 写入裁剪后的栅格文件
        output_raster = os.path.join(output_dir, f"clipped_{raster_file}")
        with rasterio.open(output_raster, "w", **out_meta) as dest:
            dest.write(out_image)

        # 重新打开裁剪后的栅格文件以读取数据
        with rasterio.open(output_raster) as clipped_src:
            clipped_data = clipped_src.read(1)

            # 处理NaN值（如果有）
            clipped_data = np.nan_to_num(clipped_data, nan=0.0)

            # 创建10个等级的颜色梯度，不包括0
            vmin, vmax = np.min(clipped_data[clipped_data > 0]), np.max(clipped_data)
            if vmin == vmax:
                # 如果所有非零值相同，则设置vmin略小于vmax以避免绘图问题
                vmin = vmax - 1e-6

            # 定义边界和颜色映射
            bounds = np.linspace(vmin, vmax, 11)  # 10个等级
            colors = plt.cm.viridis(np.linspace(0, 1, 10))
            cmap = LinearSegmentedColormap.from_list('custom_cmap', colors)
            norm = BoundaryNorm(bounds, cmap.N)

            # 将像元值为0的部分设置为黑色
            black_color = np.array([[0, 0, 0, 1]])  # RGBA for black
            cmap.set_under(black_color)

            # 可视化裁剪后的栅格
            fig, ax = plt.subplots(1, 1, figsize=(8, 6))
            im = ax.imshow(clipped_data, cmap=cmap, norm=norm)
            cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, extend='min')
            cbar.set_label('Pixel Value')
            ax.set_title(f'{raster_file}')
            plt.axis('off')  # 关闭坐标轴

            # 保存图像
            output_image = os.path.join(output_dir, f"{os.path.splitext(raster_file)[0]}.png")
            plt.savefig(output_image, bbox_inches='tight', dpi=300)
            plt.close(fig)

print("所有栅格文件已成功裁剪并以10个颜色梯度显示，像元值为0的部分为纯黑色。")