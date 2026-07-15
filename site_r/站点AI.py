import rasterio
import pandas as pd
from rasterio.transform import xy
from pathlib import Path

# 定义路径
RASTER_PATH = Path(r'D:\数据\AI\Global-AI_ET0_v3_annual\output_cropped.tif')
SITE_CSV_PATH = Path(r'F:\个人\allsite1.csv')


# 读取站点CSV文件
def read_sites_from_csv(csv_path):
    """读取站点CSV文件并返回站点信息"""
    sites_df = pd.read_csv(csv_path)
    return sites_df


# 从栅格文件中提取指定坐标的值
def extract_raster_values(raster_path, sites_df):
    """从栅格文件中提取站点对应的值"""
    # 打开栅格文件
    with rasterio.open(raster_path) as src:
        transform = src.transform
        band_data = src.read(1)  # 读取第一个波段

        # 创建一个列表存储结果
        results = []

        for _, row in sites_df.iterrows():
            site = row['Site']
            latitude = row['Latitude']
            longitude = row['Longitude']

            # 将经纬度转换为栅格索引
            try:
                row_idx, col_idx = src.index(longitude, latitude)
                value = band_data[row_idx, col_idx]  # 提取对应位置的值
                results.append({'Site': site, 'Latitude': latitude, 'Longitude': longitude, 'Value': value})
            except Exception as e:
                print(f"Error extracting value for site {site}: {e}")
                results.append({'Site': site, 'Latitude': latitude, 'Longitude': longitude, 'Value': None})

    return pd.DataFrame(results)


# 主函数
def main():
    # 读取站点数据
    sites_df = read_sites_from_csv(SITE_CSV_PATH)

    # 提取栅格值
    result_df = extract_raster_values(RASTER_PATH, sites_df)

    # 输出结果到CSV文件
    output_path = SITE_CSV_PATH.parent / "sites_with_values.csv"
    result_df.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()