import numpy as np
from pyproj import Transformer
from osgeo import gdal, osr
import matplotlib.pyplot as plt

# ======= 已知参数（来自 Photogroup 和 Pose） =======
# 内参
f_px = 3644.67566532602  # 焦距（像素）
cx = 2736.10146760854  # 主点 x
cy = 1836.06257818379  # 主点 y

# 外参（相机位置，UTM坐标）
Xc, Yc, Zc = 257812.578411203, 3416828.47203852, 82.647443135269

# 姿态角（单位：度）
omega = -179.817731568884
phi = 0.506471351361202
kappa = -158.517583722715

# ======= 你点击的像素坐标 =======
clicked_points = [
    (3146, 442),  # 示例1
    (2254, 971),  # 示例2
]

# ======= 假设地面高程（UTM Z 值） =======
GROUND_HEIGHT = 20


# ======= 计算旋转矩阵 =======
def rotation_matrix(omega_deg, phi_deg, kappa_deg):
    w = np.deg2rad(omega_deg)
    p = np.deg2rad(phi_deg)
    k = np.deg2rad(kappa_deg)

    R_omega = np.array([
        [1, 0, 0],
        [0, np.cos(w), np.sin(w)],
        [0, -np.sin(w), np.cos(w)]
    ])

    R_phi = np.array([
        [np.cos(p), 0, -np.sin(p)],
        [0, 1, 0],
        [np.sin(p), 0, np.cos(p)]
    ])

    R_kappa = np.array([
        [np.cos(k), np.sin(k), 0],
        [-np.sin(k), np.cos(k), 0],
        [0, 0, 1]
    ])

    return R_kappa @ R_phi @ R_omega


R = rotation_matrix(omega, phi, kappa)


# ======= 计算地理坐标 =======
def image_to_world(u, v, ground_z):
    # 像素坐标 → 相机归一化坐标
    x_img = (u - cx) / f_px
    y_img = (v - cy) / f_px
    cam_vec = np.array([x_img, y_img, 1.0])

    # 相机坐标系 → 地面坐标系方向向量
    dir_vec = R @ cam_vec

    # 计算交点参数 t
    t = (ground_z - Zc) / dir_vec[2]

    # 计算 UTM 坐标
    X = Xc + t * dir_vec[0]
    Y = Yc + t * dir_vec[1]
    Z = ground_z

    return X, Y, Z


# ======= 坐标转换：UTM → 经纬度 =======
transformer = Transformer.from_crs("EPSG:32650", "EPSG:4326", always_xy=True)

# 存储所有计算出的UTM坐标
utm_points = []

for (u, v) in clicked_points:
    X, Y, Z = image_to_world(u, v, GROUND_HEIGHT)
    lon, lat = transformer.transform(X, Y)
    utm_points.append((X, Y))
    print(f"像素({u}, {v}) -> UTM: ({X:.3f}, {Y:.3f}, {Z:.3f}) -> 经纬度: ({lon:.6f}, {lat:.6f})")

# ======= 处理TIFF文件 =======
# 读取TIFF文件
tiff_path = r"E:\Desktop\912pos\912.csv.tif"
dataset = gdal.Open(tiff_path, gdal.GA_ReadOnly)

if dataset is None:
    print("无法打开TIFF文件")
    exit()

# 获取图像信息
cols = dataset.RasterXSize
rows = dataset.RasterYSize
bands = dataset.RasterCount

print(f"图像尺寸: {cols} x {rows}, 波段数: {bands}")

# 读取图像数据
image_data = dataset.ReadAsArray()

# 创建新的TIFF文件并添加地理参考
driver = gdal.GetDriverByName('GTiff')
output_path = r"E:\Desktop\912pos\912_georeferenced.tif"

# 获取左上角和右下角的UTM坐标（这里简化处理，实际应根据图像范围计算）
# 假设图像四个角点的UTM坐标可以通过相机模型计算
# 这里我们简单使用第一个点和图像尺寸估算
if utm_points:
    ulx = utm_points[0][0] - 100  # 假设左上角X
    uly = utm_points[0][1] + 100  # 假设左上角Y
    lrx = utm_points[0][0] + cols / 10  # 假设右下角X
    lry = utm_points[0][1] - rows / 10  # 假设右下角Y

    # 计算像素大小
    pixel_width = (lrx - ulx) / cols
    pixel_height = (lry - uly) / rows

    # 创建输出数据集
    out_dataset = driver.Create(output_path, cols, rows, bands, dataset.GetRasterBand(1).DataType)

    # 设置地理变换参数
    out_dataset.SetGeoTransform([ulx, pixel_width, 0, uly, 0, pixel_height])

    # 设置坐标系
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(32650)  # UTM zone 50N
    out_dataset.SetProjection(srs.ExportToWkt())

    # 写入数据
    for i in range(bands):
        out_band = out_dataset.GetRasterBand(i + 1)
        out_band.WriteArray(image_data[i] if bands > 1 else image_data)

    # 关闭数据集
    out_dataset = None
    print(f"已创建地理参考TIFF文件: {output_path}")
else:
    print("没有计算出UTM坐标，无法添加地理参考")

# 关闭原始数据集
dataset = None

# 可视化结果（可选）
if bands == 3:
    # 如果是RGB图像
    plt.figure(figsize=(10, 8))
    plt.imshow(np.transpose(image_data, (1, 2, 0)))
    for i, (u, v) in enumerate(clicked_points):
        plt.plot(u, v, 'ro', markersize=8)
        plt.text(u + 20, v + 20, f'Point {i + 1}', color='red', fontsize=12)
    plt.title('点击点位置可视化')
    plt.show()
elif bands == 1:
    # 如果是单波段图像
    plt.figure(figsize=(10, 8))
    plt.imshow(image_data, cmap='gray')
    for i, (u, v) in enumerate(clicked_points):
        plt.plot(u, v, 'ro', markersize=8)
        plt.text(u + 20, v + 20, f'Point {i + 1}', color='red', fontsize=12)
    plt.title('点击点位置可视化')
    plt.show()