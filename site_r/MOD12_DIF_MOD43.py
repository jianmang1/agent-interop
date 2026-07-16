import numpy as np
import rasterio
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# 设置文件路径
file_paths = [
    "D:\\MOD12Q2\\dif\\difsos2.tif",
    "D:\\MOD12Q2\\dif\\difeos2.tif",
    "D:\\MOD12Q2\\dif\\diflos2.tif"
]

# 设置区间边界
bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, np.inf]
labels = ['{}-{}'.format(bins[i], bins[i + 1] if bins[i + 1] != np.inf else '+') for i in range(len(bins) - 1)]

# 统一设置y轴的范围和间隔
y_max = 1e7
y_min = 0
y_interval = 0.25e7

# 增加 ax2 的 y 轴最大值以避免重叠
y_max_ax2 = 105

for file_path in file_paths:
    with rasterio.open(file_path) as src:
        array = src.read(1)
        valid_array = array[~np.isnan(array) & (array != src.nodata)]
        hist, bin_edges = np.histogram(valid_array, bins=bins)
        cumulative_hist = np.cumsum(hist)
        total_pixels = np.sum(hist)
        normalized_cumulative_hist = (cumulative_hist / total_pixels) * 100

        print(f"File: {file_path}")
        for label, count in zip(labels, hist):
            print(f"{label}: {count} pixels")

        fig, ax1 = plt.subplots()

        color = 'tab:gray'
        ax1.set_xlabel('Days', fontname="Arial", fontsize=20)
        ax1.set_ylabel('Frequency/pixel number', color=color, fontname="Arial", fontsize=20)
        ax1.bar(labels, hist, color=color)
        ax1.tick_params(axis='y', labelcolor=color)
        # 设置y轴范围和间隔
        ax1.set_ylim([y_min, y_max])
        ax1.yaxis.set_major_locator(MultipleLocator(y_interval))

        ax2 = ax1.twinx()
        color = 'tab:blue'
        ax2.set_ylabel('Cumulative Frequency (%)', color=color, fontname="Arial", fontsize=20)
        ax2.plot(labels, normalized_cumulative_hist, color=color, marker='o')
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.set_ylim([0, y_max_ax2])  # 增加 ax2 的 y 轴最大值

        # 设置x轴字体
        for tick in ax1.get_xticklabels():
            tick.set_fontname("Arial")
            tick.set_fontsize(10)

        fig.tight_layout()
        plt.show()



