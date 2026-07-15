import pandas as pd

# 请将 'your_file.xlsx' 替换为你实际的 Excel 文件路径
excel_file_path = r'F:\站点\中国地面\中国地面观测物候数据\2014年观测报表\merged_grass_data.xlsx'

# 读取 Excel 文件
data = pd.read_excel(excel_file_path)

# 确定第 F 列到第 W 列的索引范围
start_col_index = 5  # F 列索引为 5
end_col_index = 21  # W 列索引为 22

# 遍历这些列
for col_index in range(start_col_index, end_col_index + 1):
    col_name = data.columns[col_index]
    try:
        # 提取月份和日期
        def extract_date(date_str):
            if isinstance(date_str, str):
                # 替换全角减号为半角减号
                date_str = date_str.replace('－', '-')
                if '.' in date_str:
                    parts = date_str.split('.')
                    if len(parts) == 3:  # 处理 2014.2.20 格式
                        year, month, day = parts
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif len(parts) == 2:  # 处理 2.08 格式
                        month, day = parts
                        return f"{month.zfill(2)}-{day.zfill(2)}"
                elif '月' in date_str:
                    parts = date_str.split('月')
                    month_part = parts[0]
                    day_part = parts[1].split('日')[0].strip()  # 处理日和其他字符
                    return f"{month_part.zfill(2)}-{day_part.zfill(2)}"
                elif '-' in date_str:
                    parts = date_str.split('-')
                    if len(parts) == 3:  # 处理带年份的格式如 2014-02-20
                        year, month, day = parts
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif len(parts) == 2:  # 处理 4-7 或 1-22 格式
                        month, day = parts
                        return f"{month.zfill(2)}-{day.zfill(2)}"
            return date_str


        data[col_name] = data[col_name].astype(str).apply(extract_date)

        # 尝试以不同格式解析日期
        formats = [
            ('%m-%d', '%m-%d'),  # 处理 01-22
            ('%Y-%m-%d', '%Y-%m-%d'),  # 处理 2014-01-22
            ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S'),  # 处理带时间的格式
            ('%m/%d', '%m/%d')  # 处理 11/11 格式
        ]

        series_list = []
        for fmt_name, fmt in formats:
            s = pd.to_datetime(data[col_name], format=fmt, errors='coerce')
            series_list.append(s)

        # 合并所有解析结果
        combined_series = series_list[0]
        for s in series_list[1:]:
            combined_series = combined_series.combine_first(s)

        # 转换为该年的第 DOY 天
        doy_series = combined_series.dt.dayofyear
        data[col_name] = doy_series
    except Exception as e:
        print(f"Error processing column {col_name}: {e}")

# 保存修改后的数据到新的 Excel 文件
output_file_path = r'F:\站点\中国地面\中国地面观测物候数据\2014年观测报表\merged_grass_data(2).xlsx'
data.to_excel(output_file_path, index=False)