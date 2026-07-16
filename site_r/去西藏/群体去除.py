import os
import rasterio
import geopandas as gpd
import numpy as np


def mask_out_region(input_tif, output_tif, geojson_path):
    """
    将 GeoJSON 范围内的像元设为无效值（NaN），保留范围外的数据。

    参数:
        input_tif (str): 输入栅格文件路径
        output_tif (str): 输出栅格文件路径
        geojson_path (str): 用于掩膜的 GeoJSON 文件路径
    """
    # 读取矢量边界
    gdf = gpd.read_file(geojson_path)
    # 确保坐标系一致
    with rasterio.open(input_tif) as src:
        crs_raster = src.crs
    if gdf.crs != crs_raster:
        gdf = gdf.to_crs(crs_raster)

    # 读取栅格数据
    with rasterio.open(input_tif) as src:
        data = src.read()  # shape: (bands, height, width)
        transform = src.transform
        profile = src.profile.copy()

    # 创建布尔掩膜：True 表示在 GeoJSON 内部，False 表示外部
    from rasterio.features import rasterize
    shapes = [(geom, 1) for geom in gdf.geometry]
    mask_raster = rasterize(
        shapes,
        out_shape=data.shape[1:],  # (height, width)
        transform=transform,
        fill=0,
        dtype=np.uint8
    )  # 1 表示在区域内，0 表示在区域外

    # 将区域内的像元设为 NaN
    masked_data = data.astype(np.float32)
    masked_data[:, mask_raster == 1] = np.nan

    # 更新输出配置
    profile.update(dtype=rasterio.float32, nodata=-9999)

    # 写出结果
    with rasterio.open(output_tif, 'w', **profile) as dst:
        dst.write(masked_data)


def main():
    base_dir = r"E:\Desktop\mai"
    folders = ["LOS"]
    files = ["mean_values.tif", "p_values.tif", "rmse_values.tif", "slope_values.tif", "std_values.tif"]
    geojson = os.path.join(base_dir, r"西藏\西藏自治区_省.geojson")
    out_base = os.path.join(base_dir, "masked_without_tibet")

    # 创建输出目录
    for folder in folders:
        os.makedirs(os.path.join(out_base, folder), exist_ok=True)

    # 批量处理
    for folder in folders:
        print(f"正在处理 {folder} ...")
        for file in files:
            input_path = os.path.join(base_dir, folder, file)
            if not os.path.exists(input_path):
                print(f"  跳过（文件不存在）: {input_path}")
                continue
            output_path = os.path.join(out_base, folder, file)
            try:
                mask_out_region(input_path, output_path, geojson)
                print(f"  已完成: {file}")
            except Exception as e:
                print(f"  处理失败 {file}: {e}")


if __name__ == "__main__":
    main()