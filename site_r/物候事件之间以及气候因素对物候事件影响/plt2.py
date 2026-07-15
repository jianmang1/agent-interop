import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import matplotlib.font_manager as fm

# 设置中文字体
font_path = 'C:/Windows/Fonts/simhei.ttf'
zh_font = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = zh_font.get_name()
plt.rcParams['axes.unicode_minus'] = False


# 加载并预处理数据
def load_data(filepath):
    df = pd.read_csv(
        filepath,
        encoding='GBK',
        usecols=['phase_early', 'phase_late', 'partial_corr_ph',
                 'partial_corr_temp', 'partial_corr_precip', 'rsquared']
    ).replace([np.inf, -np.inf], np.nan)
    return df.dropna()


# 数据聚合函数
def aggregate_data(df):
    # 对相同phase组合取均值，R²转换为百分比
    grouped = df.groupby(['phase_early', 'phase_late'], as_index=False).agg({
        'partial_corr_ph': lambda x: np.nanmean(x),
        'partial_corr_temp': lambda x: np.nanmean(x),
        'partial_corr_precip': lambda x: np.nanmean(x),
        'rsquared': lambda x: min(100, int(round(np.nanmean(x) * 100, 0)))
    })
    return grouped


# 矩阵构建函数
def build_matrix(phases, grouped_df):
    phase_idx = {phase: i for i, phase in enumerate(phases)}
    n = len(phases)

    matrices = {
        'ph': np.full((n, n), np.nan),
        'temp': np.full((n, n), np.nan),
        'precip': np.full((n, n), np.nan),
        'rsq': np.full((n, n), np.nan)
    }

    for _, row in grouped_df.iterrows():
        try:
            i = phase_idx[row['phase_early']]
            j = phase_idx[row['phase_late']]
            if i >= j: continue

            matrices['ph'][i, j] = row['partial_corr_ph']
            matrices['temp'][i, j] = row['partial_corr_temp']
            matrices['precip'][i, j] = row['partial_corr_precip']
            matrices['rsq'][i, j] = row['rsquared']
        except KeyError:
            continue

    return matrices


# 可视化函数
def plot_matrix(phases, matrices):
    fig, ax = plt.subplots(figsize=(24, 20))
    ax.set_aspect('equal')
    max_radius = 0.4  # 最大圆环半径

    # 绘制网格
    for i in range(len(phases) + 1):
        ax.axhline(i - 0.5, color='lightgray', linestyle=':', lw=0.5)
        ax.axvline(i - 0.5, color='lightgray', linestyle=':', lw=0.5)

    # 绘制各效应
    for i in range(len(phases)):
        for j in range(len(phases)):
            if i >= j: continue

            x, y = i, j
            rsq = matrices['rsq'][i, j]
            ph = matrices['ph'][i, j]
            temp = matrices['temp'][i, j]
            precip = matrices['precip'][i, j]

            # 物候效应
            if not np.isnan(ph):
                linestyle = '-' if ph > 0 else '--'
                circle = Circle((x, y), radius=np.abs(ph) * max_radius,
                                edgecolor='#2ca02c', facecolor='none',
                                linewidth=1.5, linestyle=linestyle)
                ax.add_patch(circle)

            # 温度效应
            if not np.isnan(temp):
                linestyle = '-' if temp > 0 else '--'
                circle = Circle((x, y), radius=np.abs(temp) * max_radius,
                                edgecolor='#d62728', facecolor='none',
                                linewidth=1.2, linestyle=linestyle)
                ax.add_patch(circle)

            # 降水效应
            if not np.isnan(precip):
                linestyle = '-' if precip > 0 else '--'
                circle = Circle((x, y), radius=np.abs(precip) * max_radius,
                                edgecolor='#1f77b4', facecolor='none',
                                linewidth=1.2, linestyle=linestyle)
                ax.add_patch(circle)

            # R²标注
            if not np.isnan(rsq):
                ax.text(x, y, f"{int(rsq)}%", ha='center', va='center',
                        fontsize=8, color='black')

    # 坐标轴设置
    ax.set(xticks=np.arange(len(phases)),
           yticks=np.arange(len(phases)),
           xticklabels=phases,
           yticklabels=phases,
           xlim=(-0.5, len(phases) - 0.5),
           ylim=(-0.5, len(phases) - 0.5))

    plt.xticks(rotation=55, ha='right', rotation_mode='anchor')
    plt.yticks()

    # 图例
    legend_elements = [
        plt.Line2D([0], [0], color='#2ca02c', lw=2, label='物候效应'),
        plt.Line2D([0], [0], color='#d62728', lw=2, label='温度效应'),
        plt.Line2D([0], [0], color='#1f77b4', lw=2, label='降水效应'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
                   markersize=10, label=r'数值表示$R^{2}$ (%)')
    ]
    ax.legend(handles=legend_elements, loc='upper right', frameon=False)

    plt.tight_layout()
    return fig


def export_matrices_to_csv(phases, matrices, filename_prefix="phenology_matrices_wd"):
    """将矩阵数据导出到CSV文件"""
    data_rows = []

    for i in range(len(phases)):
        for j in range(len(phases)):
            if i < j:  # 只考虑上三角矩阵
                data_rows.append({
                    'phase_early': phases[i],
                    'phase_late': phases[j],
                    'partial_corr_ph': matrices['ph'][i, j],
                    'partial_corr_temp': matrices['temp'][i, j],
                    'partial_corr_precip': matrices['precip'][i, j],
                    'rsquared': matrices['rsq'][i, j]
                })

    # 创建DataFrame并保存为CSV
    export_df = pd.DataFrame(data_rows)

    # 删除全为NaN的行
    export_df = export_df.dropna(how='all', subset=['partial_corr_ph', 'partial_corr_temp',
                                                    'partial_corr_precip', 'rsquared'])

    csv_filename = f"{filename_prefix}_export.csv"
    export_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
    print(f"数据已导出到 {csv_filename}")

    return export_df


def export_matrices_as_excel(phases, matrices, filename="phenology_matrices_wd_detailed.xlsx"):
    """将各个矩阵分别导出到Excel的不同工作表中"""
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # 导出汇总数据
        data_rows = []
        for i in range(len(phases)):
            for j in range(len(phases)):
                if i < j:  # 只考虑上三角矩阵
                    data_rows.append({
                        'phase_early': phases[i],
                        'phase_late': phases[j],
                        'partial_corr_ph': matrices['ph'][i, j],
                        'partial_corr_temp': matrices['temp'][i, j],
                        'partial_corr_precip': matrices['precip'][i, j],
                        'rsquared': matrices['rsq'][i, j]
                    })

        summary_df = pd.DataFrame(data_rows)
        summary_df = summary_df.dropna(how='all', subset=['partial_corr_ph', 'partial_corr_temp',
                                                          'partial_corr_precip', 'rsquared'])
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

        # 创建矩阵DataFrame并导出
        matrix_df = pd.DataFrame(index=phases, columns=phases)

        for key, matrix in matrices.items():
            matrix_df.iloc[:, :] = np.nan  # 清空DataFrame
            for i in range(len(phases)):
                for j in range(len(phases)):
                    if i < j:  # 只填充上三角
                        matrix_df.iloc[i, j] = matrix[i, j]

            # 将NaN替换为空字符串以便更好地显示
            matrix_df_display = matrix_df.copy()
            matrix_df_display = matrix_df_display.fillna('')

            matrix_df_display.to_excel(writer, sheet_name=key.upper())

    print(f"详细数据已导出到 {filename}")


def print_matrices_values(phases, matrices):
    """打印矩阵中的所有有效值"""
    print("=" * 80)
    print("矩阵中的有效值统计")
    print("=" * 80)

    for key in matrices:
        print(f"\n{key.upper()} 矩阵的有效值:")
        print("-" * 40)

        matrix = matrices[key]
        count = 0

        for i in range(len(phases)):
            for j in range(len(phases)):
                if i < j and not np.isnan(matrix[i, j]):
                    count += 1
                    print(f"  {phases[i]} -> {phases[j]}: {matrix[i, j]:.4f}")

        print(f"  总计有效值: {count}")

    # 打印一些统计信息
    print("\n\n统计摘要:")
    print("-" * 40)
    for key in matrices:
        matrix = matrices[key]
        values = matrix[~np.isnan(matrix)]
        if len(values) > 0:
            print(f"{key.upper():<6} - 有效值数量: {len(values)}, "
                  f"最小值: {values.min():.4f}, 最大值: {values.max():.4f}, "
                  f"平均值: {values.mean():.4f}")


# 主流程
if __name__ == "__main__":
    # 数据加载与处理
    df = load_data('F:/站点/中国地面/clime/clim_carryover_effect_wd.csv')

    # 定义阶段顺序
    predefined_phases = [
        '叶芽开始膨大期', '叶芽开放期', '花芽开始膨大期',
        '花芽开放期', '开始展叶期', '展叶盛期',
        '花序或花蕾出现期', '开花始期', '开花盛期',
        '开花末期', '果实成熟期', '果实脱落开始期',
        '果实脱落末期', '叶开始变色期', '叶全部变色期',
        '开始落叶期', '落叶末期'
    ]
    valid_phases = [p for p in predefined_phases if p in set(df['phase_early']).union(df['phase_late'])]

    # 数据聚合
    grouped_df = aggregate_data(df)

    print("数据聚合结果:")
    print(grouped_df.head(10))  # 打印前10行
    print(f"\n总共有 {len(grouped_df)} 条记录")

    # 构建矩阵
    matrices = build_matrix(valid_phases, grouped_df)

    # 打印矩阵中的值
    print_matrices_values(valid_phases, matrices)

    # 导出数据到CSV文件
    export_df = export_matrices_to_csv(valid_phases, matrices, "phenology_effects_wd_export")

    # 导出详细数据到Excel文件
    export_matrices_as_excel(valid_phases, matrices, "E:\Desktop\灌草物候\phenology_effects_wd_detailed.xlsx")

    # 显示导出的数据预览
    print("\n导出数据预览 (前10行):")
    print(export_df.head(10))

    # 可视化
    fig = plot_matrix(valid_phases, matrices)
    fig.savefig('wd_aggregated_phenology_matrix.png', dpi=600, bbox_inches='tight')
    plt.show()

