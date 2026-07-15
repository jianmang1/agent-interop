import ee

# 初始化时指定项目ID
ee.Initialize(project='988582082023')  # 替换为你的实际项目ID


def phen(year, day_of_year):
    start_date = ee.Date.fromYMD(year, 1, 1).advance(day_of_year - 1, 'day')
    end_date = start_date.advance(1, 'day')

    dataset = ee.ImageCollection('ECMWF/ERA5/DAILY') \
        .filterDate(start_date, end_date) \
        .select(['mean_2m_air_temperature', 'dewpoint_2m_temperature'])

    # 检查数据集是否为空
    print(f'Number of images in dataset for date {start_date.format("YYYY-MM-dd").getInfo()}:',
          dataset.size().getInfo())

    # 计算饱和水汽压
    def calc_sat_vapor_pressure(temp):
        return temp.expression(
            '6.11 * exp(17.27 * temp / (temp + 237.3))',
            {'temp': temp.select('mean_2m_air_temperature')}
        ).rename('sat_vapor_pressure')

    # 计算实际水汽压
    def calc_actual_vapor_pressure(dewpoint):
        return dewpoint.expression(
            '6.11 * exp(17.27 * dewpoint / (dewpoint + 237.3))',
            {'dewpoint': dewpoint.select('dewpoint_2m_temperature')}
        ).rename('actual_vapor_pressure')

    # 计算VPD
    def calculate_vpd(image):
        sat_vp = calc_sat_vapor_pressure(image)
        act_vp = calc_actual_vapor_pressure(image)
        vpd = sat_vp.subtract(act_vp).rename('vpd')
        return image.addBands(vpd)

    # 添加VPD波段到数据集
    vpd_dataset = dataset.map(calculate_vpd)

    # 获取第一个影像
    first_image = vpd_dataset.first()

    if first_image:
        # 导出结果到Google Drive
        day_of_year_str = f'{day_of_year:03}'  # 格式化为三位数，例如 001, 002, ..., 365
        export_task = ee.batch.Export.image.toDrive({
            'image': first_image,
            'description': f'VPD_{year}_{day_of_year_str}',
            'folder': "ERA5",
            'scale': 1000,  # 设置合适的分辨率，例如1km
            'region': first_image.geometry(),  # 设置导出区域
            'maxPixels': 1e13
        })
        export_task.start()
    else:
        print(f"No data available for date {start_date.format('YYYY-MM-dd').getInfo()}")


# 执行函数
for year in range(1982, 1983):  # 假设不是闰年
    for day_of_year in range(1, 366):
        phen(year, day_of_year)



