import pandas as pd
from pygbif import species

def get_growth_habit(latin_name):
    try:
        res = species.name_backbone(name=latin_name)
        if 'data' in res:
            return res['data'].get('growthHabit', res['data'].get('lifeStage'))
        return None
    except:
        return None

# 读取数据
# 示例：验证数据读取
df = pd.read_csv(r"F:\站点\植物物候观测数据集20161202\木转换结果2.csv", encoding='gbk')
print(df.head())  # 打印前几行，确认数据加载成功
# 示例：手动测试API
test_name = "Betula ermanii"  # 棘皮桦的学名
res = species.name_backbone(name=test_name)
print(res)  # 打印返回的完整结果
# 查询并添加分类
df['growth_habit'] = df['拉丁名'].apply(get_growth_habit)

# 保存结果
df.to_csv(r"F:\站点\植物物候观测数据集20161202\木转换结果_with_habit.csv", index=False, encoding='gbk')