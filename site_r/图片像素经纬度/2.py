import numpy as np
import pandas as pd
from pyproj import Transformer
import rasterio
from rasterio.transform import from_origin

# 1. 定义相机参数（假设所有照片使用相同参数）
camera_params = {
    'focal_length': 5.74,  # 单位：mm
    'sensor_size': (8.76, 8.76),  # 传感器尺寸（宽, 高），单位：mm
    'image_resolution': (1600, 1300)  # 图像分辨率（宽, 高），单位：像素
}


# 2. 定义旋转矩阵函数（与原代码一致）
def rotation_matrix(pitch, roll, yaw):
    R_x = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll), np.cos(roll)]
    ])

    R_y = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ])

    R_z = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw), np.cos(yaw), 0],
        [0, 0, 1]
    ])

    return np.dot(R_z, np.dot(R_y, R_x))


# 3. 定义将笛卡尔坐标转换为经纬度的函数（与原代码一致）
def world_to_latlon_batch(dX, dY, drone_lat, drone_lon):
    a = 6378137.0  # WGS84长半轴
    f = 1 / 298.257223563  # 扁率
    b = a * (1 - f)  # 短半轴

    lat_rad = np.radians(drone_lat)

    N = a / np.sqrt(1 - (2 * f - f ** 2) * np.sin(lat_rad) ** 2)

    m_per_deg_lat = (np.pi / 180) * (a * (1 - f)) / (1 - (2 * f - f ** 2) * np.sin(lat_rad) ** 2) ** 1.5
    m_per_deg_lon = (np.pi / 180) * (N * np.cos(lat_rad))

    delta_lat = dY / m_per_deg_lat
    delta_lon = dX / m_per_deg_lon

    object_lat = drone_lat + delta_lat
    object_lon = drone_lon + delta_lon

    return object_lat, object_lon


# 4. 定义像素坐标转经纬度的主函数（与原代码一致）
def pixel_to_latlon_matrix(image_resolution, camera_params, drone_params):
    x_coords, y_coords = np.meshgrid(np.arange(image_resolution[0]), np.arange(image_resolution[1]))

    x_pixel = (x_coords - image_resolution[0] / 2) * camera_params['sensor_size'][0] / image_resolution[0]
    y_pixel = (y_coords - image_resolution[1] / 2) * camera_params['sensor_size'][1] / image_resolution[1]

    Z_c = drone_params['altitude']  # 使用无人机的飞行高度
    X_c = x_pixel * Z_c * 1000 / camera_params['focal_length']
    Y_c = y_pixel * Z_c * 1000 / camera_params['focal_length']

    pitch, roll, yaw = np.radians(drone_params['angles'])
    R = rotation_matrix(pitch, roll, yaw)
    world_coords = np.dot(R, np.array([X_c.flatten(), Y_c.flatten(), Z_c * np.ones_like(X_c.flatten())]))

    dX = world_coords[0, :].reshape(image_resolution[1], image_resolution[0])
    dY = world_coords[1, :].reshape(image_resolution[1], image_resolution[0])

    lat, lon = world_to_latlon_batch(dX, dY, drone_params['latitude'], drone_params['longitude'])

    latlon_matrix = np.zeros((image_resolution[1], image_resolution[0], 2))
    latlon_matrix[:, :, 0] = lat
    latlon_matrix[:, :, 1] = lon

    return latlon_matrix


# 5. 读取Excel数据并处理每张照片
def process_photos_from_excel(excel_file):
    # 自动检测文件编码
    import chardet
    with open(excel_file, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']

    # 读取CSV文件
    df = pd.read_csv(excel_file, encoding=encoding)

    for index, row in df.iterrows():
        photo_name = row['照片名称']
        drone_lat = row['纬度']
        drone_lon = row['经度']
        altitude = row['高度']
        yaw = row['Yaw']
        pitch = row['Pitch']
        roll = row['Roll']

        # 构建 drone_params
        drone_params = {
            'latitude': drone_lat,
            'longitude': drone_lon,
            'altitude': altitude,
            'angles': (pitch, roll, yaw)  # 顺序：(pitch, roll, yaw)
        }

        # 计算每个像素的经纬度
        latlon_matrix, _, _ = pixel_to_latlon_matrix(camera_params['image_resolution'], camera_params, drone_params)

        # 提取四个角的经纬度
        ul_lon, ul_lat = latlon_matrix[0, 0, 1], latlon_matrix[0, 0, 0]
        ur_lon, ur_lat = latlon_matrix[0, -1, 1], latlon_matrix[0, -1, 0]
        lr_lon, lr_lat = latlon_matrix[-1, -1, 1], latlon_matrix[-1, -1, 0]
        ll_lon, ll_lat = latlon_matrix[-1, 0, 1], latlon_matrix[-1, 0, 0]

        # 选择UTM带
        utm_zone = int((np.floor((drone_lon + 180) / 6) % 60) + 1)
        hemisphere = 'N' if drone_lat >= 0 else 'S'
        utm_crs = f"EPSG:326{utm_zone}" if hemisphere == 'N' else f"EPSG:327{utm_zone}"

        # 将经纬度转换为UTM坐标
        transformer = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)
        ul_x, ul_y = transformer.transform(ul_lon, ul_lat)
        ur_x, ur_y = transformer.transform(ur_lon, ur_lat)
        ll_x, ll_y = transformer.transform(ll_lon, ll_lat)

        # 计算GeoTransform参数
        width, height = camera_params['image_resolution']
        x_res = (ur_x - ul_x) / width
        y_res = (ul_y - ll_y) / height

        transform = from_origin(ul_x, ul_y, x_res, y_res)

        # 创建GeoTIFF文件（这里写入虚拟数据，用户需替换为真实图像）
        output_tif = f"{photo_name}.tif"
        with rasterio.open(
                output_tif,
                'w',
                driver='GTiff',
                height=height,
                width=width,
                count=1,
                dtype=np.float32,
                crs=utm_crs,
                transform=transform,
        ) as dst:
            # 写入虚拟图像数据（用户可替换为真实图像）
            dummy_data = np.zeros((height, width), dtype=np.float32)
            dst.write(dummy_data, 1)

        print(f"Saved {output_tif}")


# 6. 调用函数处理照片
# 修改后的路径（推荐）
process_photos_from_excel(r"E:\Desktop\912pos\912.csv")