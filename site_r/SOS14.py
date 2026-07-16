import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, linregress
from sklearn.metrics import mean_squared_error
import math
import pandas as pd
import numpy as np

# --- 配置 ---
# 读取CSV数据
# 读取CSV数据
df = pd.read_csv('F:\\pythonforR\\sos3\\sossite.csv')

# 定义实际观测列的列表
acture3 = ['Budburst']

# 定义阈值列的前缀列表
threshold_prefixes = ['SoS_doublelogisticthreshold_',
                      'SoS_filterdoublelogisticthreshold_', 'mintomaxdoublelogistic_SoS_threshold_',
                      'SoS_threshold_', 'SoS_filterthreshold_', 'SoS_mintomaxthreshold_',
                      'cubic_SoS_threshold_', 'filtercubic_SoS_threshold_', 'mintomaxcubic_SoS_threshold_']


# 定义方法列表
meth = ['NDVI', 'EVI', 'EVI2','NDPI','NDGI']

# 构建所有可能的阈值列名并筛选出存在的列
all_threshold_columns = [f"{prefix}{method}_{i}" for prefix in threshold_prefixes for method in meth for i in
                          [5, 1, 13, 2, 21, 3]]
print("所有可能的阈值列名:")
print(all_threshold_columns)
existing_threshold_columns = [col for col in all_threshold_columns if col in df.columns]
print("\n实际存在的阈值列名:")
print(existing_threshold_columns)

# 计算总子图数量和批次
num_plots = len(acture3) * len(existing_threshold_columns)
batch_size = 30  # 每批次中的子图数量
total_batches = math.ceil(num_plots / batch_size)
print(f"\n总子图数: {num_plots}")
print(f"每批子图数: {batch_size}")
print(f"总批次数: {total_batches}")

# 设置全局绘图参数 (修改为与目标代码一致)
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 24 # 修改为 24
fig_width_inch = 580 / 25.4  # 宽度 580mm 转换为英寸
# fig_height_inch = len(meth) * 4 # 原始高度计算
fig_height_inch = 6 * 3.5  # 假设每行一个方法，共6行(NDVI,EVI,EVI2,NDPI,NDGI + 标题/标签空间)，每行4英寸
letters = ['a', 'b', 'c', 'd', 'e', 'f']

# --- 主循环 ---
for batch in range(total_batches):
    print(f"\n开始处理第 {batch + 1} 批 / 共 {total_batches} 批...")
    start_index = batch * batch_size
    end_index = min((batch + 1) * batch_size, num_plots)

    # 创建子图网格 (调整 wspace 和 hspace 可能需要微调以匹配目标样式)
    fig, axes = plt.subplots(nrows=len(meth), ncols=6, figsize=(fig_width_inch, fig_height_inch),
                             constrained_layout=False, gridspec_kw={'wspace': 0.3, 'hspace': 0.4})
    axes_flat = axes.flatten()

    plot_counter_in_batch = 0  # 用于追踪当前批次中的子图索引

    for global_plot_index in range(start_index, end_index):
        # 确定当前子图对应的 stage 和 threshold 列名
        # 注意: acture3 只有一个元素 'EOS'，所以 stage 总是 'EOS'
        stage_idx = global_plot_index // len(existing_threshold_columns)
        threshold_idx = global_plot_index % len(existing_threshold_columns)

        if stage_idx >= len(acture3):
            print(f"警告: global_plot_index {global_plot_index} 超出 acture3 范围，跳过。")
            continue

        stage = acture3[stage_idx]
        threshold = existing_threshold_columns[threshold_idx]

        # --- 数据清洗关键步骤 ---
        # 1. 移除原始数据中的 NaN
        valid_data_raw = df.dropna(subset=[stage, threshold])

        # 2. 尝试将选定的列转换为数值类型，无法转换的设为 NaN
        #    这一步处理了像 "NaN", "", "null" 这样的字符串空值
        valid_data_numeric = valid_data_raw.copy()
        valid_data_numeric[stage] = pd.to_numeric(valid_data_numeric[stage], errors='coerce')
        valid_data_numeric[threshold] = pd.to_numeric(valid_data_numeric[threshold], errors='coerce')

        # 3. 再次移除因转换产生的 NaN
        valid_data_final = valid_data_numeric.dropna(subset=[stage, threshold])

        # 4. 检查是否有足够的数据点 (至少2个点才能做线性回归)
        if len(valid_data_final) < 2:
            print(f"  子图 ({stage} vs {threshold}): 数据点不足 ({len(valid_data_final)})，跳过绘图。")
            # 隐藏这个子图
            fig.delaxes(axes_flat[plot_counter_in_batch])
            plot_counter_in_batch += 1
            continue

        # --- 绘图 ---
        ax = axes_flat[plot_counter_in_batch]

        # 绘制散点图 (调整点大小 s)
        sns.scatterplot(x=valid_data_final[stage], y=valid_data_final[threshold], ax=ax, color='black', alpha=0.6,
                        s=20)  # 增大点大小

        # 添加1:1线 (修改为实线 k-)
        lims = [0, 200]
        ax.plot(lims, lims, 'k-', alpha=0.75, zorder=1, linewidth=1)  # 实线

        # 设置坐标轴范围和刻度 (调整刻度字体大小)
        ax.set_xlim(lims)
        ax.set_ylim(lims)
        # 设置x轴和y轴的刻度间隔为50，并指定字体大小
        ax.set_xticks(np.arange(0, 201, 50))
        ax.set_yticks(np.arange(0, 201, 50))
        ax.tick_params(axis='both', which='major', labelsize=24)  # 修改为 24

        # --- 计算统计量 ---
        try:
            # 线性回归 (使用 .to_numpy() 以匹配目标代码风格，虽然不是必须)
            x_vals_np = valid_data_final[stage].to_numpy()
            y_vals_np = valid_data_final[threshold].to_numpy()
            slope, intercept, r_value, p_value, std_err = linregress(x_vals_np, y_vals_np)

            # 绘制拟合线
            fit_line = slope * x_vals_np + intercept
            # 使用不同颜色和线型区分1:1线 (保持红色实线)
            ax.plot(x_vals_np, fit_line, 'r-', alpha=0.8, linewidth=1, label=f'Fit Line')

            # 计算相关系数 (Pearsonr) - linregress 已经提供了 r_value
            # r, _ = pearsonr(valid_data_final[stage], valid_data_final[threshold])
            r = r_value

            # 计算 RMSE (使用 .to_numpy())
            rmse = np.sqrt(mean_squared_error(x_vals_np, y_vals_np))

            # 在图上添加文本信息 (调整字体大小和位置)
            # R 和 RMSE
            ax.text(0.95, 0.1, f'R: {r:.2f}\nRMSE: {rmse:.2f}', # 调整 y 位置
                    transform=ax.transAxes,
                    horizontalalignment='right',
                    verticalalignment='bottom',
                    fontsize=24, # 修改为 24
                    bbox=dict(facecolor='white', alpha=0.5, edgecolor='none', pad=0.2)) # 调整 alpha

            # 子图标签 (e.g., a1, a2, ...) (调整字体大小和位置)
            # 确定行列索引用于标签
            row_in_grid = plot_counter_in_batch // 6
            col_in_grid = plot_counter_in_batch % 6
            if row_in_grid < len(letters):
                letter = letters[row_in_grid]
            else:
                letter = 'z'  # 防止越界
            number = col_in_grid + 1
            label = f'({letter}{number})'
            ax.text(0.05, 0.95, label, # 位置基本一致
                    transform=ax.transAxes,
                    verticalalignment='top',
                    horizontalalignment='left',
                    fontsize=24, # 修改为 24
                    weight='bold',
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0.2)) # 调整 alpha

        except Exception as e:
            print(f"  子图 ({stage} vs {threshold}): 计算或绘图时出错: {e}")
            ax.text(0.5, 0.5, 'Calculation Error',
                    transform=ax.transAxes,
                    horizontalalignment='center',
                    verticalalignment='center',
                    fontsize=24, # 修改为 24
                    color='red')
            # 仍然保留子图标签 (调整字体大小)
            row_in_grid = plot_counter_in_batch // 6
            col_in_grid = plot_counter_in_batch % 6
            if row_in_grid < len(letters):
                letter = letters[row_in_grid]
            else:
                letter = 'z'
            number = col_in_grid + 1
            label = f'({letter}{number})'
            ax.text(0.05, 0.95, label,
                    transform=ax.transAxes,
                    verticalalignment='top',
                    horizontalalignment='left',
                    fontsize=24, # 修改为 24
                    weight='bold',
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0.2))

        # 移除顶部和右侧的脊柱
        # ax.spines['top'].set_visible(False)
        #  ax.spines['right'].set_visible(False)
        ax.set_xlabel('')
        ax.set_ylabel('')
        plot_counter_in_batch += 1

    # --- 处理当前批次中未使用的子图 ---
    for j in range(plot_counter_in_batch, len(axes_flat)):
        fig.delaxes(axes_flat[j])

    # --- 添加大图标签 (调整字体大小和位置) ---
    fig.text(0.5, 0.06, 'Bud burst (DOY)', ha='center', fontsize=30, weight='bold') # 调整 y 和 fontsize
    fig.text(0.04, 0.5, 'MOD43A4 SOS (DOY)', va='center', rotation='vertical', fontsize=30, weight='bold') # 调整 x, y 和 fontsize
    fig.text(0.5, 0.92, 'Threshold', ha='center', fontsize=30, weight='bold')

    # 添加 Y 轴方法标签 (左侧) (调整字体大小和位置)
    for idx, method in enumerate(meth):
        if idx < axes.shape[0]:  # 确保不越界
            # 调整 y 坐标以匹配子图行 (需要根据实际效果微调)
            y_coord = 0.8 - (idx * 0.16) # 调整起始点和步长
            fig.text(0.07, y_coord, method, va='center', rotation='vertical', fontsize=24, weight='bold') # 调整 fontsize

    # 添加大图的Y轴坐标（基于meth）
    for idx, method in enumerate(meth):
        # 调整Y轴坐标，使标签更加紧凑
        fig.text(0.07, 0.8 - (idx * 0.16), method, va='center', rotation='vertical', fontsize=24, weight='bold')
    # 添加大图的X轴坐标（固定位置）
    # 添加大图的X轴坐标（固定位置）
    x_ticks_positions = [0.3,0.25,0.2,0.15,0.1,0.05]
    for idx, pos in enumerate(x_ticks_positions):
        fig.text(0.85 - (idx * 0.135), 0.9, f"{pos:.0%}", ha='center', fontsize=24, weight='bold')

    # --- 保存图像 ---
    output_filename = f'F:\\pythonforR\\sos3\\SOS_scatter_plots_withoutsjm_batch{batch + 1}.png'
    plt.savefig(output_filename, dpi=600, bbox_inches='tight')
    print(f"  已保存第 {batch + 1} 批图像至: {output_filename}")
    plt.clf()  # 清除当前 figure 的所有内容
    plt.close(fig)  # 关闭 figure 窗口，释放内存

print("\n所有批次处理完成。")




