import os
import pandas as pd
from openai import OpenAI
import time

# 配置信息
input_csv = r"F:\站点\中国地面\中国地面观测物候数据\种.csv"
output_csv = "F:\站点\中国地面\中国地面观测物候数据\\ai植物分类结果.csv"
api_key = "sk-c8a5c441ad074253b2d2e566259c0165"  # 直接使用你的API Key

# 读取CSV文件
try:
    df = pd.read_csv(input_csv, encoding='gbk')  # 保持原始编码
except UnicodeDecodeError:
    df = pd.read_csv(input_csv, encoding='utf-8')

# 初始化OpenAI客户端
client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def get_plant_type(species):
    try:
        completion = client.chat.completions.create(
            model="qwen-turbo",
            messages=[
                {'role': 'user', 'content': f"'{species}'是灌木、乔木还是草本，仅回答灌或乔或草"}
            ],
            temperature=0.1
        )
        result = completion.choices[0].message.content.strip()
        return result if result in ['灌', '乔', '草'] else "未知"
    except Exception as e:
        print(f"处理 {species} 时发生错误：{str(e)}")
        return "未知"

def process_species(species):
    """处理单个物种并打印结果"""
    time.sleep(1)  # 保持1秒间隔
    result = get_plant_type(species)
    # 实时打印处理结果
    print(f"{species}: {result}")
    return result

# 应用处理函数
df['类型'] = df['植物种名'].apply(process_species)

# 保存结果
df.to_csv(output_csv, index=False, encoding='utf-8-sig')
print(f"\n处理完成，结果已保存至 {output_csv}")