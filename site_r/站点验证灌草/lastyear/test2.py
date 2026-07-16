import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pymc as pm
import arviz as az
from sklearn.preprocessing import MinMaxScaler
from scipy.stats import t, gaussian_kde
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
    scaler = MinMaxScaler()
    x_scaled = scaler.fit_transform(x.values.reshape(-1, 1)).flatten()
    return x_scaled, scaler


# 定义分析函数
def fit_change_point_model(data, pheno):
    try:
        df = data[['lastyear_LOS', pheno]].dropna()
        if len(df) < 10:
            print(f"样本不足，跳过 {pheno}")
            return None

        # 确保 x 和 y 是 Pandas Series
        x = pd.Series(df['lastyear_LOS'].values, name='lastyear_LOS')
        y = pd.Series(df[pheno].values, name=pheno)

        # 检查 x 和 y 的分布
        print(f"{pheno} 数据分布：")
        print("x (lastyear_LOS):", x.describe())
        print("y (物候期):", y.describe())

        # 标准化年份
        x_scaled, x_scaler = standardize_data(x)
        print(f"{pheno} 标准化后 x 范围：{x_scaled.min()} 到 {x_scaled.max()}")

        with pm.Model() as model:
            # 设置先验分布
            a = pm.StudentT('a', nu=3, mu=np.mean(y), sigma=np.std(y))  # 截距
            b1 = pm.StudentT('b1', nu=3, mu=0, sigma=np.std(y))  # 斜率1
            b2 = pm.StudentT('b2', nu=3, mu=0, sigma=np.std(y))  # 斜率2
            cp = pm.Uniform('cp', lower=x_scaled.min(), upper=x_scaled.max())  # 使用均匀分布
            sigma = pm.HalfStudentT('sigma', nu=3, sigma=np.std(y))  # 噪声

            # 分段回归模型
            y_pred = a + b1 * x_scaled + (b2 - b1) * pm.math.switch(x_scaled >= cp, x_scaled - cp, 0)

            # 确保y_pred不会出现极端值
            y_pred = pm.math.clip(y_pred, y.min() - 10, y.max() + 10)

            # 定义观测模型
            pm.Normal('obs', mu=y_pred, sigma=sigma, observed=y)

            # 手动指定初始值
            initvals = {
                'a': np.mean(y),
                'b1': 0,
                'b2': 0,
                'cp': (x_scaled.min() + x_scaled.max()) / 2,
                'sigma': np.std(y)
            }

            # 采样设置
            trace = pm.sample(
                draws=4000,
                tune=4000,
                chains=4,
                cores=1,  # Windows 下设为 1
                target_accept=0.95,
                return_inferencedata=True,
                initvals=initvals
            )
        return trace, x_scaler, x.min(), x.max()
    except Exception as e:
        print(f'Error in {pheno}: {str(e)}')
        return None


def analyze_phenology(data, title):
    results = {}
    pheno_columns = ['开始展叶期']  # 仅测试一个变量

    for pheno in pheno_columns:
        print(f'Analyzing {pheno}...')
        result = fit_change_point_model(data, pheno)
        if result is not None:
            trace, x_scaler, x_min, x_max = result
            cp_samples = trace.posterior['cp'].values.flatten()
            cp_original = x_scaler.inverse_transform(cp_samples.reshape(-1, 1)).flatten()

            # 检查 cp_original 的分布特性
            print(f"{pheno} 变点位置分布统计：")
            print(pd.Series(cp_original).describe())

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

        # 使用 ArviZ 绘制 KDE 曲线
        az.plot_kde(
            cp_original, ax=ax,
            plot_kwargs={"color": "red", "label": "变点分布"}, bw=0.05  # 调整带宽
        )

        # 中位数变点位置
        median_cp = np.median(cp_original)
        q_low, q_high = np.percentile(cp_original, [5, 95])
        ax.axvline(median_cp, color='red', linestyle='--', label=f'中位变点: {median_cp:.1f}')
        ax.axvspan(q_low, q_high, color='red', alpha=0.2, label='90% 置信区间')

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
    wood_mean = pd.read_csv('F:\\站点\\中国地面\\灌本数据_每年均值.csv', encoding='gbk')

    # 数据预处理
    wood_mean = preprocess_data(wood_mean)

    sites_of_interest = ['佳木斯', '嫩江', '德都', '牡丹江', '北京']

    # 过滤数据
    wood_filtered = wood_mean[wood_mean['站点'].isin(sites_of_interest)]

    # 执行分析
    print("开始分析灌木数据...")
    wood_results = analyze_phenology(wood_filtered, '灌木数据')

    # 生成图形
    print("生成结果图表...")
    plot_results(wood_filtered, wood_results, '灌木数据')