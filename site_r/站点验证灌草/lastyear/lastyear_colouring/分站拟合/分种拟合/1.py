import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据（假设路径和数据正确）
grass_mean = pd.read_csv('F:\\站点\\中国地面\\草本数据_每年均值（种）.csv', encoding='gbk')
wood_mean = pd.read_csv('F:\\站点\\中国地面\\灌本数据_每年均值（种）.csv', encoding='gbk')

sites_of_interest  = [
    '七角白蔹', '万年蒿', '三叶草', '东北石竹', '东方草莓', '二月兰',
    '兴安毛茛', '卷丹', '地锦', '夏至草', '大丽花', '大礼花',
    '大花萱草', '大苞萱草', '射干', '少花野菊', '山兰', '山芍药',
    '木瓜', '桔梗', '棉团铁成莲', '沙蒿', '爬山虎', '玉竹',
    '白莲蒿', '益母', '睡莲（白）', '秋海棠', '紫花地丁',
    '紫花玉簪', '细梗石头花', '芍药', '芦苇', '苍耳', '苜蓿',
    '苦苣', '苦参', '苦苦菜', '苦菜', '草莓', '荠', '荷包牡丹',
    '荷花', '荷花（后湖）', '莲', '菊芋', '葶苈', '蒲公英',
    '蜀葵', '车前', '车前草', '轮叶党参', '野草', '野菊',
    '金针菜', '铃兰', '飞蓬', '马兰花', '马蔺', '马齿苋',
    '黄花菜', '黄花萱草', '龙芽草三裂绣线菊', '三角枫', '东北卫矛',
    '东北山梅花', '东北扁核木', '东北溲疏', '东北茶藨子', '东北连翘',
    '东陵绣球', '丝棉木', '中亚锦鸡儿', '中国柽柳', '中宁枸杞',
    '中麻黄', '乌柳', '乌桕', '乌苏里绣线菊', '乌苏里鼠李',
    '互叶醉鱼草', '五叶地锦', '京山梅花', '伞花蔷薇', '侧柏',
    '修枝荚蒾', '倒榆', '元宝枫', '元宝槭', '光萼溲疏', '八仙花',
    '关东巧玲花', '兴安杜鹃', '兴安落叶松', '刺南蛇藤', '刺梅',
    '刺梨', '刺榆', '刺槐', '刺玫', '加拿大杨', '北京丁香',
    '北京杨', '北京锦鸡儿', '北海道黄杨木', '千头柏', '华北卫矛',
    '华北绣线菊', '华北落叶松', '华山松', '单瓣榆叶梅', '单瓣黄刺玫',
    '卫矛', '叉子圆柏', '叶底珠', '合欢', '君迁子', '唐古特白刺',
    '四川忍冬', '国槐', '圆叶鼠李', '圆柏', '圆锥绣球', '土庄绣线菊',
    '垂柳', '多刺玫蔷薇', '多枝柽柳', '大叶朴', '大字杜鹃', '大花溲疏',
    '大黄柳', '太平花', '家榆', '小叶丁香', '小叶杨', '小叶椴',
    '小叶锦鸡儿', '小蜡', '小青杨', '山丁子', '山刺玫', '山杏',
    '山杨', '山桃', '山梨', '山楂', '山槐', '山皂荚', '山茱萸',
    '山荆子', '山葡萄', '山里红', '常青藤', '库页悬钩子', '悬铃木',
    '截叶榆叶梅', '探春', '接骨木', '文冠果', '新疆杨', '日本晚樱',
    '日本樱花', '早花忍冬', '早锦带花', '旱柳', '春榆', '暖木条荚蒾',
    '暴马丁香', '望春玉兰', '朝鲜丁香', '朝鲜小檗', '朝鲜山茱萸',
    '朝鲜接骨木', '朝鲜黄杨', '木槿', '木瓜', '木绣球',
    '木通马兜铃', '朴树', '李', '李子', '李子树', '杏', '杏树',
    '杜仲', '杜松', '杜梨', '杠柳', '板栗', '构树', '枣', '枣树',
    '枫香', '枸杞', '柞栎', '柠条锦鸡儿', '柳叶绣线菊', '柳树',
    '柽柳', '柿', '柿树', '树锦鸡儿', '栒子木', '核桃', '核桃秋',
    '栾树', '桃叶卫茅', '桃叶卫茅', '桃树', '桃梅', '桐　树', '桑',
    '桑树', '桧柏', '梓树', '梣叶槭', '梧桐', '梨树', '梭梭',
    '楸树', '榆', '榆叶梅', '榆树', '榛', '榛子', '槐树', '樟子松',
    '樱桃', '毛刺槐', '毛果绣线菊', '毛柏杨', '毛梾', '毛樱桃',
    '毛漆树', '毛白杨', '水曲柳', '水杉', '水榆花秋', '水腊树',
    '江南槐', '沙冬青', '沙地柏', '沙拐枣', '沙木蓼', '沙枣',
    '沙棘', '沙蒿', '油松', '法国梧桐', '法国梧桐树', '泡桐',
    '洋丁香', '洋槐', '火炬树', '灵武长枣', '爬山虎', '牡丹',
    '牡丹樱', '猬实', '玉兰', '玉兰树', '玉叶地锦', '玫瑰',
    '珍珠梅', '珍珠绣线菊', '甘肃小檗', '甘蒙柽柳', '甘蒙锦鸡儿',
    '白丁香', '白杄', '白桦', '白榆', '白沙蒿', '白玉兰', '白玉堂',
    '白皮松', '白绢梅', '白花丁香', '白蜡', '百花山花秋', '皂荚',
    '省沽油', '短梗五加', '短穗柽柳', '石楠', '石榴', '石蚕叶绣线菊',
    '碧桃', '秋海棠', '秦岭忍冬', '稠李', '粉花绣线菊', '糖槭',
    '糠椴', '紫杉', '紫丁香', '紫叶小檗', '紫叶李', '紫叶桃',
    '紫椴', '紫穗槐', '紫荆', '紫薇', '紫藤', '红松', '红柳',
    '红丁香', '红叶小檗', '红叶李', '红梅', '红王子锦带', '红玫瑰',
    '红瑞木', '红皮云杉', '红花锦鸡儿', '红运玉兰', '细叶小檗',
    '细枝岩黄耆', '细穗柽柳', '绣球荚蒾', '绣线菊', '绦柳',
    '绿叶悬钩子', '美人梅', '美国白蜡', '美国黄松', '美国黑核桃',
    '老铁山腺毛茶藨子', '胡杨', '胡枝子', '胡桃楸', '胡颓子',
    '腊梅', '腺毛茶藨子', '臭椿', '色木槭', '芙蓉', '花曲柳',
    '花木兰', '花木蓝', '苦楝', '苹果', '茶条槭', '荆条',
    '荷花丁香', '葡萄', '葱皮忍冬', '蒙古扁桃', '蒙古栎', '蒙椴',
    '蔷薇', '藏花忍冬', '虎榛子', '蜡梅', '西府海棠', '西洋接骨木',
    '豆梨', '贴梗海棠', '辛夷', '辽东丁香', '辽东栎', '辽东楤木',
    '迎春', '迎春花', '迎红杜鹃', '连翘', '郁李', '酸枣',
    '重瓣棣棠花', '重瓣榆叶梅', '重瓣黄刺玫', '野蔷薇', '金丝柳',
    '金刚鼠李', '金枝垂柳', '金老梅', '金花忍冬', '金钟花',
    '金钟连翘', '金银忍冬', '金银木', '金银花', '钩齿溲疏',
    '铃铛刺', '银杏', '锦带花', '长柄女贞', '长梗郁李', '长白忍冬',
    '长白瑞香', '长白茶藨子', '长白落叶松', '长穗柽柳', '雪松',
    '雪柳', '霸王', '青杄', '青海云杉', '风箱果', '香茶藨子',
    '香荚蒾', '鸡树条子', '鸡树条荚蒾', '鸡麻', '鹅掌楸',
    '鹿角桧', '黄刺条', '黄刺梅', '黄刺玫', '黄山栾', '黄栌',
    '黄槐', '黄檗', '黄花忍冬', '黄花落叶松', '黄菠萝', '黄蔷薇',
    '黑桦', '鼠李', '龙爪槐', '龙须柳'
]

pheno_columns = [
   '开始展叶期', '展叶盛期'
]

# 过滤站点数据，仅保留有效样本量大于3的数据
def filter_sites_by_valid_samples(df, sites, min_valid_samples=3):
    filtered_df = df[df['植物种名'].isin(sites)]
    return filtered_df.groupby('植物种名').filter(lambda x: len(x.dropna(subset=['lastyear_叶开始变色期', *pheno_columns])) > min_valid_samples)

grass_filtered = filter_sites_by_valid_samples(grass_mean, sites_of_interest)
wood_filtered = filter_sites_by_valid_samples(wood_mean, sites_of_interest)


def plot_scatter_with_fit(df, title):
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 12))
    num_phenos = len(pheno_columns)

    # 使用cm.hsv生成足够多的颜色
    cmap = plt.get_cmap('hsv')
    colors = cmap(np.linspace(0, 1, len(sites_of_interest)))

    for i, pheno in enumerate(pheno_columns):
        ax = axes[i]
        all_x, all_y = [], []

        for j, site in enumerate(sites_of_interest):
            site_data = df[df['植物种名'] == site]
            valid_data = site_data[['lastyear_叶开始变色期', pheno]].dropna()
            valid_data = valid_data[np.isfinite(valid_data).all(axis=1)]

            if not valid_data.empty:
                x = valid_data['lastyear_叶开始变色期']
                y = valid_data[pheno]
                all_x.extend(x)
                all_y.extend(y)

                # 控制图例显示
                ax.scatter(x, y, label=f'{site} 数据', color=colors[j], alpha=0.7)

                # 拟合曲线
                slope, intercept, r_value, _, _ = linregress(x, y)
                fit_line_x = np.linspace(min(x), max(x), 100)
                fit_line_y = slope * fit_line_x + intercept
                ax.plot(fit_line_x, fit_line_y, color=colors[j], linestyle='--',
                        label=f'{site} Fit ($R^2$={r_value ** 2:.2f}, slope={slope:.2f})')

        # 全站点拟合曲线
        if len(all_x) > 1:
            slope_all, intercept_all, r_value_all, _, _ = linregress(all_x, all_y)
            fit_line_x_all = np.linspace(min(all_x), max(all_x), 100)
            fit_line_y_all = slope_all * fit_line_x_all + intercept_all
            ax.plot(fit_line_x_all, fit_line_y_all, color='black', linestyle='-',
                    label=f'全站点 Fit ($R^2$={r_value_all ** 2:.2f}, slope={slope_all:.2f})')

        ax.set_title(f'{title} - {pheno}')
        ax.set_ylabel(pheno)

        # 控制图例显示
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))  # 调整位置避免遮挡

    # 设置x轴标签
    for ax in axes[-1:]:
        ax.set_xlabel('lastyear_叶开始变色期')

    plt.tight_layout()
    plt.show()

# 绘制图表
plot_scatter_with_fit(grass_filtered, '草本数据')
plot_scatter_with_fit(wood_filtered, '灌木数据')


