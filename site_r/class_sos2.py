import os
from osgeo import gdal
import numpy as np
import pandas as pd
from scipy.stats import linregress, normaltest, kstest, uniform, expon, lognorm, gamma
from scipy.optimize import curve_fit
import warnings
from openpyxl import Workbook
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from scipy.stats import gaussian_kde, kstest, normaltest, lognorm, gamma
from scipy.optimize import curve_fit
from sklearn.mixture import GaussianMixture
import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
# 忽略所有警告
warnings.filterwarnings('ignore')

def preprocess_data(evi_values, method='remove_outliers'):
    if len(evi_values) == 0:
        return evi_values

    if method == 'remove_outliers':
        # 使用箱线图法去除异常值
        Q1 = np.percentile(evi_values, 25)
        Q3 = np.percentile(evi_values, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        evi_values_clean = evi_values[(evi_values >= lower_bound) & (evi_values <= upper_bound)]
        return evi_values_clean

    elif method == 'standardize':
        # 标准化
        scaler = StandardScaler()
        evi_values_scaled = scaler.fit_transform(evi_values.reshape(-1, 1)).flatten()
        return evi_values_scaled

    elif method == 'normalize':
        # 归一化
        scaler = MinMaxScaler()
        evi_values_normalized = scaler.fit_transform(evi_values.reshape(-1, 1)).flatten()
        return evi_values_normalized

    elif method == 'log_transform':
        # 对数变换
        evi_values_log = np.log1p(evi_values)
        return evi_values_log

    else:
        raise ValueError(f"Unknown preprocessing method: {method}")

# 定义双峰分布的概率密度函数
def bimodal_pdf(x, mu1, sigma1, mu2, sigma2, w):
    return (w * np.exp(-0.5 * ((x - mu1) / sigma1) ** 2) / (sigma1 * np.sqrt(2 * np.pi)) +
            (1 - w) * np.exp(-0.5 * ((x - mu2) / sigma2) ** 2) / (sigma2 * np.sqrt(2 * np.pi)))

from scipy.stats import gaussian_kde
import matplotlib.pyplot as plt

def fit_kde(evi_values, plot=False):
    if len(evi_values) == 0:
        return None, None

    # 计算KDE
    kde = gaussian_kde(evi_values)

    # 生成拟合曲线
    x_fit = np.linspace(evi_values.min(), evi_values.max(), 1000)
    y_fit = kde(x_fit)

    if plot:
        plt.hist(evi_values, bins=50, density=True, alpha=0.6, color='g', label='Histogram')
        plt.plot(x_fit, y_fit, 'r-', lw=2, label='KDE Fit')
        plt.title('Kernel Density Estimation (KDE)')
        plt.xlabel('EVI')
        plt.ylabel('Density')
        plt.legend()
        plt.show()

    return x_fit, y_fit
from sklearn.mixture import GaussianMixture

def fit_gmm(evi_values, n_components=2, plot=False):
    if len(evi_values) == 0:
        return None, None

    # 训练GMM模型
    gmm = GaussianMixture(n_components=n_components, random_state=42)
    gmm.fit(evi_values.reshape(-1, 1))

    # 生成拟合曲线
    x_fit = np.linspace(evi_values.min(), evi_values.max(), 1000).reshape(-1, 1)
    y_fit = np.exp(gmm.score_samples(x_fit))

    if plot:
        plt.hist(evi_values, bins=50, density=True, alpha=0.6, color='g', label='Histogram')
        plt.plot(x_fit, y_fit, 'r-', lw=2, label='GMM Fit')
        plt.title(f'Gaussian Mixture Model (GMM) with {n_components} Components')
        plt.xlabel('EVI')
        plt.ylabel('Density')
        plt.legend()
        plt.show()

    return x_fit, y_fit
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
    evi_file = f'F:\\MODIS43A4_DOY\\SOS\\mask_applied_masked_all_SoS_value_{year}.tif'
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
                    evi_values = evi_values[np.isfinite(evi_values)]

                    if len(evi_values) > 0:
                        # 计算统计量
                        stats = {
                            'mean': np.mean(evi_values),
                            'std': np.std(evi_values),
                            'min': np.min(evi_values),
                            'q1': np.percentile(evi_values, 25),
                            'median': np.median(evi_values),
                            'q3': np.percentile(evi_values, 75),
                            'max': np.max(evi_values),
                            'values': evi_values.tolist()
                        }

                        # 存储结果
                        if year not in results[value]:
                            results[value][year] = stats
                        else:
                            for key, val in stats.items():
                                if key != 'values':
                                    results[value][year][key] = val
                                else:
                                    results[value][year][key].extend(val)

# 分析趋势并输出到Excel
excel_file = r'F:\MODIS43A4_DOY\SOS\allsos_class_results.xlsx'
writer = pd.ExcelWriter(excel_file, engine='openpyxl')

# 在主循环中添加预处理、KDE 和 GMM 拟合
for value in values_to_extract:
    if results[value]:
        years = list(results[value].keys())
        years.sort()  # 确保年份按顺序排列

        # 提取统计信息
        means = [results[value][year]['mean'] for year in years]
        stds = [results[value][year]['std'] for year in years]
        mins = [results[value][year]['min'] for year in years]
        q1s = [results[value][year]['q1'] for year in years]
        medians = [results[value][year]['median'] for year in years]
        q3s = [results[value][year]['q3'] for year in years]
        maxs = [results[value][year]['max'] for year in years]
        evi_values_per_year = [np.array(results[value][year].get('values', [])) for year in years]

        # 初始化存储检验结果的字典
        distribution_tests = {year: {} for year in years}
        kde_results = {year: {} for year in years}
        gmm_results = {year: {} for year in years}

        # 对每个年份的数据进行多种分布类型的检验、预处理、KDE 和 GMM 拟合
        for idx, evi_values in enumerate(evi_values_per_year):
            year = years[idx]
            if len(evi_values) > 0:
                # 正态性检验
                stat_norm, p_norm = normaltest(evi_values)
                distribution_tests[year]['Normal'] = {'stat': stat_norm, 'p-value': p_norm, 'fit': p_norm > 0.05}

                # 均匀分布检验
                stat_unif, p_unif = kstest(evi_values, 'uniform')
                distribution_tests[year]['Uniform'] = {'stat': stat_unif, 'p-value': p_unif, 'fit': p_unif > 0.05}

                # 指数分布检验
                stat_expo, p_expo = kstest(evi_values, 'expon')
                distribution_tests[year]['Exponential'] = {'stat': stat_expo, 'p-value': p_expo, 'fit': p_expo > 0.05}

                # 对数正态分布检验
                s, loc, scale = lognorm.fit(evi_values, floc=0)
                stat_lognorm, p_lognorm = kstest(evi_values, 'lognorm', args=(s, loc, scale))
                distribution_tests[year]['Lognormal'] = {'stat': stat_lognorm, 'p-value': p_lognorm, 'fit': p_lognorm > 0.05}

                # 伽玛分布检验
                a, loc, scale = gamma.fit(evi_values, floc=0)
                stat_gamma, p_gamma = kstest(evi_values, 'gamma', args=(a, loc, scale))
                distribution_tests[year]['Gamma'] = {'stat': stat_gamma, 'p-value': p_gamma, 'fit': p_gamma > 0.05}

                # 双峰分布检测
                try:
                    params, _ = curve_fit(bimodal_pdf, np.linspace(min(evi_values), max(evi_values), 100),
                                          np.histogram(evi_values, bins=100, density=True)[0],
                                          p0=[0, 1, 1, 1, 0.5])
                    fitted_pdf = bimodal_pdf(np.linspace(min(evi_values), max(evi_values), 100), *params)
                    stat_bimodal, p_bimodal = kstest(evi_values, lambda x: np.interp(x, np.linspace(min(evi_values), max(evi_values), 100), fitted_pdf))
                    distribution_tests[year]['Bimodal'] = {'stat': stat_bimodal, 'p-value': p_bimodal, 'fit': p_bimodal > 0.05}
                except Exception as e:
                    print(f"Error fitting bimodal distribution for year {year}: {e}")
                    distribution_tests[year]['Bimodal'] = {'stat': None, 'p-value': None, 'fit': False}

                # 数据预处理
                evi_values_clean = preprocess_data(evi_values, method='remove_outliers')
                evi_values_standardized = preprocess_data(evi_values, method='standardize')
                evi_values_normalized = preprocess_data(evi_values, method='normalize')
                evi_values_log = preprocess_data(evi_values, method='log_transform')

                # KDE 拟合
                x_fit_kde, y_fit_kde = fit_kde(evi_values_clean)
                kde_results[year]['x_fit'] = x_fit_kde
                kde_results[year]['y_fit'] = y_fit_kde

                # GMM 拟合
                x_fit_gmm, y_fit_gmm = fit_gmm(evi_values_clean, n_components=2)
                gmm_results[year]['x_fit'] = x_fit_gmm
                gmm_results[year]['y_fit'] = y_fit_gmm

            else:
                distribution_tests[year] = {
                    'Normal': {'stat': None, 'p-value': None, 'fit': False},
                    'Uniform': {'stat': None, 'p-value': None, 'fit': False},
                    'Exponential': {'stat': None, 'p-value': None, 'fit': False},
                    'Lognormal': {'stat': None, 'p-value': None, 'fit': False},
                    'Gamma': {'stat': None, 'p-value': None, 'fit': False},
                    'Bimodal': {'stat': None, 'p-value': None, 'fit': False}
                }
                kde_results[year] = {'x_fit': None, 'y_fit': None}
                gmm_results[year] = {'x_fit': None, 'y_fit': None}

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
            'Exponential p-value': [distribution_tests[year]['Exponential']['p-value'] for year in years],
            'Exponential Fit': [distribution_tests[year]['Exponential']['fit'] for year in years],
            'Lognormal p-value': [distribution_tests[year]['Lognormal']['p-value'] for year in years],
            'Lognormal Fit': [distribution_tests[year]['Lognormal']['fit'] for year in years],
            'Gamma p-value': [distribution_tests[year]['Gamma']['p-value'] for year in years],
            'Gamma Fit': [distribution_tests[year]['Gamma']['fit'] for year in years],
            'Bimodal p-value': [distribution_tests[year]['Bimodal']['p-value'] for year in years],
            'Bimodal Fit': [distribution_tests[year]['Bimodal']['fit'] for year in years],
            'KDE Fit X': [kde_results[year]['x_fit'].tolist() if kde_results[year]['x_fit'] is not None else None for year in years],
            'KDE Fit Y': [kde_results[year]['y_fit'].tolist() if kde_results[year]['y_fit'] is not None else None for year in years],
            'GMM Fit X': [gmm_results[year]['x_fit'].flatten().tolist() if gmm_results[year]['x_fit'] is not None else None for year in years],
            'GMM Fit Y': [gmm_results[year]['y_fit'].flatten().tolist() if gmm_results[year]['y_fit'] is not None else None for year in years]
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
print(f"Results saved to: {excel_file}")