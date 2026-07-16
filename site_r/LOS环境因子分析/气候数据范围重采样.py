import os
import glob
from pathlib import Path
import rasterio
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
import rioxarray as rxr
from tqdm import tqdm

# 参考文件路径（用于获取裁剪范围和 CRS）
ref_path = r"I:\SOS\masked2_masked_all_SoS_DOY_2003_resampled.tif"

# 输入输出配置：每个变量的输入目录和输出目录
datasets = [
    (r"I:\TerraClimate\pre_tif", r"I:\TerraClimate\pre_tif_clipped"),
    (r"I:\TerraClimate\rad_tif", r"I:\TerraClimate\rad_tif_clipped"),
    (r"I:\TerraClimate\sm_tif", r"I:\TerraClimate\sm_tif_clipped"),
    (r"I:\TerraClimate\tmax_tif", r"I:\TerraClimate\tmax_tif_clipped"),
    (r"I:\TerraClimate\tmin_tif", r"I:\TerraClimate\tmin_tif_clipped"),
    (r"I:\TerraClimate\vpd_tif", r"I:\TerraClimate\vpd_tif_clipped"),
]

# 创建输出目录
for _, out_dir in datasets:
    Path(out_dir).mkdir(parents=True, exist_ok=True)

# 读取参考栅格的范围和 CRS
with rasterio.open(ref_path) as ref_src:
    ref_bounds = ref_src.bounds  # (left, bottom, right, top)
    ref_crs = ref_src.crs

print(f"裁剪目标范围: {ref_bounds}")
print(f"目标 CRS: {ref_crs}")

# 遍历每个数据集目录
for in_dir, out_dir in datasets:
    print(f"\n处理目录: {in_dir}")
    tif_files = glob.glob(os.path.join(in_dir, "*.tif"))
    for tif in tqdm(tif_files, desc=f"裁剪 {os.path.basename(in_dir)}"):
        try:
            # 使用 rioxarray 自动处理重投影和裁剪
            src = rxr.open_rasterio(tif)

            # 打开参考文件作为匹配模板
            ref = rxr.open_rasterio(ref_path)

            # 重投影并裁剪到参考范围（自动处理 CRS 不一致）
            clipped = src.rio.reproject_match(ref)

            # 保存结果
            out_path = os.path.join(out_dir, os.path.basename(tif))
            clipped.rio.to_raster(out_path, compress='LZW')

            src.close()
            ref.close()
        except Exception as e:
            print(f"处理 {tif} 时出错: {e}")

print("\n✅ 所有文件裁剪完成！")