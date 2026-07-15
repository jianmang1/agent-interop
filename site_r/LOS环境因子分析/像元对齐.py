import os
from osgeo import gdal


def resample_tif_to_reference(input_path, reference_path, output_path):
    """
    将输入TIF文件重采样到与参考TIF文件相同的分辨率和投影，同时保留输入文件的地理范围
    """
    # 打开参考文件以获取目标分辨率
    ref_dataset = gdal.Open(reference_path)
    if ref_dataset is None:
        print(f"无法打开参考文件: {reference_path}")
        return False

    # 获取参考文件的分辨率
    ref_gt = ref_dataset.GetGeoTransform()
    ref_pixel_width = ref_gt[1]
    ref_pixel_height = ref_gt[5]

    # 获取参考文件的投影
    ref_projection = ref_dataset.GetProjection()

    # 获取参考文件的地理范围
    ref_min_x = ref_gt[0]
    ref_max_y = ref_gt[3]
    ref_max_x = ref_gt[0] + ref_gt[1] * ref_dataset.RasterXSize
    ref_min_y = ref_gt[3] + ref_gt[5] * ref_dataset.RasterYSize

    # 打开输入文件
    input_dataset = gdal.Open(input_path)
    if input_dataset is None:
        print(f"无法打开输入文件: {input_path}")
        ref_dataset = None
        return False

    # 获取输入文件的地理范围
    input_gt = input_dataset.GetGeoTransform()
    input_min_x = input_gt[0]
    input_max_y = input_gt[3]
    input_max_x = input_gt[0] + input_gt[1] * input_dataset.RasterXSize
    input_min_y = input_gt[3] + input_gt[5] * input_dataset.RasterYSize

    # 确保输出范围是输入文件的范围（保留原始地理范围）
    output_min_x = max(input_min_x, ref_min_x)
    output_max_y = min(input_max_y, ref_max_y)
    output_max_x = min(input_max_x, ref_max_x)
    output_min_y = max(input_min_y, ref_min_y)

    # 如果输入范围与参考范围不重叠，则跳过
    if output_min_x >= output_max_x or output_min_y >= output_max_y:
        print(f"输入文件与参考文件地理范围不重叠，跳过: {input_path}")
        input_dataset = None
        ref_dataset = None
        return False

    # 使用gdal.Warp进行重采样
    warp_options = gdal.WarpOptions(
        format='GTiff',
        xRes=abs(ref_pixel_width),
        yRes=abs(ref_pixel_height),
        dstSRS=ref_projection,
        resampleAlg='bilinear',  # 可根据需要改为 'nearest', 'cubic', 'lanczos' 等
        outputBounds=[output_min_x, output_min_y, output_max_x, output_max_y],
        targetAlignedPixels=True,  # 对齐到像素网格
        multithread=True
    )

    # 执行重采样
    output_dataset = gdal.Warp(output_path, input_dataset, options=warp_options)

    if output_dataset is None:
        print(f"重采样失败: {input_path}")
        input_dataset = None
        ref_dataset = None
        return False

    # 关闭数据集
    input_dataset = None
    ref_dataset = None
    output_dataset = None

    print(f"重采样完成: {input_path} -> {output_path}")
    return True


def batch_resample_tifs(input_folder, reference_path, output_folder):
    """
    批量重采样文件夹中的所有TIF文件
    """
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)

    # 获取所有TIF文件
    tif_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.tif')]

    if not tif_files:
        print(f"在 {input_folder} 中未找到TIF文件")
        return

    print(f"找到 {len(tif_files)} 个TIF文件，开始批量重采样...")

    success_count = 0
    for filename in tif_files:
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, f"resampled_{filename}")

        print(f"正在处理: {filename}")
        if resample_tif_to_reference(input_path, reference_path, output_path):
            success_count += 1

    print(f"批量重采样完成！成功处理 {success_count}/{len(tif_files)} 个文件")


# 设置路径
input_folder = r"I:\SOS"
reference_path = r"I:\TerraClimate\pre_tif\TerraClimate_ppt_198101.tif"
output_folder = r"I:\TerraClimate\pre_tif\resampled"

# 执行批量重采样
batch_resample_tifs(input_folder, reference_path, output_folder)



