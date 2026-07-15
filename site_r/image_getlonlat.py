import os
from PIL import Image
from piexif import GPSIFD, load
import pandas as pd


def get_gps_info(image_path):
    try:
        img = Image.open(image_path)
        exif_dict = load(img.info.get('exif', b''))

        if 'GPS' not in exif_dict:
            return None, None

        lat_ref = exif_dict['GPS'][GPSIFD.GPSLatitudeRef]
        lat = exif_dict['GPS'][GPSIFD.GPSLatitude]
        lon_ref = exif_dict['GPS'][GPSIFD.GPSLongitudeRef]
        lon = exif_dict['GPS'][GPSIFD.GPSLongitude]

        # 转换为十进制度数
        lat_value = (lat[0][0] / lat[0][1]) + \
                    (lat[1][0] / lat[1][1] / 60) + \
                    (lat[2][0] / lat[2][1] / 3600)
        lon_value = (lon[0][0] / lon[0][1]) + \
                    (lon[1][0] / lon[1][1] / 60) + \
                    (lon[2][0] / lon[2][1] / 3600)

        if lat_ref == 'S':
            lat_value = -lat_value
        if lon_ref == 'W':
            lon_value = -lon_value

        return lat_value, lon_value
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None, None


def batch_process(directory):
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return

    files = os.listdir(directory)
    if not files:
        print(f"No files found in directory {directory}.")
        return

    data = []
    for filename in files:
        if filename.lower().endswith(('.jpg', '.jpeg')):
            filepath = os.path.join(directory, filename)
            lat, lon = get_gps_info(filepath)
            if lat and lon:
                data.append([filename, lat, lon])
            else:
                data.append([filename, None, None])

    return data


def save_to_excel(data, output_file):
    df = pd.DataFrame(data, columns=['Filename', 'Latitude', 'Longitude'])
    df.to_excel(output_file, index=False)
    print(f"Data saved to {output_file}")


# 指定图片所在的目录和输出Excel文件路径
directory = 'H:\site'
output_file = 'H:\site\gps_data.xlsx'

data = batch_process(directory)
save_to_excel(data, output_file)