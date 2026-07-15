import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm


# 定义分类规则
def classify_pixel(value):
    if value in [31, 32, 33]:
        return 0  # Grassland
    elif value == 21:
        return 1  # Forests
    elif value == 22:
        return 2  # Shrublands
    elif value == 23:
        return 3  # Savannas
    elif value in [11, 12]:
        return 4  # Croplands
    elif value in [61, 62, 63, 64, 65, 66, 67]:
        return 5  # Bare
    else:
        return -1  # Unclassified or other


# 定义颜色映射
cmap = ListedColormap(['green', 'darkgreen', 'brown', 'yellow', 'orange', 'beige', 'white'])
norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5], cmap.N)

# 打开TIF文件
with rasterio.open('D:\\中科院class\\11.tif') as src:
    # 读取第一个波段的数据
    band = src.read(1)

    # 应用分类规则
    classified = np.array([classify_pixel(v) for v in band.flat])
    classified = classified.reshape(band.shape)

# 绘制分类后的图像
plt.figure(figsize=(10, 10))
plt.imshow(classified, cmap=cmap, norm=norm)
plt.colorbar(ticks=[0, 1, 2, 3, 4, 5], label='Land Cover Type')
plt.title(' Classified Land Cover')
plt.show()