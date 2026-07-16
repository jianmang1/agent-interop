# -*- coding: utf-8 -*-

from pathlib import Path
from PIL import Image, ImageOps
import matplotlib.pyplot as plt
import numpy as np
import csv
from datetime import datetime

# === 配置区 ===
# 修改为你的图片路径（建议使用原始字符串 r"..." 或者直接用 Path）
IMAGE_PATH = Path('E:\Desktop\912pos\912.jpg')
# 是否在退出时自动保存到 CSV（也可按键 s 手动保存）
AUTO_SAVE_CSV = True
# 输出 CSV 文件路径
OUTPUT_CSV = Path("E:\Desktop\912pos\clicked_pixels.csv")


# === 工具函数 ===
def load_image(path: Path) -> np.ndarray:
    """读取图片并根据 EXIF 方向自动纠正，返回 numpy 数组（RGB）。"""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)  # 根据 EXIF 方向纠正
    return np.array(img)


class ClickCollector:
    def __init__(self, ax, image_array, img_path: Path, auto_save=True, out_csv=Path("clicked_pixels.csv")):
        self.ax = ax
        self.img_path = img_path
        self.image_array = image_array
        self.h, self.w = image_array.shape[:2]
        self.points = []  # list of (u, v)
        self.scats = []  # scatter handles
        self.texts = []  # annotation handles
        self.auto_save = auto_save
        self.out_csv = out_csv

        # 连接事件
        self.cid_click = ax.figure.canvas.mpl_connect('button_press_event', self.on_click)
        self.cid_key = ax.figure.canvas.mpl_connect('key_press_event', self.on_key)
        self.cid_close = ax.figure.canvas.mpl_connect('close_event', self.on_close)

        self.print_instructions()

    def print_instructions(self):
        print("\n======== 使用说明 ========")
        print(f"图像尺寸：width={self.w}, height={self.h} (像素)")
        print("左键：添加点；右键：撤销上一个点；中键：清空所有点")
        print("按 d 或 Backspace：撤销上一个点")
        print("按 c：清空所有点")
        print("按 s：保存已点击点到 CSV")
        print("按 q：关闭窗口（若开启 AUTO_SAVE_CSV 将自动保存）")
        print("像素坐标返回为 (u, v)，u 从左到右，v 从上到下，均为 0 基索引。")
        print("==========================\n")

    def on_click(self, event):
        # 只在图像坐标轴内响应
        if event.inaxes != self.ax:
            return
        # matplotlib 图像坐标：x -> u（列），y -> v（行）；origin='upper' 时 v 向下增大
        if event.button == 1:  # 左键添加
            if event.xdata is None or event.ydata is None:
                return
            u = int(round(event.xdata))
            v = int(round(event.ydata))
            # 限制在图像范围内
            if 0 <= u < self.w and 0 <= v < self.h:
                self.points.append((u, v))
                scat = self.ax.scatter([u], [v], s=40)
                txt = self.ax.text(u + 8, v + 8, str(len(self.points)), fontsize=9)
                self.scats.append(scat)
                self.texts.append(txt)
                self.ax.figure.canvas.draw_idle()
                print(f"Added #{len(self.points)}: (u={u}, v={v})")
        elif event.button == 3:  # 右键撤销
            self.undo_last()
        elif event.button == 2:  # 中键清空
            self.clear_all()

    def on_key(self, event):
        if event.key in ['d', 'backspace']:
            self.undo_last()
        elif event.key == 'c':
            self.clear_all()
        elif event.key == 's':
            self.save_csv()
        elif event.key == 'q':
            plt.close(self.ax.figure)

    def undo_last(self):
        if not self.points:
            return
        self.points.pop()
        h1 = self.scats.pop()
        h2 = self.texts.pop()
        try:
            h1.remove()
        except Exception:
            pass
        try:
            h2.remove()
        except Exception:
            pass
        self.ax.figure.canvas.draw_idle()
        print("撤销上一个点。")

    def clear_all(self):
        self.points.clear()
        for h in self.scats:
            try:
                h.remove()
            except Exception:
                pass
        for t in self.texts:
            try:
                t.remove()
            except Exception:
                pass
        self.scats.clear()
        self.texts.clear()
        self.ax.figure.canvas.draw_idle()
        print("已清空所有点。")

    def save_csv(self):
        if not self.points:
            print("无点可保存。")
            return
        self.out_csv.parent.mkdir(parents=True, exist_ok=True)
        with open(self.out_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["image_path", str(self.img_path)])
            writer.writerow(["image_width", self.w])
            writer.writerow(["image_height", self.h])
            writer.writerow(["saved_at", datetime.now().isoformat(timespec='seconds')])
            writer.writerow([])
            writer.writerow(["index", "u", "v"])  # 0-based 像素坐标
            for i, (u, v) in enumerate(self.points, start=1):
                writer.writerow([i, u, v])
        print(f"已保存 {len(self.points)} 个点到 CSV: {self.out_csv}")

    def on_close(self, event):
        if self.auto_save:
            self.save_csv()


def main():
    if not IMAGE_PATH.exists():
        raise FileNotFoundError(f"图片不存在：{IMAGE_PATH}")

    img = load_image(IMAGE_PATH)

    # 设定图形大小，避免超大图造成窗口过大
    plt.rcParams['figure.dpi'] = 100
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111)

    # origin='upper'：使得 v 轴向下增大，与图像像素坐标一致
    ax.imshow(img, origin='upper')
    ax.set_title("点击图像以记录像素坐标 (u, v) — 左键添加、右键撤销、中键清空。按 s 保存，q 退出。")
    ax.set_axis_off()

    collector = ClickCollector(ax, img, IMAGE_PATH, auto_save=AUTO_SAVE_CSV, out_csv=OUTPUT_CSV)

    plt.show()


if __name__ == '__main__':
    main()
