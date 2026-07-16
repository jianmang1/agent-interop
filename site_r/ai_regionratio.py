import rasterio
import os
import pandas as pd
import numpy as np


def count_valid_pixels(file_path):
    """统计给定TIFF文件中像元值为0或1的有效像素总数。"""
    with rasterio.open(file_path) as src:
        mask = src.read(1)
        return ((mask == 0) | (mask == 1)).sum()


def count_zero_pixels(file_path):
    """统计给定TIFF文件中像元值为0的像素数量。"""
    with rasterio.open(file_path) as src:
        mask = src.read(1)
        return (mask == 1).sum()


# 输入和输出路径
mask_files = ["D:\\MOD12Q2\\vs\\classai\\{}.tif".format(i) for i in range(1, 5)]
output_excel = "D:\\MOD12Q2\\ratio\\zero_pixel_ratios.xlsx"

results = []

for mask_file in mask_files:
    try:
        valid_pixels = count_valid_pixels(mask_file)
        zero_pixels = count_zero_pixels(mask_file)

        if valid_pixels == 0:
            ratio = None
            print(f"警告: {mask_file} 的有效像素数为 0，无法计算比例。")
        else:
            ratio = zero_pixels / valid_pixels
            print(f"Mask: {mask_file}, 像元值为0的比例 = {ratio:.4f}")

        results.append({
            'Mask_File': os.path.basename(mask_file),
            'Zero_Pixel_Count': zero_pixels,
            'Valid_Pixel_Count': valid_pixels,
            'Ratio_Zero': ratio
        })

    except Exception as e:
        print(f"处理文件 {mask_file} 时出错: {e}")
        results.append({
            'Mask_File': os.path.basename(mask_file),
            'Zero_Pixel_Count': None,
            'Valid_Pixel_Count': None,
            'Ratio_Zero': None
        })

# 将结果转换为DataFrame并保存到Excel
df = pd.DataFrame(results)
df.to_excel(output_excel, index=False)
print(f"结果已保存至 {output_excel}")