import os  # 导入os模块
from osgeo import gdal
import numpy as np
import pandas as pd
from scipy.stats import normaltest, kstest
from scipy.optimize import curve_fit
from scipy.stats import linregress
import warnings

# 忽略所有警告
warnings.filterwarnings('ignore')

def bimodal_pdf(x, mu1, sigma1, mu2, sigma2, w):
    return w * np.exp(-0.5 * ((x - mu1) / sigma1) ** 2) / (sigma1 * np.sqrt(2 * np.pi)) + \
        (1 - w) * np.exp(-0.5 * ((x - mu2) / sigma2) ** 2) / (sigma2 * np.sqrt(2 * np.pi))

# 定义读取栅格数据的函数
def read_raster(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    dataset = gdal.Open(file_path)
    if dataset is None:
        raise RuntimeError(f"Failed to open the raster file: {file_path}")

    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()
    x_size = dataset.RasterXSize
    y_size = dataset.RasterYSize

    return data, x_size, y_size

# 读取重采样的土地利用数据
resampled_land_file = r'F:\个人\CLASS\新建文件夹\中科院_mode_resampled_clipped.tif'
print(f"Reading resampled land use data from: {resampled_land_file}")
resampled_land_data, x_size, y_size = read_raster(resampled_land_file)

# 找到特定值的像元位置
values_to_extract = [21, 22, 23, 24, 31, 32, 33, 61, 62, 63, 64, 65, 66, 67]

# 定义块大小
chunk_size = 1000  # 根据你的内存情况调整这个值

# 初始化存储结果的字典
results = {value: {} for value in values_to_extract}

# 循环读取EVI数据
for year in range(2001, 2024):
    evi_file = f'F:\MODIS43A4_DOY\SOS\mask_applied_masked_all_SoS_value_{year}.tif'
    print(f"Reading EVI data for year {year} from: {evi_file}")

    try:
        evi_data, _, _ = read_raster(evi_file)
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

                if len(evi_values) > 0:
                    # 过滤掉 NaN 和无穷大值
                    evi_values = np.array(evi_values)
                    evi_values = evi_values[np.isfinite(evi_values)]

                    if len(evi_values) > 0:
                        # 随机抽取子样本
                        sample_size = min(50, len(evi_values))  # 抽取50个样本或全部样本（如果少于50）
                        sampled_evi_values = np.random.choice(evi_values, size=sample_size, replace=False)

                        # 计算统计量
                        mean_evi = np.mean(sampled_evi_values)
                        std_evi = np.std(sampled_evi_values)
                        min_evi = np.min(sampled_evi_values)
                        q1_evi = np.percentile(sampled_evi_values, 25)
                        median_evi = np.median(sampled_evi_values)
                        q3_evi = np.percentile(sampled_evi_values, 75)
                        max_evi = np.max(sampled_evi_values)

                        # 正态性检验
                        stat_norm, p_norm = normaltest(sampled_evi_values)

                        # 均匀分布检验
                        stat_unif, p_unif = kstest(sampled_evi_values, 'uniform', args=(min_evi, max_evi - min_evi))

                        # 双峰分布检测
                        initial_guess = [mean_evi, std_evi, mean_evi + 1, std_evi, 0.5]
                        try:
                            params, _ = curve_fit(bimodal_pdf, np.linspace(min_evi, max_evi, 100),
                                                  bimodal_pdf(np.linspace(min_evi, max_evi, 100), *initial_guess),
                                                  p0=initial_guess)
                            mu1, sigma1, mu2, sigma2, w = params
                            bimodal_fit = True
                        except:
                            mu1, sigma1, mu2, sigma2, w = None, None, None, None, None
                            bimodal_fit = False

                        # 存储结果
                        if year not in results[value]:
                            results[value][year] = {
                                'mean': mean_evi,
                                'std': std_evi,
                                'min': min_evi,
                                'q1': q1_evi,
                                'median': median_evi,
                                'q3': q3_evi,
                                'max': max_evi,
                                'values': sampled_evi_values.tolist(),
                                'normal_p': p_norm,
                                'uniform_p': p_unif,
                                'bimodal_fit': bimodal_fit,
                                'mu1': mu1,
                                'sigma1': sigma1,
                                'mu2': mu2,
                                'sigma2': sigma2,
                                'w': w
                            }
                        else:
                            results[value][year]['mean'] = mean_evi
                            results[value][year]['std'] = std_evi
                            results[value][year]['min'] = min_evi
                            results[value][year]['q1'] = q1_evi
                            results[value][year]['median'] = median_evi
                            results[value][year]['q3'] = q3_evi
                            results[value][year]['max'] = max_evi
                            results[value][year]['values'].extend(sampled_evi_values.tolist())

# 分析趋势并输出到Excel
excel_file = 'F:\MODIS43A4_DOY\SOS\\allsos_class_results.xlsx'
writer = pd.ExcelWriter(excel_file, engine='openpyxl')

for value in values_to_extract:
    if results[value]:
        years = list(results[value].keys())
        means = [results[value][year]['mean'] for year in years]
        stds = [results[value][year]['std'] for year in years]
        mins = [results[value][year]['min'] for year in years]
        q1s = [results[value][year]['q1'] for year in years]
        medians = [results[value][year]['median'] for year in years]
        q3s = [results[value][year]['q3'] for year in years]
        maxs = [results[value][year]['max'] for year in years]

        # 收集所有年份的EVI值用于正态性和其他分布类型的检验
        evi_values_per_year = [np.array(results[value][year].get('values', [])) for year in years]

        # 初始化存储检验结果的字典
        distribution_tests = {year: {} for year in years}

        # 对每个年份的数据进行多种分布类型的检验
        for idx, evi_values in enumerate(evi_values_per_year):
            year = years[idx]
            if len(evi_values) > 0:
                # 正态性检验
                stat_norm, p_norm = normaltest(evi_values)
                distribution_tests[year]['Normal'] = {'stat': stat_norm, 'p-value': p_norm, 'fit': p_norm > 0.05}

                # 均匀分布检验
                stat_unif, p_unif = kstest(evi_values, 'uniform')
                distribution_tests[year]['Uniform'] = {'stat': stat_unif, 'p-value': p_unif, 'fit': p_unif > 0.05}
            else:
                distribution_tests[year] = {
                    'Normal': {'stat': None, 'p-value': None, 'fit': False},
                    'Uniform': {'stat': None, 'p-value': None, 'fit': False}
                }

        # 使用线性回归分析趋势
        slope, intercept, r_value, p_value, std_err = linregress(years, means)

        # 创建DataFrame
        df = pd.DataFrame({
            'Year': years,
            'Mean EVI': means,
            'Std EVI': stds,
            'Min EVI': mins,
            'Q1 EVI': q1s,
            'Median EVI': medians,
            'Q3 EVI': q3s,
            'Max EVI': maxs,
            'Normality p-value': [distribution_tests[year]['Normal']['p-value'] for year in years],
            'Normal Fit': [distribution_tests[year]['Normal']['fit'] for year in years],
            'Uniform p-value': [distribution_tests[year]['Uniform']['p-value'] for year in years],
            'Uniform Fit': [distribution_tests[year]['Uniform']['fit'] for year in years],
            'Bimodal Fit': [results[value][year]['bimodal_fit'] for year in years],
            'Mu1': [results[value][year]['mu1'] for year in years],
            'Sigma1': [results[value][year]['sigma1'] for year in years],
            'Mu2': [results[value][year]['mu2'] for year in years],
            'Sigma2': [results[value][year]['sigma2'] for year in years],
            'W': [results[value][year]['w'] for year in years]
        })

        # 添加趋势信息
        df['Trend'] = slope
        df['Trend Std Err'] = std_err
        df['p-value'] = p_value
        df['Significant'] = df['p-value'] < 0.05

        # 写入Excel
        sheet_name = f'Value_{value}'
        df.to_excel(writer, sheet_name=sheet_name, index=False)

# 保存Excel文件
writer.close()
print(f"Results exported to: {excel_file}")