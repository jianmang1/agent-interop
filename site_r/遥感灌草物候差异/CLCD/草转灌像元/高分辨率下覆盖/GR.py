import rasterio
import numpy as np
import os

def process_year(year):
    clcd_path = rf'F:\转变\masked_CLCD\masked_CLCD_v01_{year}.tif'

    mean_config = [
        (rf'D:\MODIS43A4_2024\SOS\500m(unmask0)\masked2_masked_all_SoS_DOY_{year}.tif', 'SOS')
    ]

    # 读取当前年份的 30m CLCD 数据
    if not os.path.exists(clcd_path):
        raise FileNotFoundError(f"缺失当前年数据: {clcd_path}")

    with rasterio.open(clcd_path) as clcd_src:
        clcd_array = clcd_src.read(1)
        clcd_transform = clcd_src.transform
        clcd_crs = clcd_src.crs
        clcd_shape = clcd_array.shape

    for mean_path, prefix in mean_config:
        if not os.path.exists(mean_path):
            raise FileNotFoundError(f"缺失 mean_config 数据: {mean_path}")

        with rasterio.open(mean_path) as mean_src:
            mean_array = mean_src.read(1)
            mean_transform = mean_src.transform
            mean_crs = mean_src.crs
            mean_shape = mean_array.shape

            if clcd_crs != mean_crs:
                raise ValueError(f"CRS 不一致: {clcd_crs} vs {mean_crs}")

            # 创建 SI 数组
            si_array = np.zeros_like(mean_array, dtype=np.float32)

            # 遍历每个像元位置
            for row in range(mean_shape[0]):
                for col in range(mean_shape[1]):
                    # 获取当前像元的地理中心点
                    x, y = mean_transform * (col + 0.5, row + 0.5)
                    # 转换为 30m CLCD 栅格中的行和列
                    clcd_row, clcd_col = clcd_src.index(x, y)

                    # 确定覆盖区域：500m 像元大约覆盖 16.666 个 30m 像元，取中间 17x17 的区域
                    min_row = max(0, clcd_row - 8)
                    max_row = min(clcd_shape[0] - 1, clcd_row + 8)
                    min_col = max(0, clcd_col - 8)
                    max_col = min(clcd_shape[1] - 1, clcd_col + 8)

                    # 提取 30m CLCD 窗口
                    window = clcd_array[min_row:max_row + 1, min_col:max_col + 1]

                    n3 = np.count_nonzero(window == 3)
                    total = window.size
                    si = n3 / total if total > 0 else 0
                    si_array[row, col] = si

            # 保存 SI 数组为新的 GeoTIFF 文件
            output_path = rf'D:\转变\masked_CLCD\masked_CLCD_v01_{year}_{prefix}_SR.tif'
            with rasterio.open(
                    output_path,
                    'w',
                    driver='GTiff',
                    height=mean_shape[0],
                    width=mean_shape[1],
                    count=1,
                    dtype=rasterio.float32,
                    crs=mean_crs,
                    transform=mean_transform
            ) as dst:
                dst.write(si_array, 1)
                print(f"已保存 SI 文件: {output_path}")


if __name__ == "__main__":
    for year in range(2002, 2022):
        print(f"开始处理年份: {year}")
        process_year(year)



