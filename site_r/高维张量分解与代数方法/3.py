import rasterio
import numpy as np
from libpysal.weights import W
from esda.moran import Moran
from esda.getisord import G_Local
import os
from tqdm import tqdm

# 配置环境优化
os.environ["OMP_NUM_THREADS"] = "4"  # 限制OpenMP线程数
os.environ["MKL_NUM_THREADS"] = "4"


def chunk_generator(data, valid_mask, chunk_size=256, buffer=1):
    """
    分块生成器：带缓冲区的数据分块
    参数：
        data: 原始数据矩阵
        valid_mask: 有效值掩膜
        chunk_size: 分块尺寸（默认256x256）
        buffer: 邻接缓冲区大小（Queen邻接需要至少1）
    """
    rows, cols = data.shape
    for i in range(0, rows, chunk_size):
        for j in range(0, cols, chunk_size):
            # 计算块边界
            row_start = max(0, i - buffer)
            row_end = min(rows, i + chunk_size + buffer)
            col_start = max(0, j - buffer)
            col_end = min(cols, j + chunk_size + buffer)

            # 提取带缓冲区的数据块
            chunk_data = data[row_start:row_end, col_start:col_end]
            chunk_mask = valid_mask[row_start:row_end, col_start:col_end]

            # 生成全局坐标映射
            chunk_rows, chunk_cols = np.where(chunk_mask)
            global_rows = row_start + chunk_rows
            global_cols = col_start + chunk_cols

            yield (global_rows, global_cols), (chunk_rows, chunk_cols), (row_start, row_end, col_start, col_end)


# --------------------------
# 主程序
# --------------------------
# 1. 数据读取
tif_path = "D:/MODIS43A4_2024/SOS/500m(unmask0)/mean_values.tif"
with rasterio.open(tif_path) as src:
    sos_data = src.read(1)
    transform = src.transform
    crs = src.crs

sos_data = np.where(sos_data == -9999, np.nan, sos_data).astype(np.float32)
valid_mask = ~np.isnan(sos_data)
all_rows, all_cols = np.where(valid_mask)

# 2. 构建全局ID映射
print("构建全局ID映射...")
global_id_map = {}
for idx, (r, c) in tqdm(enumerate(zip(all_rows, all_cols)), total=len(all_rows)):
    global_id_map[(r, c)] = idx

# 3. 分块构建邻接矩阵
chunk_size = 256  # 根据内存调整（推荐256-512）
buffer_size = 1  # Queen邻接需要1像素缓冲区
neighbors = [(-1, -1), (-1, 0), (-1, 1),
             (0, -1), (0, 1),
             (1, -1), (1, 0), (1, 1)]

adjacency = {}
total_chunks = (sos_data.shape[0] // chunk_size + 1) * (sos_data.shape[1] // chunk_size + 1)

print(f"开始分块处理，共{total_chunks}个区块...")
for (g_rows, g_cols), (c_rows, c_cols), bounds in tqdm(chunk_generator(sos_data, valid_mask, chunk_size, buffer_size),
                                                       total=total_chunks):
    # 处理当前块中的每个有效像元
    for local_idx, (r, c) in enumerate(zip(c_rows, c_cols)):
        global_r = g_rows[local_idx]
        global_c = g_cols[local_idx]
        current_id = global_id_map[(global_r, global_c)]

        # 寻找邻接像元
        neighbor_ids = []
        for dr, dc in neighbors:
            nr = global_r + dr
            nc = global_c + dc
            if (nr, nc) in global_id_map:
                neighbor_ids.append(global_id_map[(nr, nc)])

        adjacency[current_id] = neighbor_ids

# 4. 创建稀疏权重矩阵
print("创建权重矩阵...")
w = W(adjacency, silence_warnings=True)

# 5. 统计分析
data_clean = sos_data[valid_mask].flatten()

# Moran's I 分析
print("计算Moran's I...")
moran = Moran(data_clean, w, permutations=99)
print(f"全局Moran's I: {moran.I:.4f}, p-value: {moran.p_sim:.4f}")

# Getis-Ord Gi* 分析
print("计算Getis-Ord Gi*...")
gi = G_Local(data_clean, w, permutations=99)

# 6. 结果输出
print("保存结果...")
z_scores = np.full(sos_data.shape, np.nan, dtype=np.float32)
z_scores[all_rows, all_cols] = gi.z_sim

with rasterio.open("Gi_Z_Scores.tif", "w",
                   driver="GTiff",
                   height=z_scores.shape[0],
                   width=z_scores.shape[1],
                   count=1,
                   dtype=np.float32,
                   crs=crs,
                   transform=transform,
                   compress='LZW') as dst:
    dst.write(z_scores, 1)

print("处理完成！结果已保存为 Gi_Z_Scores.tif")