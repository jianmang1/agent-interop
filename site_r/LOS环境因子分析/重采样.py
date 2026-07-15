import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
import os
from pathlib import Path


def resample_and_align_modis_to_terraclimate(modis_dir, terraclimate_template, output_dir):
    """
    将MODIS SOS数据重采样并对齐到TerraClimate裁剪后的网格

    参数:
    modis_dir: MODIS数据目录
    terraclimate_template: TerraClimate裁剪模板文件路径
    output_dir: 输出目录
    """

    # 读取TerraClimate裁剪模板文件获取目标分辨率和范围
    with rasterio.open(terraclimate_template) as template_ds:
        dst_crs = template_ds.crs
        dst_transform = template_ds.transform
        dst_width = template_ds.width
        dst_height = template_ds.height
        dst_bounds = template_ds.bounds
        dst_nodata = template_ds.nodata if template_ds.nodata is not None else -9999

    print(f"目标分辨率: {dst_transform[0]:.4f} x {abs(dst_transform[4]):.4f}")
    print(f"目标尺寸: {dst_width} x {dst_height}")
    print(f"目标范围: {dst_bounds}")
    print(f"目标坐标系: {dst_crs}")

    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 处理2001-2024年的MODIS数据
    for year in range(2001, 2025):
        input_file = os.path.join(modis_dir, f"masked2_masked_all_EoS_DOY_{year}.tif")

        if not os.path.exists(input_file):
            print(f"警告: 文件不存在 {input_file}")
            continue

        output_file = os.path.join(output_dir, f"masked2_masked_all_EoS_DOY_{year}_aligned.tif")

        print(f"正在处理 {input_file}")

        with rasterio.open(input_file) as src_ds:
            # 获取源数据信息
            src_crs = src_ds.crs
            src_transform = src_ds.transform
            src_width = src_ds.width
            src_height = src_ds.height
            src_bounds = src_ds.bounds
            src_nodata = src_ds.nodata if src_ds.nodata is not None else -9999

            print(f"  源数据分辨率: {src_transform[0]:.4f} x {abs(src_transform[4]):.4f}")
            print(f"  源数据尺寸: {src_width} x {src_height}")
            print(f"  源数据范围: {src_bounds}")

            # 创建输出数据数组
            dst_data = np.empty((dst_height, dst_width), dtype=src_ds.dtypes[0])
            dst_data[:] = dst_nodata  # 初始化为nodata值

            # 执行重采样和对齐，使用裁剪模板的变换参数
            reproject(
                source=rasterio.band(src_ds, 1),  # 源数据
                destination=dst_data,  # 目标数据
                src_transform=src_transform,
                src_crs=src_crs,
                dst_transform=dst_transform,  # 使用裁剪模板的变换参数
                dst_crs=dst_crs,
                resampling=Resampling.nearest,  # 使用最近邻重采样，适合DOY数据
                src_nodata=src_nodata,
                dst_nodata=dst_nodata
            )

            # 创建输出文件，使用裁剪模板的元数据确保完全对齐
            output_meta = {
                'driver': 'GTiff',
                'height': dst_height,
                'width': dst_width,
                'transform': dst_transform,
                'crs': dst_crs,
                'nodata': dst_nodata,
                'dtype': src_ds.dtypes[0],
                'count': 1
            }

            with rasterio.open(output_file, 'w', **output_meta) as dst_ds:
                dst_ds.write(dst_data, 1)

        print(f"已保存: {output_file}")

    print("所有文件重采样和对齐完成!")


def validate_alignment(file1_path, file2_path):
    """
    验证两个栅格文件是否对齐
    """
    with rasterio.open(file1_path) as ds1, rasterio.open(file2_path) as ds2:
        # 检查坐标系
        crs_match = ds1.crs == ds2.crs
        # 检查变换矩阵
        transform_match = (ds1.transform.almost_equals(ds2.transform) and
                           ds1.width == ds2.width and
                           ds1.height == ds2.height)
        # 检查范围
        bounds_match = (abs(ds1.bounds[0] - ds2.bounds[0]) < 1e-6 and
                        abs(ds1.bounds[1] - ds2.bounds[1]) < 1e-6 and
                        abs(ds1.bounds[2] - ds2.bounds[2]) < 1e-6 and
                        abs(ds1.bounds[3] - ds2.bounds[3]) < 1e-6)

        print(f"坐标系匹配: {crs_match}")
        print(f"变换矩阵匹配: {transform_match}")
        print(f"范围匹配: {bounds_match}")

        return crs_match and transform_match and bounds_match


# 使用示例
if __name__ == "__main__":
    # 设置路径
    modis_directory = r"D:\MODIS43A4_2024\EOS2"
    terraclimate_template = r"I:\TerraClimate\pre_tif_clipped\TerraClimate_ppt_202301.tif"
    output_directory = r"D:\MODIS43A4_2024\EOS2_aligned"

    # 执行重采样和对齐
    resample_and_align_modis_to_terraclimate(modis_directory, terraclimate_template, output_directory)

    # 验证对齐结果（可选）
    print("\n验证对齐结果...")
    sample_output = os.path.join(output_directory, "masked2_masked_all_EoS_DOY_2001_aligned.tif")
    if os.path.exists(sample_output):
        is_aligned = validate_alignment(sample_output, terraclimate_template)
        print(f"对齐验证结果: {'成功' if is_aligned else '失败'}")



