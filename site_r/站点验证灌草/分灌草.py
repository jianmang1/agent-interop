import requests
from urllib.parse import quote
from lxml import etree
import pandas as pd
import time
import os

# 文件路径验证
csv_path = r"F:\站点\中国地面\1963-2012.csv"
if not os.path.exists(csv_path):
    raise FileNotFoundError("CSV文件未找到，请检查路径是否正确")

# 读取CSV文件
try:
    df = pd.read_csv(csv_path, encoding='gbk')  # 尝试常见中文编码
except UnicodeDecodeError:
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except Exception as e:
        raise Exception(f"无法读取CSV文件，请检查编码格式: {str(e)}")

if '植物种名' not in df.columns:
    raise ValueError("CSV文件中缺少'植物种名'列")

# 配置请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://db.kib.ac.cn/CNFlora/'
}


# 爬取函数
def crawl_plant_info(species_name):
    try:
        # 编码物种名
        encoded_name = quote(species_name)
        search_url = f"https://db.kib.ac.cn/CNFlora/SearchEngine.aspx?q={encoded_name}"

        # 获取搜索页面
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        # 解析搜索结果
        html = etree.HTML(response.text)

        # 修正XPath：移除可能不存在的tbody
        detail_path = html.xpath('//*[@id="ContentPlaceHolder1_pnl_result"]/table/tr[2]/td[5]/a/@href')

        if not detail_path:
            print(f"{species_name}: 未找到匹配结果")
            return None

        # 构建详情页URL
        detail_url = f"https://db.kib.ac.cn/CNFlora/{detail_path[0]}"

        # 获取详情页
        detail_response = requests.get(detail_url, headers=headers, timeout=10)
        detail_response.raise_for_status()

        # 解析详情内容
        detail_html = etree.HTML(detail_response.text)
        content = detail_html.xpath('//*[@id="ContentPlaceHolder1_lbl_fulltext"]//text()')

        return ' '.join(content).strip() if content else None

    except Exception as e:
        print(f"{species_name}: 爬取失败 - {str(e)}")
        return None


# 测试单个物种
test_result = crawl_plant_info("五角枫")
print("【五角枫测试结果】")
print(test_result if test_result else "未获取到数据")

# 批量爬取
results = []
for index, row in df.iterrows():
    species = row['植物种名']
    if pd.isna(species):
        continue

    print(f"正在处理: {species} ({index + 1}/{len(df)})")
    content = crawl_plant_info(species.strip())
    results.append({'物种名': species, '内容': content})

    # 礼貌性延时
    time.sleep(20)

# 保存结果
output_df = pd.DataFrame(results)
output_df.to_csv("F:\站点\中国地面\植物志爬取.csv", index=False, encoding='utf-8-sig')
print("爬取完成，结果已保存到 植物志数据爬取结果.csv")