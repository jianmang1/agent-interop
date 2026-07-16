import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pymc as pm
import arviz as az
from multiprocessing import freeze_support

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# 数据预处理
def preprocess_data(data):
    data = data.copy()
    for col in data.columns:
        if col not in ['站点', 'lastyear_LOS']:
            data[col] = data[col].clip(lower=data[col].quantile(0.01), upper=data[col].quantile(0.99))
    return data


# 数据标准化
def standardize_data(x):
    # Min-Max 标准化，将数据缩放到 [0, 1]
    return (x - x.min()) / (x.max() - x.min())


# 定义分析函数
def fit_change_point_model(data, pheno):
    try:
        df = data[['lastyear_LOS', pheno]].dropna()
        if len(df) < 10:
            print(f"样本不足，跳过 {pheno}")
            return None

        x = df['lastyear_LOS'].values
        y = df[pheno].values

        # 标准化年份
        x_scaled = standardize_data(x)

        with pm.Model() as model:
            # 调整先验分布
            a = pm.Normal('a', mu=np.mean(y), sigma=10)
            b1 = pm.Normal('b1', mu=0, sigma=5)
            b2 = pm.Normal('b2', mu=0, sigma=5)
            cp = pm.Uniform('cp', lower=x_scaled.min(), upper=x_scaled.max())

            # 分段预测
            y_pred = pm.math.clip(
                a + b1 * x_scaled + (b2 - b1) * pm.math.switch(x_scaled >= cp, x_scaled - cp, 0),
                -1e6, 1e6
            )
            sigma = pm.HalfNormal('sigma', sigma=10)
            pm.Normal('obs', mu=y_pred, sigma=sigma, observed=y)

            # 采样设置
            trace = pm.sample(
                draws=2000,
                tune=2000,
                chains=4,
                cores=1,  # Windows 下设为 1
                target_accept=0.95,
                return_inferencedata=True
            )
        return trace, x.min(), x.max()
    except Exception as e:
        print(f'Error in {pheno}: {str(e)}')
        return None


def analyze_phenology(data, title):
    results = {}
    pheno_columns = [
        '开始展叶期', '展叶盛期', '花序或花蕾出现期', '开花始期',
        '开花盛期', '开花末期', '果实成熟期', '果实脱落开始期',
        '果实脱落末期', '叶开始变色期', '叶全部变色期'
    ]

    for pheno in pheno_columns:
        print(f'Analyzing {pheno}...')
        result = fit_change_point_model(data, pheno)
        if result is not None:
            trace, x_min, x_max = result
            cp_samples = trace.posterior['cp'].values.flatten()
            cp_original = cp_samples * (x_max - x_min) + x_min
            results[pheno] = {
                'trace': trace,
                'cp_original': cp_original,
                'x_min': x_min,
                'x_max': x_max
            }
    return results


def plot_results(data, results, title):
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)

    for pheno, res in results.items():
        df = data[['lastyear_LOS', pheno]].dropna()
        x = df['lastyear_LOS'].values
        y = df[pheno].values
        x_plot = np.linspace(x.min(), x.max(), 100)
        x_plot_scaled = (x_plot - res['x_min']) / (res['x_max'] - res['x_min'])

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(x, y, alpha=0.7, label='观测值')

        # 后验预测
        posterior = res['trace'].posterior.stack(sample=('chain', 'draw'))
        n_samples = 200
        idx = np.random.choice(len(posterior.sample), n_samples, replace=False)
        for i in idx:
            a = posterior['a'][i].item()
            b1 = posterior['b1'][i].item()
            b2 = posterior['b2'][i].item()
            cp = posterior['cp'][i].item()
            y_pred = a + b1 * x_plot_scaled + (b2 - b1) * np.where(x_plot_scaled >= cp, x_plot_scaled - cp, 0)
            ax.plot(x_plot, y_pred, color='gray', alpha=0.1)

        # 变点分布
        cp_original = res['cp_original']
        az.plot_kde(cp_original, ax=ax, plot_kwargs={"color": "red"}, label='变点分布')  # 修复点
        median_cp = np.median(cp_original)
        ax.axvline(median_cp, color='red', linestyle='--', label=f'中位变点: {median_cp:.1f}')

        ax.set_title(f'{title} - {pheno}')
        ax.set_xlabel('lastyear_LOS')
        ax.set_ylabel('物候期')
        ax.legend()
        plt.show()

        # 保存图片
        filename = f"{title}_{pheno}.png".replace(' ', '_').replace('/', '_')
        plt.savefig(f"{output_dir}/{filename}", dpi=300, bbox_inches='tight')
        plt.close()

if __name__ == '__main__':
    freeze_support()  # Windows 必需

    # 读取数据
    grass_mean = pd.read_csv('F:\\站点\\中国地面\\草本数据_每年均值.csv', encoding='gbk')
    wood_mean = pd.read_csv('F:\\站点\\中国地面\\灌本数据_每年均值.csv', encoding='gbk')

    # 数据预处理
    grass_mean = preprocess_data(grass_mean)
    wood_mean = preprocess_data(wood_mean)

    sites_of_interest = ['泰安', '民勤', '哈尔滨', '银川', '牡丹江', '北京', '长春']

    # 过滤数据
    grass_filtered = grass_mean[grass_mean['站点'].isin(sites_of_interest)]
    wood_filtered = wood_mean[wood_mean['站点'].isin(sites_of_interest)]

    # 执行分析
    print("开始分析草本数据...")
    grass_results = analyze_phenology(grass_filtered, '草本数据')
    print("开始分析灌木数据...")
    wood_results = analyze_phenology(wood_filtered, '灌木数据')

    # 生成图形
    print("生成结果图表...")
    plot_results(grass_filtered, grass_results, '草本数据')
    plot_results(wood_filtered, wood_results, '灌木数据')