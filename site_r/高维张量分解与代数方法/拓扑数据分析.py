import rasterio
import numpy as np
import gudhi as gd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.utils import resample


def load_and_preprocess(file_path, max_samples=16000):
    """加载并预处理数据"""
    with rasterio.open(file_path) as src:
        data = src.read(1)
        data[data == -9999] = np.nan

    # 创建坐标网格
    x = np.arange(data.shape[1])
    y = np.arange(data.shape[0])
    xx, yy = np.meshgrid(x, y)

    # 提取非NaN值及其坐标
    mask = ~np.isnan(data)
    points = np.vstack([xx[mask], yy[mask], data[mask]]).T

    # 智能采样策略
    if len(points) > max_samples:
        points = resample(points,
                          replace=False,
                          n_samples=max_samples,
                          random_state=42)
    return points, data.shape


def compute_topology(points):
    """计算拓扑特征"""
    scaler = MinMaxScaler()
    scaled_points = scaler.fit_transform(points[:, :2])  # 只缩放空间坐标

    alpha_complex = gd.AlphaComplex(points=scaled_points)
    simplex_tree = alpha_complex.create_simplex_tree()

    persistence = simplex_tree.persistence()

    return persistence


def visualize_analysis(persistence, points):
    """可视化分析结果"""
    plt.figure(figsize=(15, 8))

    # 原始数据点分布
    plt.subplot(1, 2, 1)
    plt.scatter(points[:, 0], points[:, 1], c=points[:, 2], cmap='viridis')
    plt.colorbar(label='Value')
    plt.title('Valid Data Points Distribution')

    # 持久性图
    plt.subplot(1, 2, 2)
    gd.plot_persistence_diagram(persistence)
    plt.title('Persistence Diagram')

    plt.tight_layout()
    plt.show()


# 执行分析流程
file_path = r'D:\MODIS43A4_2024\SOS\500m(unmask0)\mean_values.tif'

# 数据预处理（自动处理大数据）
point_cloud, orig_shape = load_and_preprocess(file_path)

# 拓扑计算
persistence = compute_topology(point_cloud)

# 可视化分析
visualize_analysis(persistence, point_cloud)

# 高级特征提取
print("关键拓扑指标：")
for dim in [0, 1]:
    lifetimes = [p[1][1] - p[1][0] for p in persistence if p[0] == dim and p[1][1] != float('inf')]
    if lifetimes:
        print(f"H{dim}特征: 平均持续{np.mean(lifetimes):.3f}, 最大持续{max(lifetimes):.3f}")