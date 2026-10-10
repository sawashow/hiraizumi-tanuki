"""アイテムの絵（白背景・横一列に3つ）を、ゲーム用のドット絵に変換する。
使い方: python tools/make_items.py シート.jpg 出力フォルダ 名前1,名前2,名前3 [--scale 0.04]
  - 白い背景を外から塗りつぶして透過にし、近くにある塊（きらめきなど）を1つにまとめて、左から順に切り出す
  - 3つとも同じ縮尺で縮小する（元絵の大きさの比率を保つ）。半透明の画素は、はっきりした色（不透明）にする
出力: 出力フォルダ/名前.png
"""
import argparse
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from slice_sheet import components, remove_white_bg  # noqa: E402

MERGE_GAP = 30   # この距離（元絵のピクセル）より近い塊は、同じアイテムとみなす


def main(src, out_dir, names, scale, clear_white=False):
    img = remove_white_bg(Image.open(src), erode=False)
    if clear_white:   # 中に閉じた白（鳥居の梁の間）や、うっすらした光も消す
        px = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = px[x, y]
                if a and min(r, g, b) > 205 and max(r, g, b) - min(r, g, b) < 60:
                    px[x, y] = (0, 0, 0, 0)
    boxes = sorted((c["box"] for c in components(img)), key=lambda b: b[0])
    groups = []
    for b in boxes:
        if groups and b[0] - groups[-1][2] < MERGE_GAP:
            g = groups[-1]
            groups[-1] = (min(g[0], b[0]), min(g[1], b[1]), max(g[2], b[2]), max(g[3], b[3]))
        else:
            groups.append(b)
    groups = [g for g in groups if (g[2] - g[0]) * (g[3] - g[1]) > 4000]
    print("アイテム数:", len(groups))
    os.makedirs(out_dir, exist_ok=True)
    for name, (x0, y0, x1, y1) in zip(names, groups):
        crop = img.crop((x0, y0, x1, y1))
        small = crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))), Image.NEAREST)
        px = small.load()
        for y in range(small.height):
            for x in range(small.width):
                r, g, b, a = px[x, y]
                px[x, y] = (r, g, b, 255) if a >= 128 else (0, 0, 0, 0)
        small.save(os.path.join(out_dir, name + ".png"))
        print(name, small.size)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out_dir")
    ap.add_argument("names")
    ap.add_argument("--scale", type=float, default=0.0714)
    ap.add_argument("--clear-white", action="store_true", help="閉じた白や、うっすらした光も消す")
    a = ap.parse_args()
    main(a.src, a.out_dir, a.names.split(","), a.scale, a.clear_white)
