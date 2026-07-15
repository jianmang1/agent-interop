import geopandas as gpd
import pandas as pd
from shapely.geometry import box

# 定义分割线的经纬度
split_latitude = 41.0

# 加载两个Shapefile文件
ioa_gdf = gpd.read_file(r'F:\个人\Export_Output.shp')
china_gdf = gpd.read_file(r'D:\数据\边界\中华人民共和国\中华人民共和国.shp')

# 确保所有数据使用相同的坐标参考系统（CRS），这里假设为WGS84 (EPSG:4326)
ioa_gdf = ioa_gdf.to_crs(epsg=4326)
china_gdf = china_gdf.to_crs(epsg=4326)

# 创建分割用的多边形，并确保其简单且有效
split_polygon = box(-180, -90, 180, split_latitude).buffer(0)

# 检查并修复ioa_gdf中的无效几何
ioa_gdf['geometry'] = ioa_gdf['geometry'].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)

# 检查并修复china_gdf中的无效几何
china_gdf['geometry'] = china_gdf['geometry'].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)

# 创建一个包含分割线的GeoDataFrame
split_line_gdf = gpd.GeoDataFrame(geometry=[split_polygon], crs=ioa_gdf.crs)

# 筛选ioa面中位于北纬41度以下的部分
ioa_below_41 = ioa_gdf[ioa_gdf.intersects(split_polygon)]

# 对于中国面中位于北纬41度以上的部分，先找到与分割线相交的部分
china_intersects_split = gpd.sjoin(china_gdf, split_line_gdf, how='inner', predicate='intersects')

# 检查sjoin结果中是否有index_left或index_right
if 'index_left' in china_intersects_split.columns:
    intersected_indices = china_intersects_split['index_left']
else:
    intersected_indices = china_intersects_split.index

# 从原始数据集中排除与分割线相交的部分
china_above_41 = china_gdf[~china_gdf.index.isin(intersected_indices)]

# 合并两个筛选后的GeoDataFrame
combined_gdf = gpd.GeoDataFrame(pd.concat([ioa_below_41, china_above_41], ignore_index=True))

# 保存新的Shapefile文件
output_path = r'F:\个人\merged_result.shp'
combined_gdf.to_file(output_path)

print(f"新Shapefile已保存至 {output_path}")