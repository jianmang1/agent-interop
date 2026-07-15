import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# 1. 读取数据 - 尝试不同的编码方式
file_path = r'F:\站点\中国地面\年变化_analysis_results.csv'

try:
    # 首先尝试GBK编码（最常见于中文Windows系统）
    df_raw = pd.read_csv(file_path, encoding='gbk')
    print("成功使用GBK编码读取文件")
except UnicodeDecodeError:
    try:
        # 如果GBK失败，尝试GB2312
        df_raw = pd.read_csv(file_path, encoding='gb2312')
        print("成功使用GB2312编码读取文件")
    except UnicodeDecodeError:
        try:
            # 最后尝试latin-1编码（万能编码，但可能导致乱码）
            df_raw = pd.read_csv(file_path, encoding='latin-1')
            print("成功使用latin-1编码读取文件，但可能出现乱码")
        except Exception as e:
            print(f"无法读取文件: {e}")
            exit()

print("原始列名:")
print(df_raw.columns.tolist())

# 获取列名列表，从第二列开始（跳过Unnamed: 0）
actual_cols = df_raw.columns.tolist()[1:]

# 定义目标物候期阶段
target_phenology_stages = [
    '开始展叶期', '展叶盛期', '花序或花蕾出现期', '开花始期', '开花盛期',
    '开花末期', '果实成熟期', '果实脱落开始期', '果实脱落末期',
    '叶开始变色期', '叶全部变色期'
]

# 初始化一个空的DataFrame来存储清洗后的数据
clean_data = []

# 按每4列一组处理 (CLASS, Year, Trend, Change)
# 实际列索引从1开始，所以每组为 (1,2,3,4), (5,6,7,8), (9,10,11,12), ...
for i in range(0, len(actual_cols), 4):
    if i + 3 >= len(actual_cols):
        break

    # 获取实际的列位置（相对于原始df_raw）
    actual_idx = i + 1  # 因为跳过了Unnamed: 0列，所以加1

    class_col = df_raw.columns[actual_idx]
    year_col = df_raw.columns[actual_idx + 1]
    trend_col = df_raw.columns[actual_idx + 2]
    change_col = df_raw.columns[actual_idx + 3]

    # 提取当前组的数据
    temp_df = df_raw.iloc[:, [actual_idx, actual_idx + 1, actual_idx + 2, actual_idx + 3]].copy()
    temp_df.columns = ['CLASS', 'Year', 'Trend_Value', 'Change_Value']

    # 确定当前组对应的物候期阶段
    # 从列名中提取物候期名称 (例如从 "开始展叶期_Trend" 提取 "开始展叶期")
    stage_name = trend_col.replace('_Trend', '')
    temp_df['Phenology_Stage'] = stage_name

    clean_data.append(temp_df)

# 合并所有组
if clean_data:
    df_clean = pd.concat(clean_data, ignore_index=True)

    # 转换年份和趋势值为数值
    df_clean['Year'] = pd.to_numeric(df_clean['Year'], errors='coerce')
    df_clean['Trend_Value'] = pd.to_numeric(df_clean['Trend_Value'], errors='coerce')
    df_clean['Change_Value'] = pd.to_numeric(df_clean['Change_Value'], errors='coerce')

    # 不进行完全的数据清理，但移除关键字段的缺失值
    df_valid = df_clean.dropna(subset=['CLASS', 'Year', 'Trend_Value'])

    # 获取实际的类别名称
    unique_classes = df_valid['CLASS'].unique()
    print(f"数据中发现的类别: {unique_classes}")

    # 过滤出'草本'和'灌木'类别，如果不存在则使用现有类别
    target_classes = ['草本', '灌木']

    # 检查哪些目标类别存在于数据中
    existing_target_classes = [cls for cls in target_classes if cls in unique_classes]

    if not existing_target_classes:
        # 如果目标类别不存在，使用数据中存在的类别作为替代
        print("目标类别'草本'和'灌木'不存在，使用现有类别进行分析")
        existing_target_classes = unique_classes[:2] if len(unique_classes) >= 2 else unique_classes

    df_filtered = df_valid[df_valid['CLASS'].isin(existing_target_classes)]

    # 显示过滤后的类别信息
    filtered_classes = df_filtered['CLASS'].unique()
    print(f"过滤后的类别: {filtered_classes}")

    # 显示每个类别的数据量
    class_counts = df_filtered['CLASS'].value_counts()
    print("过滤后各类别数据量:")
    print(class_counts)

    # 创建一个透视表，将不同物候期作为列
    pivot_data = []

    for cls in filtered_classes:
        df_group = df_filtered[df_filtered['CLASS'] == cls]

        row_data = {'CLASS': cls}

        for stage in target_phenology_stages:
            df_stage = df_group[df_group['Phenology_Stage'] == stage]

            if len(df_stage) > 0:
                # 计算趋势值的均值，去除NaN后再计算
                valid_trend_values = df_stage['Trend_Value'].dropna()
                if len(valid_trend_values) > 0:
                    mean_trend = valid_trend_values.mean()
                else:
                    mean_trend = np.nan

                # 计算 _Change 值应为 _Trend 与 Year（x轴）的拟合斜率
                # 过滤掉包含NaN的行
                df_stage_clean = df_stage.dropna(subset=['Year', 'Trend_Value'])

                if len(df_stage_clean) >= 2:
                    X = df_stage_clean['Year'].values.reshape(-1, 1)
                    y = df_stage_clean['Trend_Value'].values

                    model = LinearRegression()
                    model.fit(X, y)
                    slope = model.coef_[0]  # 这就是 Change 值
                else:
                    slope = np.nan

                # 添加到行数据中
                row_data[f'{stage}_Trend'] = mean_trend
                row_data[f'{stage}_Change'] = slope  # Change 是 Trend 与 Year 的拟合斜率
            else:
                # 如果没有数据，则填充NaN
                row_data[f'{stage}_Trend'] = np.nan
                row_data[f'{stage}_Change'] = np.nan

        pivot_data.append(row_data)

    # 创建最终的结果DataFrame
    if pivot_data:  # 确保有数据才继续
        results_df = pd.DataFrame(pivot_data)

        # 重新排列列的顺序，按照Trend和Change交替的方式
        ordered_columns = ['CLASS']
        for stage in target_phenology_stages:
            ordered_columns.extend([f'{stage}_Trend', f'{stage}_Change'])

        results_df = results_df[ordered_columns]

        # 格式化输出
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.float_format', lambda x: '%.4f' % x)

        print("\n统计结果 (按类别和物候期):")
        print(results_df.to_string(index=False))

        # 保存为CSV文件
        csv_output_file = r'F:\站点\中国地面\phenology_stats_result.csv'
        results_df.to_csv(csv_output_file, index=False, encoding='utf-8-sig')
        print(f"\n结果已保存至: {csv_output_file}")

        # 保存为XLSX文件
        xlsx_output_file = r'F:\站点\中国地面\phenology_stats_result.xlsx'
        results_df.to_excel(xlsx_output_file, index=False, engine='openpyxl')
        print(f"\n结果已保存至: {xlsx_output_file}")

        # 打印列名用于验证
        print("\n生成的列名:")
        print(list(results_df.columns))
    else:
        print("没有符合条件的数据可以处理")

else:
    print("未能成功解析数据，请检查文件格式。")
