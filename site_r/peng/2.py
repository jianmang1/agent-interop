// 定义参数
var index = 'NDVI';           // 要绘制的指数类型
var folderName = 'GEE_job2023.3.27';   // Google Drive导出路径
var startYear = 2013;         // 起始年份
var endYear = 2022;
var satellites = 'Landsat';   // 可选：Sentinel, Landsat 或 Mix

// 加载站点数据
var sites = ee.FeatureCollection('users/huangmengjiao7/2021_2022locations');
var points = sites;
print(points, '监测站点');
Map.addLayer(points, {color:'red'}, '监测点位');

// 时间范围
var startDate = ee.Date.fromYMD(startYear,1,1);
var endDate = ee.Date.fromYMD(endYear,12,31);

// 获取第一个点作为中心
var poi = ee.Feature(points.first());
Map.centerObject(poi, 9);
Map.addLayer(poi, {color: 'blue'}, '兴趣点');

// 谐波回归参数
var dependent = ee.String('NDVI');
var independents = ee.List(['constant', 't']);
var timeField = 'system:time_start';

// 影像显示函数
var displayImage = function(date, region){
  var selectedImage = collection.filterBounds(region)
                       .filterDate(ee.Date(date).advance(-1, 'day'),
                               ee.Date(date).advance(1, 'day'));
  selectedImage.first().get('system:index').evaluate(function(obj) {
      Map.layers().set(3, ui.Map.Layer(ee.Image(selectedImage.first()),
          {bands: ['red', 'green', 'blue'], min: 0, max: 5000}, obj));
  });
};

// 卫星参数配置
var imageCollections = {
  'Landsat': {scale: 30, bands: ['blue','green','red','nir','swir1','swir2','QA_PIXEL']},
  'Sentinel': {scale: 10, bands: ['B2','B3','B4','B5','B6','B7','B8','B8A','B11','B12']}
};

// 通用函数：Landsat数据处理
function processLandsatCollection(collectionName, bandMap) {
  return ee.ImageCollection(collectionName)
    .filterBounds(points.geometry())
    .filterDate(startDate, endDate)
    .map(maskcloudsr)
    .map(applyScaleFactors)
    .select(ee.Keys(bandMap), ee.Values(bandMap))
    .map(addLandsatVIs);
}

// Landsat云掩膜
function maskcloudsr(image) {
  var qa = image.select('QA_PIXEL');
  var cloud = qa.bitwiseAnd(1 << 5).and(qa.bitwiseAnd(1 << 7)).or(qa.bitwiseAnd(1 << 3));
  return image.updateMask(cloud.not());
}

// Landsat辐射校正
function applyScaleFactors(image) {
  var optical = image.select('SR_B.').multiply(0.0000275).add(-0.2);
  var thermal = image.select('ST_B.*').multiply(0.00341802).add(149.0);
  return image.addBands(optical, null, true).addBands(thermal, null, true);
}

// Landsat指数计算
function addLandsatVIs(image) {
  var date = ee.Date(image.get(timeField));
  var ndvi = image.normalizedDifference(['nir','red']).rename('NDVI');
  var nirRef = image.select('nir');
  var nirv = ndvi.multiply(nirRef).rename('NIRv');
  return image
    .addBands(ndvi)
    .addBands(nirv)
    .set('imageScale', 30)
    .set('SATELLITE', image.get('SPACECRAFT_ID'));
}

// Sentinel-2数据处理
function processSentinelCollection() {
  return ee.ImageCollection('COPERNICUS/S2')
    .filterBounds(points.geometry())
    .filterDate(startDate, endDate)
    .map(maskS2clouds)
    .select(imageCollections.Sentinel.bands, ['blue','green','red','re1','re2','re3','nir','nir2','swir1','swir2'])
    .map(addS2VIs);
}

// Sentinel-2云掩膜
function maskS2clouds(image) {
  var qa = image.select('QA60');
  var mask = qa.bitwiseAnd(1 << 10).eq(0).and(qa.bitwiseAnd(1 << 11).eq(0));
  return image.updateMask(mask);
}

// Sentinel-2指数计算 (优化后)
function addS2VIs(image) {
  var date = ee.Date(image.get(timeField));
  var red = image.select('red').multiply(0.0001);
  var nir = image.select('nir').multiply(0.0001);
  var blue = image.select('blue').multiply(0.0001);

  var ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI');
  var nirv = ndvi.multiply(nir).rename('NIRv');

  return image
    .addBands(ndvi)
    .addBands(nirv)
    .set('imageScale', 10)
    .set('CLOUD_COVER', image.get('CLOUDY_PIXEL_PERCENTAGE'));
}

// 构建数据集
var collection;
if (satellites === 'Landsat') {
  var landsatBands = {
    'LT05': ['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5','SR_B7','QA_PIXEL'],
    'LE07': ['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5','SR_B7','QA_PIXEL'],
    'LC08': ['SR_B2','SR_B3','SR_B4','SR_B5','SR_B6','SR_B7','QA_PIXEL']
  };

  var col5 = processLandsatCollection('LANDSAT/LT05/C02/T1_L2', landsatBands.LT05);
  var col7 = processLandsatCollection('LANDSAT/LE07/C02/T1_L2', landsatBands.LE07);
  var col8 = processLandsatCollection('LANDSAT/LC08/C02/T1_L2', landsatBands.LC08);
  collection = col5.merge(col7).merge(col8);

} else if (satellites === 'Sentinel') {
  collection = processSentinelCollection();

} else { // Mix模式
  var landsat = ...; // 同Landsat处理
  var sentinel = processSentinelCollection();
  collection = landsat.merge(sentinel);
}

// 谐波回归函数
function harmonicRegression(collection, targetBand) {
  return collection.map(function(img) {
      var t = img.date().difference(ee.Date('1970-01-01'), 'year');
      var cos = t.multiply(2 * Math.PI).cos();
      var sin = t.multiply(2 * Math.PI).sin();
      return img.addBands(ee.Image(t).rename('t'))
               .addBands(cos.rename('cos'))
               .addBands(sin.rename('sin'));
    })
    .reduce(ee.Reducer.linearRegression({
      numX: 4,
      numY: 1
    }))
    .select('coefficients');
}

// 执行谐波回归
var ndviCoefficients = harmonicRegression(collection.select(['NDVI','t','cos','sin']), 'NDVI');
var nirvCoefficients = harmonicRegression(collection.select(['NIRv','t','cos','sin']), 'NIRv');

// 数据导出优化
var exportData = points.map(function(feature) {
  var pointData = collection.map(function(image) {
    var stats = image.reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: feature.geometry(),
      scale: image.get('imageScale')
    });
    return ee.Feature(null, stats)
      .set({
        date: image.date().format('YYYY-MM-dd'),
        satellite: image.get('SATELLITE'),
        cloudCover: image.get('CLOUD_COVER')
      });
  });
  return pointData.flatten();
}).flatten();

// 批量导出
Export.table.toDrive({
  collection: exportData,
  description: 'Vegetation_Indices_Export',
  fileFormat: 'CSV',
  folder: folderName
});

// 可视化参数
var visParams = {bands: ['red', 'green', 'blue'], min: 0, max: 5000};
var chart = ui.Chart.image.series(collection.select('NDVI'), poi.geometry(), ee.Reducer.mean(), 30)
  .setOptions({
    title: 'NDVI时间序列',
    vAxis: {title: 'NDVI'},
    hAxis: {title: '日期'},
    lineWidth: 1,
    pointSize: 3
  });
print(chart);