import csv

input_file = r'F:\站点\中国地面\筛选后的草本数据.csv'
output_file = r'F:\站点\中国地面\筛选后的草本数据2.csv'

# 定义要检查的列名分组
leaf_columns = [
    '叶芽开始膨大期', '叶芽开放期', '开始展叶期',
    '展叶盛期', '叶开始变色期', '叶全部变色期'
]

flower_columns = [
    '花芽开始膨大期', '花芽开放期', '花序或花蕾出现期',
    '开花始期', '开花盛期', '开花末期'
]

fruit_columns = [
    '果实成熟期', '果实脱落开始期', '果实脱落末期'
]

# 创建列索引映射
column_indices = {}

with open(input_file, 'r', newline='', encoding='gbk') as infile:
    reader = csv.reader(infile)
    header = next(reader)
    column_indices = {col: idx for idx, col in enumerate(header)}

def check_increasing(cols, row):
    prev_value = None
    valid = True

    for col in cols:
        if col not in column_indices:
            continue
        cell = row[column_indices[col]].strip()
        if not cell:  # 跳过空单元格
            continue
        try:
            current_value = float(cell)  # 转换为数值
        except ValueError:
            valid = False  # 非数值数据视为无效
            break

        if prev_value is not None and current_value <= prev_value:
            valid = False
            break
        prev_value = current_value  # 更新前一个有效值

    return valid

with open(input_file, 'r', newline='', encoding='gbk') as infile, \
        open(output_file, 'w', newline='', encoding='gbk') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    # 读取并写入标题行
    header = next(reader)
    writer.writerow(header + ['Leaf_Valid', 'Flower_Valid', 'Fruit_Valid'])

    for row in reader:
        leaf_valid = check_increasing(leaf_columns, row)
        flower_valid = check_increasing(flower_columns, row)
        fruit_valid = check_increasing(fruit_columns, row)

        writer.writerow(row + [leaf_valid, flower_valid, fruit_valid])



