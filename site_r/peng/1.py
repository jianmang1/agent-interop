import ee
import math

# 初始化时指定项目ID
ee.Initialize(project='988582082023')  # 替换为你的实际项目ID

# 验证初始化是否成功
try:
    print(ee.Image('NASA/NASADEM_HGT/001').getInfo()['id'])
except ee.EEException as e:
    print("初始化失败:", str(e))

# 参数设置
index = 'NDVI'
folder_name = 'GEE_job2023.3.27'
start_year = 2013
end_year = 2022
satellites = 'Landsat'  # 可选 'Sentinel', 'Landsat', 'Mix'

# 加载站点数据
points = ee.FeatureCollection('projects/composed-apogee-416302/assets/expanded_locations')

# 日期范围
start_date = ee.Date.fromYMD(start_year, 1, 1)
end_date = ee.Date.fromYMD(end_year, 12, 31)


# Landsat 处理函数
def mask_clouds_landsat(image):
    qa = image.select('QA_PIXEL')
    cloud = qa.bitwiseAnd(1 << 5).And(qa.bitwiseAnd(1 << 7)).Or(qa.bitwiseAnd(1 << 3))
    return image.updateMask(cloud.Not())


def apply_scale_factors(image):
    optical = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    thermal = image.select('ST_B.*').multiply(0.00341802).add(149.0)
    return image.addBands(optical, None, True).addBands(thermal, None, True)


def add_landsat_vis(image):
    date = ee.Date(image.get('system:time_start'))
    years = date.difference(ee.Date('1970-01-01'), 'year')
    ndvi = image.normalizedDifference(['nir', 'red'])
    evi = image.expression(
        '2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1)',
        {'nir': image.select('nir'), 'red': image.select('red'), 'blue': image.select('blue')}
    )
    nir_ref = image.select('nir')
    nirv = ndvi.multiply(nir_ref)
    return image.addBands(ee.Image(years).rename('t').float()) \
        .addBands(ndvi.rename('NDVI')) \
        .addBands(evi.rename('EVI')) \
        .addBands(nir_ref.rename('NIR_reflectance')) \
        .addBands(nirv.rename('NIRv')) \
        .addBands(ee.Image.constant(1))


# 加载 Landsat 数据
if satellites in ['Landsat', 'Mix']:
    landsat_collections = []
    for sensor in ['LC08', 'LE07', 'LT05']:
        collection = ee.ImageCollection(f'LANDSAT/{sensor}/C02/T1_L2') \
            .filterBounds(points.geometry()) \
            .filterDate(start_date, end_date) \
            .map(mask_clouds_landsat) \
            .map(apply_scale_factors)

        if sensor == 'LC08':
            collection = collection.select(
                ['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7', 'QA_PIXEL'],
                ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'QA_PIXEL']
            )
        else:
            collection = collection.select(
                ['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B7', 'QA_PIXEL'],
                ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'QA_PIXEL']
            )

        landsat_collections.append(collection.map(add_landsat_vis))

    col_ls = ee.ImageCollection(landsat_collections[0].merge(landsat_collections[1])).merge(landsat_collections[2])


# 谐波回归函数（保持不变）
def fit_harmonic(collection, dependent_var):
    harmonic_independents = ee.List(['constant', 't', 'cos', 'sin'])

    def add_harmonic(image):
        time_rad = image.select('t').multiply(2 * math.pi)
        return image.addBands(time_rad.cos().rename('cos')) \
            .addBands(time_rad.sin().rename('sin'))

    harmonic_col = collection.map(add_harmonic)

    trend = harmonic_col.select(harmonic_independents.add(dependent_var)) \
        .reduce(ee.Reducer.linearRegression(harmonic_independents.size(), 1))

    coeffs = trend.select('coefficients') \
        .arrayProject([0]) \
        .arrayFlatten([harmonic_independents])

    def add_fitted(image):
        return image.addBands(
            image.select(harmonic_independents) \
                .multiply(coeffs) \
                .reduce('sum') \
                .rename(f'{dependent_var}_fitted')
        )

    return harmonic_col.map(add_fitted)


# 主程序
if __name__ == '__main__':
    # 运行谐波回归（处理两个指标）
    # 首先对 NDVI 进行回归
    fitted_col_ndvi = fit_harmonic(col_ls, 'NDVI')
    # 然后对 NIRv 进行回归（在 NDVI 的基础上）
    fitted_col = fit_harmonic(fitted_col_ndvi, 'NIRv')  # 最终集合包含 NDVI_fitted 和 NIRv_fitted

    # 获取所有点位
    points_list = points.toList(points.size())


    # 导出每个点位数据
    def export_data(feature):
        plot_name = feature.get('plot').getInfo()
        desc = f"data_{satellites}_{plot_name}_{start_year}_{end_year}"

        filtered = fitted_col.filterBounds(feature.geometry())

        def process_image(img):
            redu = img.reduceRegion(
                ee.Reducer.mean(),
                feature.geometry(),
                img.get('imageScale')  # 使用图像的原始分辨率
            )
            return ee.Feature(None, redu).set({
                'date': img.date().format(),
                'satellite': img.get('SATELLITE'),
                'plot': plot_name,
                'lat': feature.geometry().coordinates().get(0),
                'lon': feature.geometry().coordinates().get(1)
            })

        data = filtered.map(process_image)

        task = ee.batch.Export.table.toDrive(
            collection=data,
            description=desc[:100],
            folder=folder_name,
            fileNamePrefix=desc,
            fileFormat='CSV'
        )
        task.start()


    for i in range(points.size().getInfo()):
        feat = ee.Feature(points_list.get(i))
        export_data(feat)

    print("所有导出任务已启动，请检查Task Manager")