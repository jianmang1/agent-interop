import os
import pandas as pd
from openai import OpenAI
import time
from datetime import datetime, timedelta

# 计算4小时后的时间
target_time = datetime.now() + timedelta(hours=6)
print(f"程序将在 {target_time.strftime('%Y-%m-%d %H:%M:%S')} 开始运行。")

# 暂停程序直到目标时间
while datetime.now() < target_time:
    remaining_time = (target_time - datetime.now()).total_seconds()
    print(f"距离程序运行还有 {remaining_time:.0f} 秒...", end="\r")
    time.sleep(1)  # 每秒检查一次

print("\n开始运行程序...")
# 配置信息
input_csv = r"F:\站点\中国地面\中国地面观测物候数据\种.csv"
output_csv = r"F:\站点\中国地面\中国地面观测物候数据\种_deepseek.csv"
api_key = "sk-b99882fe8dec406b8da0449249774814"  # 替换为DeepSeek API Key

# 读取CSV文件
try:
    df = pd.read_csv(input_csv, encoding='gbk')
except UnicodeDecodeError:
    df = pd.read_csv(input_csv, encoding='utf-8')

# 初始化OpenAI客户端（DeepSeek版本）
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",  # 修改base_url
)

def get_plant_type(species, station):
    try:
        # 构建消息内容，包含站点名称和物种名称
        message_content = f"站点'{station}'的'{species}'是灌木、乔木、草本还是藤本，仅回答灌、乔、藤或草"
        completion = client.chat.completions.create(
            model="deepseek-reasoner",  # 修改模型名称
            messages=[
                {'role': 'user', 'content': message_content}
            ],
            temperature=0.1
        )
        result = completion.choices[0].message.content.strip()
        # 加强结果校验
        return result if result in ['灌', '乔', '藤', '草'] else f"未知({result})"
    except Exception as e:
        print(f"处理 {species}（站点：{station}）时发生错误：{str(e)}")
        return "API错误"

def process_species(row):
    """处理单个物种并打印结果"""
    species = row['植物种名']
    station = row['站点']  # 假设站点列名为'站点'
    time.sleep(1)  # 保持1秒间隔（DeepSeek免费版限速）
    result = get_plant_type(species, station)
    print(f"{station}: {species}: {result}")  # 实时打印结果
    return result

# 应用处理函数
df['类型'] = df.apply(process_species, axis=1)

# 保存结果
df.to_csv(output_csv, index=False, encoding='utf-8-sig')
print(f"\n处理完成，结果已保存至 {output_csv}")