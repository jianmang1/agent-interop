import subprocess
from osgeo import gdal

# 输入文件路径列表
input_files = [
    r"D:\MOD12Q2\vs\classai\1.tif",
    r"D:\MOD12Q2\vs\classai\2.tif",
    r"D:\MOD12Q2\vs\classai\3.tif",
    r"D:\MOD12Q2\vs\classai\4.tif"
]

# 目标文件路径
target_file = r"I:\output\SOS_climate_pcorr\best_month_complete\best_month_complete.tif"

# 获取目标文件的空间参考系统
ds_target = gdal.Open(target_file)
target_srs_wkt = ds_target.GetSpatialRef().ExportToWkt()
ds_target = None  # 关闭数据集

for input_file in input_files:
    # 创建输出文件名
    output_file = f"{input_file.split('.')[0]}_resampled2.tif"

    # gdalwarp 命令
    command = [
        "gdalwarp",
        "-t_srs", target_srs_wkt,  # 使用目标文件的空间参考系统
        "-r", "bilinear",  # 使用双线性插值方法
        input_file,
        output_file
    ]

    # 运行命令
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"成功重采样 {input_file} 到 {output_file}")
    else:
        print(f"重采样 {input_file} 失败: {result.stderr}")



