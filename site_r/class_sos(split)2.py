import os
import numpy as np
from osgeo import gdal
from scipy.stats import f_oneway
import pandas as pd
from itertools import combinations
import statsmodels.api as sm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import matplotlib.pyplot as plt
import seaborn as sns

# 定义函数读取栅格数据
def read_raster(file_path, chunk_size=1000):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ds = gdal.Open(file_path)
    if ds is None:
        raise RuntimeError(f"Failed to open file: {file_path}")

    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    return data, ds.RasterXSize, ds.RasterYSize, chunk_size

# 读取重采样的土地利用数据
resampled_land_file = r'F:\个人\CLASS\新建文件夹\中科院_mode_resampled_clipped.tif'

print(f"Reading resampled land use data from: {resampled_land_file}")
resampled_land_data, x_size, y_size, chunk_size = read_raster(resampled_land_file)

# 找到特定值的像元位置
values_to_extract = [21, 22, 23, 24, 31, 32, 33, 61, 62, 63, 64, 65, 66, 67]

# 初始化存储结果的字典，按土地利用类型分类
results_by_type = {value: [] for value in values_to_extract}

# 抽样比例
sample_fraction = 0.01  # 抽取1%的数据

# 循环读取EVI数据
for year in range(2001, 2024):
    evi_file = fr'F:\MODIS43A4_DOY\SOS\mask_applied_masked_all_SoS_value_{year}.tif'
    print(f"Reading EVI data for year {year} from: {evi_file}")

    try:
        evi_data, _, _, _ = read_raster(evi_file)
    except Exception as e:
        print(f"Error reading EVI data for year {year}: {e}")
        continue  # 跳过无法读取的年份

    # 分块处理
    for y in range(0, y_size, chunk_size):
        for x in range(0, x_size, chunk_size):
            end_y = min(y + chunk_size, y_size)
            end_x = min(x + chunk_size, x_size)

            # 提取当前块的数据
            land_chunk = resampled_land_data[y:end_y, x:end_x]
            evi_chunk = evi_data[y:end_y, x:end_x]

            # 确保两个块的形状一致
            if land_chunk.shape != evi_chunk.shape:
                raise ValueError(f"Shapes do not match: land_chunk {land_chunk.shape}, evi_chunk {evi_chunk.shape}")

            # 对于每个土地利用类型，应用掩码提取特定像元的EVI值，并排除无效值 -9999
            for value in values_to_extract:
                mask_chunk = (land_chunk == value) & (evi_chunk != -9999)
                evi_values = evi_chunk[mask_chunk].flatten()

                # 抽样
                if len(evi_values) > 0:
                    sampled_evi_values = np.random.choice(evi_values, size=int(len(evi_values) * sample_fraction), replace=False)
                    results_by_type[value].extend(sampled_evi_values)

# 过滤掉空列表
results_by_type = {k: v for k, v in results_by_type.items() if v}

# 创建DataFrame用于ANOVA和Tukey's HSD测试
data = []
for value, evi_values in results_by_type.items():
    for evi in evi_values:
        data.append({'Land Use': value, 'EVI': evi})

df = pd.DataFrame(data)

# 将EVI值转换为float32以节省内存
df['EVI'] = df['EVI'].astype(np.float32)

# 进行ANOVA分析
anova_result = f_oneway(*[df[df['Land Use'] == value]['EVI'] for value in values_to_extract])
print(f"ANOVA F-statistic: {anova_result.statistic:.4f}, P-value: {anova_result.pvalue:.4f}")

if anova_result.pvalue < 0.05:
    print("ANOVA indicates significant differences between groups.")
else:
    print("ANOVA does not indicate significant differences between groups.")

# 进行Tukey's HSD测试
tukey = pairwise_tukeyhsd(endog=df['EVI'], groups=df['Land Use'], alpha=0.05)

# 打印Tukey's HSD测试结果
print(tukey)

# 将Tukey's HSD结果转换为DataFrame
tukey_df = pd.DataFrame(data=tukey._results_table.data[1:], columns=tukey._results_table.data[0])

# 添加字母标记
group_letters = {}
letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
letter_index = 0
assigned_letters = {}

for i, row in tukey_df.iterrows():
    group1 = int(row['group1'])
    group2 = int(row['group2'])
    reject = row['reject']

    if group1 not in assigned_letters:
        assigned_letters[group1] = letters[letter_index]
        letter_index += 1

    if group2 not in assigned_letters and not reject:
        assigned_letters[group2] = assigned_letters[group1]
    elif group2 not in assigned_letters and reject:
        assigned_letters[group2] = letters[letter_index]
        letter_index += 1

for value in values_to_extract:
    if value in assigned_letters:
        group_letters[value] = assigned_letters[value]
    else:
        group_letters[value] = 'N/A'  # 如果某个组没有参与比较

# 添加字母标记到原始DataFrame
df['Letter'] = df['Land Use'].map(group_letters)

# 绘制带字母标记的箱线图
plt.figure(figsize=(12, 8))
sns.boxplot(data=df, x='Land Use', y='EVI')
for i, (value, letter) in enumerate(group_letters.items()):
    plt.text(i, df[df['Land Use'] == value]['EVI'].max() + 0.05, letter, ha='center', va='bottom', fontsize=12, fontweight='bold')

plt.title('EVI Distribution by Land Use with Tukey HSD Letters')
plt.xlabel('Land Use')
plt.ylabel('EVI')
plt.xticks(rotation=45, ha='right')  # 旋转x轴标签以避免重叠
plt.tight_layout()

# 保存图表
output_dir = r'F:\MODIS43A4_DOY\SOS\output_EVI_values_by_type'
os.makedirs(output_dir, exist_ok=True)
output_plot_file = os.path.join(output_dir, 'evi_distribution_with_tukey_letters.png')
plt.savefig(output_plot_file)
plt.show()

print("Box plot with Tukey HSD letters has been saved to:", output_plot_file)