import os
import glob
from pathlib import Path
import rasterio
from rasterio.enums import Resampling
import rioxarray as rxr
from tqdm import tqdm

# 参考文件路径（用于获取目标尺寸和 CRS）
ref_path = r"I:\SOS\masked2_masked_all_SoS_DOY_2003_resampled.tif"

# 裁剪后的数据集目录
clipped_datasets = [
    r"I:\TerraClimate\pre_tif_clipped",
    r"I:\TerraClimate\rad_tif_clipped",
    r"I:\TerraClimate\sm_tif_clipped",
    r"I:\TerraClimate\tmax_tif_clipped",
    r"I:\TerraClimate\tmin_tif_clipped",
    r"I:\TerraClimate\vpd_tif_clipped",
]

# 读取参考栅格的尺寸、变换和 CRS
with rasterio.open(ref_path) as ref_src:
    ref_height = ref_src.height
    ref_width = ref_src.width
    ref_transform = ref_src.transform
    ref_crs = ref_src.crs

print(f"目标尺寸: {ref_width} x {ref_height}")
print(f"目标 CRS: {ref_crs}")

# 遍历每个裁剪后的数据集目录
for clipped_dir in clipped_datasets:
    print(f"\n调整尺寸目录: {clipped_dir}")

    # 获取该目录下所有tif文件
    tif_files = glob.glob(os.path.join(clipped_dir, "*.tif"))

    for tif in tqdm(tif_files, desc=f"调整尺寸 {os.path.basename(clipped_dir)}"):
        try:
            # 使用 rioxarray 读取已裁剪的影像
            src = rxr.open_rasterio(tif, chunks=True)  # 使用分块处理大文件

            # 获取当前影像的尺寸
            current_height, current_width = src.shape[1], src.shape[2]

            # 如果当前尺寸与目标尺寸不一致，则进行重采样
            if (current_height, current_width) != (ref_height, ref_width):
                # 使用 rasterio 的 reproject 方法调整尺寸
                # 创建目标变换矩阵
                src_crs = src.rio.crs

                # 创建输出数组
                adjusted = src.rio.reproject(
                    dst_crs=ref_crs,
                    shape=(ref_height, ref_width),
                    transform=ref_transform,
                    resampling=Resampling.nearest  # 可根据数据类型选择合适的重采样方法
                )

                # 保存调整后的影像
                out_path = tif  # 覆盖原文件，也可以保存到新路径
                adjusted.rio.to_raster(out_path, compress='LZW')

                print(f"  调整尺寸: {current_width}x{current_height} -> {ref_width}x{ref_height}")
            else:
                print(f"  尺寸已匹配: {current_width}x{current_height}")

            src.close()

        except Exception as e:
            print(f"处理 {tif} 时出错: {e}")

print("\n✅ 所有文件尺寸调整完成！")



