import os
import rasterio
from rasterio.enums import Resampling
import numpy as np

# 定义文件路径
mask_path = r'D:\MODIS43A4_2024\output_resampled.tif'
output_dir = r'D:\MOD12Q2\MCD12Q2_SOS'

# 生成2001年至2023年的文件列表
start_year = 2001
end_year = 2023
files_to_mask = [f'SOS_MCD12Q2_{year}.tif' for year in range(start_year, end_year + 1)]


def apply_mask(mask_path, input_path, output_path):
    # 打开目标文件以获取其元数据
    with rasterio.open(input_path) as target_src:
        target_transform = target_src.transform
        target_width = target_src.width
        target_height = target_src.height
        target_crs = target_src.crs
        nodata_value = target_src.nodata if target_src.nodata is not None else -9999

        # 读取并重采样掩膜文件
        with rasterio.open(mask_path) as mask_src:
            mask_data_resampled = mask_src.read(1, out_shape=(target_height, target_width),
                                                resampling=Resampling.nearest)
            # 更新掩膜：只保留值为1的像元
            mask = mask_data_resampled == 1

        # 读取原始数据
        data = target_src.read(1)

        # 应用掩膜
        masked_data = np.where(mask, data, nodata_value)

        # 写入新的TIFF文件
        profile = target_src.profile
        profile.update(dtype=rasterio.float32, nodata=nodata_value)

        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(masked_data.astype(rasterio.float32), 1)


def main():
    for file in files_to_mask:
        input_path = os.path.join(output_dir, file)
        output_path = os.path.join(output_dir, f'masked2_{file}')

        print(f"Processing {file}...")
        apply_mask(mask_path, input_path, output_path)
        print(f"Masked {file} saved to {output_path}")


if __name__ == "__main__":
    main()