import rasterio
import os
import pandas as pd
from rasterio.enums import Resampling
import numpy as np
from rasterio import warp
import numpy as np


def reproject_mask_to_match_image(mask_path, image_shape, transform):
    """Reproject the mask to match the shape and transform of the image."""
    with rasterio.open(mask_path) as src:
        mask = src.read(1)

        # Define the output profile based on the target image
        out_profile = src.profile.copy()
        out_profile.update({
            'height': image_shape[0],
            'width': image_shape[1],
            'transform': transform,
            'driver': 'GTiff',
            'dtype': src.meta['dtype']
        })

        # Reproject the mask
        reprojected_mask = np.zeros((out_profile['height'], out_profile['width']), dtype=src.meta['dtype'])
        warp.reproject(
            source=mask,
            destination=reprojected_mask,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=out_profile['transform'],
            dst_crs=src.crs,
            resampling=Resampling.nearest
        )

    return reprojected_mask


def count_valid_pixels_in_reprojected_mask(reprojected_mask):
    """Count the number of pixels with value 0 or 1 in the reprojected mask."""
    return ((reprojected_mask == 0) | (reprojected_mask == 1)).sum()


def count_positive_pixels_with_mask(file_path, mask_path):
    """Count the number of pixels with values between 1 and 365 in a given TIF file where the mask has value 1."""
    # Check if both files exist before opening them
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Image file does not exist: {file_path}")
    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"Mask file does not exist: {mask_path}")

    with rasterio.open(file_path) as src_img, rasterio.open(mask_path) as src_mask:
        image = src_img.read(1)  # Read the first band from the image
        transform = src_img.transform

    # Reproject the mask to match the image
    reprojected_mask = reproject_mask_to_match_image(mask_path, image.shape, transform)

    # Count valid pixels (0 or 1) in the reprojected mask
    valid_pixels_count = count_valid_pixels_in_reprojected_mask(reprojected_mask)
    # print(f"Valid pixels (0 or 1) in reprojected mask: {valid_pixels_count}")

    # Apply the mask and count SOS pixels
    masked_image = image * (reprojected_mask == 1)
    positive_pixels = ((masked_image >= 1) & (masked_image <= 365)).sum()

    return positive_pixels, valid_pixels_count


# Paths
base_dir = "D:\\MOD12Q2\\MCD12Q2_SOS"
# 修改mask_files路径，处理1-4和7的mask文件
mask_numbers = [1, 2, 3, 4, 7]
mask_files = []
for i in mask_numbers:
    mask_file = f"D:\\MOD12Q2\\vs\\classai\\plant\\{i}_masked_tibet.tif"
    if os.path.exists(mask_file):
        mask_files.append(mask_file)
        print(f"Found mask file: {mask_file}")
    else:
        print(f"Warning: Mask file does not exist: {mask_file}")

if not mask_files:
    print("No mask files found. Please check the paths.")
    exit()

output_excel_base = "D:\\MOD12Q2\\ratio\\plantclass\\mcd12\\pixel_ratio_results_{}.xlsx"

ratios_all_masks = []

for mask_file in mask_files:
    ratios = []

    # Loop through each year from 2001 to 2023
    for year in range(2001, 2024):  # Include 2023
        file_name = f"masked2_SOS_MCD12Q2_{year}_masked_tibet.tif"
        file_path = os.path.join(base_dir, file_name)

        if os.path.exists(file_path):
            try:
                positive_pixel_sum_sos, mask_ones_count = count_positive_pixels_with_mask(file_path, mask_file)

                if mask_ones_count == 0:
                    ratio = None
                    print(f"The mask file {mask_file}, Year {year}: mask contains no pixels with value 1.")
                else:
                    ratio = positive_pixel_sum_sos / mask_ones_count
                    print(f"Mask: {mask_file}, Year {year}: Ratio of SOS pixels = {ratio:.4f}")

                ratios.append({'Year': year, 'Ratio': ratio})
            except ValueError as e:
                print(f"File {file_name} has dimension mismatch: {e}")
                ratios.append({'Year': year, 'Ratio': None})
            except Exception as e:
                print(f"Error processing {file_name} with {mask_file}: {e}")
                ratios.append({'Year': year, 'Ratio': None})
        else:
            print(f"File {file_name} does not exist.")
            ratios.append({'Year': year, 'Ratio': None})

    # Convert list of dictionaries to DataFrame
    df = pd.DataFrame(ratios)

    # Write DataFrame to Excel file
    mask_num = os.path.basename(mask_file).split('_')[0]  # Extract number from filename
    output_excel = output_excel_base.format(mask_num)
    df.to_excel(output_excel, index=False)
    print(f"Results saved to {output_excel}")
    ratios_all_masks.append(df)

# Combine all results into a single DataFrame
if ratios_all_masks:
    combined_df = pd.concat(ratios_all_masks, keys=[f'Mask {os.path.basename(m).split("_")[0]}' for m in mask_files])
    combined_output_excel = "D:\\MOD12Q2\\ratio\\mcd12\\combined_pixel_ratio_results.xlsx"
    combined_df.to_excel(combined_output_excel, index=True)
    print(f"Combined results saved to {combined_output_excel}")
else:
    print("No data to save.")
