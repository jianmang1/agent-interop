import os

# 定义三个文件夹路径
folders = [
    r"E:\中国典型旱区地表植被物候数据集\vEOS",
    r"E:\中国典型旱区地表植被物候数据集\vPOS",
    r"E:\中国典型旱区地表植被物候数据集\vSOS"
]

# 遍历每个文件夹
for folder in folders:
    if os.path.exists(folder):
        # 获取文件夹中所有文件
        for filename in os.listdir(folder):
            old_path = os.path.join(folder, filename)
            # 检查是否为文件（而非子文件夹）
            if os.path.isfile(old_path):
                # 构造新文件名（在原文件名前加'v'）
                new_filename = 'v' + filename
                new_path = os.path.join(folder, new_filename)

                # 重命名文件
                os.rename(old_path, new_path)
                print(f"已重命名: {filename} -> {new_filename}")
    else:
        print(f"文件夹不存在: {folder}")