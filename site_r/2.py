import os


def add_prefix_to_files():
    """
    在vEOS, vPOS, vSOS这三个文件夹下的所有文件名最前面添加字母'v'
    """
    # 定义目标文件夹列表
    folders = ['vEOS', 'vPOS', 'vSOS']

    # 记录处理的文件数量
    total_renamed = 0

    for folder in folders:
        # 检查文件夹是否存在
        if not os.path.exists(folder):
            print(f"警告: 文件夹 '{folder}' 不存在，跳过处理")
            continue

        # 获取文件夹中的所有文件
        files = os.listdir(folder)

        for filename in files:
            # 构建原始文件路径
            old_path = os.path.join(folder, filename)

            # 跳过子目录，只处理文件
            if os.path.isfile(old_path):
                # 分离文件名和扩展名
                name, ext = os.path.splitext(filename)

                # 创建新的文件名（在原文件名前添加'v'）
                new_name = f"v{name}{ext}"
                new_path = os.path.join(folder, new_name)

                # 重命名文件
                try:
                    os.rename(old_path, new_path)
                    print(f"已重命名: {filename} -> {new_name}")
                    total_renamed += 1
                except Exception as e:
                    print(f"重命名失败 {filename}: {str(e)}")

    print(f"\n总共重命名了 {total_renamed} 个文件")


if __name__ == "__main__":
    print("开始批量重命名文件...")
    print("此脚本将在vEOS, vPOS, vSOS三个文件夹中的每个文件名前添加'v'")
    confirmation = input("确认执行此操作吗? (y/N): ")

    if confirmation.lower() == 'y':
        add_prefix_to_files()
    else:
        print("操作已取消")
