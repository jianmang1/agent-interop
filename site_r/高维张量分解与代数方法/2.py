# -*- coding: utf-8 -*-
"""
MODIS物候参数（SOS/POS/EOS）时空张量分析
作者: Your Name
日期: 2024-06-05
"""

import numpy as np
import tensorly as tl
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import os

# ---------------------------
# 0. 参数配置（根据实际数据修改!）
# ---------------------------
data_path = 'temp.dat'  # 内存映射文件路径
output_dir = './results/'  # 输出目录
H, W, B, T = 1200, 1800, 3, 24  # 空间高度、宽度、波段数、时间年数
ranks = [50, 50, 3, 5]  # Tucker分解维度 [H, W, B, T]
chunk_size = (512, 512, 3, 6)  # 分块计算尺寸 (H, W, B, T)

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)


# ---------------------------
# 1. 数据加载与预处理
# ---------------------------
def load_and_normalize(data_path, H, W, B, T):
    """加载内存映射文件并进行标准化"""
    # 加载内存映射文件（只读模式）
    X = np.memmap(data_path, dtype=np.float32, mode='r', shape=(H, W, B, T))

    # 创建可写入的内存映射文件用于存储标准化后数据
    X_norm = np.memmap(os.path.join(output_dir, 'temp_norm.dat'),
                       dtype=np.float32, mode='w+', shape=(H, W, B, T))

    # 逐波段-时间标准化
    for b in range(B):
        for t in range(T):
            # 提取当前波段-时间数据
            block = X[:, :, b, t].copy()  # 创建内存副本避免修改原数据

            # 标准化处理
            scaler = StandardScaler()
            X_norm[:, :, b, t] = scaler.fit_transform(block)

            # 释放内存
            del block

    return X_norm


print("步骤1: 数据标准化...")
X = load_and_normalize(data_path, H, W, B, T)


# ---------------------------
# 2. 高维张量分解（Tucker）
# 修改后的Tucker分解函数
def tucker_decomposition(X, ranks, chunk_size):
    """Tucker分解（仅使用NumPy后端）"""
    print("未安装Dask，使用NumPy后端...")
    tl.set_backend('numpy')

    # 尝试降低秩、增加迭代次数、使用随机初始化
    core, factors = tl.decomposition.tucker(
        X.astype(np.float32),
        rank=ranks,
        init='random',  # 改为随机初始化
        tol=1e-5,  # 降低收敛阈值
        n_iter_max=200,  # 增加最大迭代次数
        svd='truncated_svd'  # 使用截断SVD
    )
    return core, factors


# 调整ranks参数（示例）
ranks = [5, 5, 3, 3]  # 降低分解秩

print("\n步骤2: 执行Tucker分解...")
core, factors = tucker_decomposition(X, ranks, chunk_size)

# ---------------------------
# 3. 结果可视化
# ---------------------------
def plot_band_factors(A_band, output_dir):
    """绘制波段因子矩阵"""
    plt.figure(figsize=(10, 6))
    plt.imshow(A_band, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')
    plt.colorbar(label='权重系数', shrink=0.8)
    plt.xticks(np.arange(A_band.shape[1]), [f'成分{i + 1}' for i in range(A_band.shape[1])])
    plt.yticks(np.arange(3), ['SOS', 'POS', 'EOS'])
    plt.title("物候参数波段因子矩阵", fontsize=14)
    plt.savefig(os.path.join(output_dir, 'band_factors.png'), dpi=300, bbox_inches='tight')
    plt.close()


def plot_spatial_pattern(factors, H, W, output_dir):
    """绘制空间主成分"""
    spatial_H = factors[0][:, 0].reshape(H, 1)
    spatial_W = factors[1][:, 0].reshape(1, W)
    pattern = np.dot(spatial_H, spatial_W)

    plt.figure(figsize=(12, 8))
    plt.imshow(pattern, cmap='viridis',
               extent=[0, W, H, 0],  # 调整坐标轴为实际地理范围
               aspect='auto')
    plt.colorbar(label='空间模式强度')
    plt.title("空间主成分联合分布 (H-W方向)", fontsize=14)
    plt.savefig(os.path.join(output_dir, 'spatial_pattern.png'), dpi=300, bbox_inches='tight')
    plt.close()


def plot_time_components(factors, output_dir):
    """绘制时间成分演化"""
    years = np.arange(2001, 2001 + T)
    A_time = factors[3]

    plt.figure(figsize=(12, 6))
    for i in range(3):  # 绘制前3个成分
        plt.plot(years, A_time[:, i],
                 marker='o', linestyle='--',
                 linewidth=1.5, markersize=6,
                 label=f'时间成分{i + 1}')

    plt.xlabel('年份', fontsize=12)
    plt.ylabel('成分强度', fontsize=12)
    plt.title("物候参数时间演化趋势", fontsize=14)
    plt.legend(loc='upper left')
    plt.grid(alpha=0.3)
    plt.savefig(os.path.join(output_dir, 'time_components.png'), dpi=300, bbox_inches='tight')
    plt.close()


print("\n步骤3: 生成可视化结果...")
plot_band_factors(factors[2], output_dir)
plot_spatial_pattern(factors, H, W, output_dir)
plot_time_components(factors, output_dir)


# ---------------------------
# 4. 异常检测与保存结果
# ---------------------------
def detect_anomalies(X, core, factors, output_dir):
    """计算重构误差异常区域"""
    X_recon = tl.tucker_to_tensor(core, factors)
    error = np.mean((X - X_recon) ** 2, axis=(2, 3))  # 按空间位置聚合

    plt.figure(figsize=(12, 8))
    plt.imshow(error, cmap='Reds',
               vmax=np.percentile(error, 95),  # 取95%分位数作为上限
               aspect='auto')
    plt.colorbar(label='均方误差 (MSE)')
    plt.title("物候参数重构误差热点", fontsize=14)
    plt.savefig(os.path.join(output_dir, 'anomalies.png'), dpi=300, bbox_inches='tight')
    plt.close()
    return error


print("\n步骤4: 异常检测...")
error_map = detect_anomalies(X, core, factors, output_dir)

# 保存分解结果
np.savez_compressed(
    os.path.join(output_dir, 'tucker_results.npz'),
    core=core,
    factors=factors,
    error_map=error_map,
    metadata={
        'bands': ['SOS', 'POS', 'EOS'],
        'years': list(range(2001, 2025)),
        'ranks': ranks
    }
)

print("\n分析完成! 结果保存至:", output_dir)