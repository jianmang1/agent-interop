import rasterio
import os
import pandas as pd


def count_positive_pixels(file_path):
    """Count the number of pixels with values greater than 0 in a given TIF file."""
    with rasterio.open(file_path) as src:
        image = src.read(1)  # Read the first band
        return (image > 0).sum()


# Paths
base_dir = "D:\MODIS43A4_2024\SOS"
mask_file = "D:/MOD12Q2/resampled_mask.tif"
output_excel = "D:\MOD12Q2\\ratio\pixel_ratio_results2.xlsx"

# Calculate positive pixels for mask file once, since it's used for each year comparison
positive_pixel_count_mask = count_positive_pixels(mask_file)

ratios = []

if positive_pixel_count_mask == 0:
    print("The mask file contains no positive pixels. Cannot compute ratios.")
else:
    # Loop through each year from 2001 to 2023
    for year in range(2001, 2024):  # Include 2023
        file_name = f"mask_applied_masked_all_SOS_DOY_{year}.tif"
        file_path = os.path.join(base_dir, file_name)

        if os.path.exists(file_path):
            positive_pixel_sum_sos = count_positive_pixels(file_path)
            ratio = positive_pixel_sum_sos / positive_pixel_count_mask

            ratios.append({'Year': year, 'Ratio': ratio})
            print(f"Year {year}: Ratio of positive pixel counts = {ratio}")
        else:
            print(f"File {file_name} does not exist.")
            ratios.append({'Year': year, 'Ratio': None})

# Convert list of dictionaries to DataFrame
df = pd.DataFrame(ratios)

# Write DataFrame to Excel file
df.to_excel(output_excel, index=False)

print(f"Results have been written to {output_excel}")