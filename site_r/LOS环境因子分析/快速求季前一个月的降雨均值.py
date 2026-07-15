import os
import glob
import numpy as np
import rasterio

def calculate_valid_mean_tif(input_dir, output_path):
    """
    计算指定目录下所有 *.tif 文件的像元有效值均值。
    - 0 和 NaN 视为无效值，不参与平均。
    - 输出使用 float32 类型，无效像元为 NaN。
    """
    # 获取文件列表：1999_ppt.tif 到 2024_ppt.tif
    tif_files = []
    for year in range(1999, 2025):  # 包含 2024
        path = os.path.join(input_dir, f"masked2_masked_all_EoS_DOY_{year}_aligned.tif")
        if os.path.exists(path):
            tif_files.append(path)
        else:
            print(f"警告: {path} 不存在，跳过。")

    if not tif_files:
        raise FileNotFoundError("未找到任何有效的 TIFF 文件。")

    print(f"共找到 {len(tif_files)} 个有效文件。")

    # 读取第一个文件获取元数据
    with rasterio.open(tif_files[0]) as src:
        meta = src.meta.copy()
        height, width = src.shape
        count = src.count  # 波段数，通常为1

    # 初始化累加器和计数器（使用 float64 避免精度损失）
    sum_data = np.zeros((count, height, width), dtype=np.float64)
    valid_counts = np.zeros((count, height, width), dtype=np.int32)

    for i, fp in enumerate(tif_files):
        print(f"处理 ({i+1}/{len(tif_files)}): {os.path.basename(fp)}")
        with rasterio.open(fp) as src:
            data = src.read().astype(np.float64)

            # 获取 nodata 值（如有）
            nodata = src.nodata

            # 构建有效值掩膜：非 NaN、非 inf、非 0、非 nodata
            valid_mask = ~np.isnan(data) & ~np.isinf(data) & (data != 0)
            if nodata is not None:
                valid_mask &= (data != nodata)

            # 累加有效值
            sum_data += np.where(valid_mask, data, 0.0)
            valid_counts += valid_mask.astype(np.int32)

    # 计算均值：仅当 valid_counts > 0 时计算，否则为 NaN
    mean_data = np.divide(
        sum_data,
        valid_counts,
        out=np.full_like(sum_data, np.nan),
        where=(valid_counts > 0)
    )

    # 更新元数据：输出为 float32，nodata 设为 NaN（GeoTIFF 不直接存 NaN，但 float 可表示）
    meta.update({
        'dtype': 'float32',
        'nodata': None,  # 不显式设置 nodata，用 NaN 表示无效
        'compress': 'lzw'  # 可选：压缩减小文件体积
    })

    # 写入结果
    with rasterio.open(output_path, 'w', **meta) as dst:
        dst.write(mean_data.astype(np.float32))

    print(f"✅ 均值栅格已保存至: {output_path}")

# ===== 主程序 =====
if __name__ == "__main__":
    input_dir = r"D:\MODIS43A4_2024\EOS2_aligned"
    output_file = os.path.join(input_dir, "mean.tif")

    calculate_valid_mean_tif(input_dir, output_file)


