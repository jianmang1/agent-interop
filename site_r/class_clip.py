import rasterio
import numpy as np
# 设置输入输出路径
mask_path = r'D:\数据\AI\Global-AI_ET0_v3_annual\mask_less_than_6500.tif'
input_landuse_path = r'C:\Users\Administrator\Documents\WeChat Files\wxid_6xia227bhla912\FileStorage\File\2024-10\2020年中科院土地利用数据30m\2020年中科院土地利用数据30m\land2020.tif'
def apply_mask_to_raster(mask_path, input_landuse_path, output_path, chunk_size=256):
    # 打开掩膜文件
    with rasterio.open(mask_path) as src_mask:
        mask_meta = src_mask.meta.copy()
        nodata_value = src_mask.nodata or -9999  # 获取掩膜的nodata值，如果不存在则设为-9999

        # 打开土地利用栅格文件
        with rasterio.open(input_landuse_path) as src_landuse:
            if src_mask.shape != src_landuse.shape or src_mask.crs != src_landuse.crs:
                raise ValueError("掩膜和土地利用栅格的CRS或尺寸不匹配")

            # 更新元数据以反映新的nodata值（如果需要）
            landuse_meta = src_landuse.meta.copy()
            landuse_meta.update(nodata=nodata_value)

            # 创建输出文件
            with rasterio.open(output_path, "w", **landuse_meta) as dst:
                for ji, window in src_landuse.block_windows():
                    # 读取当前窗口的数据
                    mask_chunk = src_mask.read(1, window=window)
                    landuse_chunk = src_landuse.read(1, window=window)

                    # 创建一个布尔掩膜，其中True表示要保留的像元
                    valid_mask = mask_chunk > 0  # 或者根据你的具体需求设置阈值

                    # 使用布尔掩膜更新土地利用数组
                    masked_landuse_chunk = np.where(valid_mask, landuse_chunk, nodata_value)

                    # 写入输出文件
                    dst.write(masked_landuse_chunk, 1, window=window)

# 定义输出路径
output_landuse_path = r'D:\中科院class\masked_landuse_with_values.tif'

# 调用函数
apply_mask_to_raster(mask_path, input_landuse_path, output_landuse_path)