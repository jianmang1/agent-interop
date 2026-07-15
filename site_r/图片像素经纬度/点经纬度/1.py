import numpy as np
from pyproj import Transformer

# ======= 已知参数（来自 Photogroup 和 Pose） =======
# 内参
f_px = 1913.333374  # 焦距（像素）
cx = 800.000000  # 主点 x
cy = 650.000000  # 主点 y

# 外参（相机位置，UTM坐标）
Xc, Yc, Zc = 257812.578411203, 3416828.47203852, 82.647443135269

# 姿态角（单位：度）
omega = -179.817731568884
phi = 0.506471351361202
kappa = -158.517583722715

# ======= 你点击的像素坐标 =======
clicked_points = [
    (314, 442),  # 示例1
    (225, 971),  # 示例2
]

# ======= 假设地面高程（UTM Z 值） =======
GROUND_HEIGHT = 16.4


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

for (u, v) in clicked_points:
    X, Y, Z = image_to_world(u, v, GROUND_HEIGHT)
    lon, lat = transformer.transform(X, Y)
    print(f"像素({u}, {v}) -> UTM: ({X:.3f}, {Y:.3f}, {Z:.3f}) -> 经纬度: ({lon:.6f}, {lat:.6f})")