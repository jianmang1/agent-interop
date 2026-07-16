import rasterio
from rasterio.enums import Resampling
from rasterio.windows import Window
import numpy as np

# 打开参考图像
with rasterio.open(r"D:\MODIS43A4_2024\SOS\all_SoS_DOY_2001.tif") as src_ref:
    ref_transform = src_ref.transform
    ref_crs = src_ref.crs
    ref_width = src_ref.width
    ref_height = src_ref.height

# 打开需要重采样的图像
with rasterio.open(r"F:\个人\CLASS\新建文件夹\中科院.tif") as src_resample:
    resample_profile = src_resample.profile.copy()

    # 设置输出文件的参数
    resample_profile.update(
        driver='GTiff',
        height=ref_height,
        width=ref_width,
        transform=ref_transform,
        crs=ref_crs
    )

    # 创建输出文件
    with rasterio.open(r"D:\中科院class\output_masked_resampled_mode.tif", 'w', **resample_profile) as dst:
        # 遍历所有块
        for ji, window in src_resample.block_windows():
            # 读取窗口内的数据
            data = src_resample.read(window=window)

            # 计算目标窗口
            dst_window = Window(
                int(ji[1] * window.width / src_resample.width * ref_width),
                int(ji[0] * window.height / src_resample.height * ref_height),
                int(window.width * ref_width / src_resample.width),
                int(window.height * ref_height / src_resample.height)
            )

            # 确保目标窗口在输出图像范围内
            if dst_window.col_off + dst_window.width > ref_width or dst_window.row_off + dst_window.height > ref_height:
                continue

            # 重采样并写入目标文件
            try:
                rasterio.warp.reproject(
                    source=data,
                    destination=rasterio.band(dst, 1, window=dst_window),
                    src_transform=src_resample.window_transform(window),
                    src_crs=src_resample.crs,
                    dst_transform=ref_transform,
                    dst_crs=ref_crs,
                    resampling=Resampling.mode
                )
            except Exception as e:
                print(f"Error processing window {ji}: {e}")

print("重采样完成")