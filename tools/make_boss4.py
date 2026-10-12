"""4面ボス（清衡「金色坐仏」）のシート（白背景・いろいろな姿が並んでいる）から、使う姿を選んで、ゲーム用のコマにする。

使い方: python tools/make_boss4.py シート.jpg 出力フォルダ [--height 84] [--colors 16] [--list]
  元絵は boss4_sheet2.jpg（2026-10-12。蓮の台座に座った、6本腕の即身仏。前の boss4_sheet.jpg は、小さくて迫力が無かった）
  --list   見つけた姿の番号と位置だけ表示し、番号入りの確認画像（出力フォルダ/boss3_list.png）を書く（tools/make_boss3.py --list と同じ）

ゲームで使う姿は、NAMES に番号で書く:
  idle（浮く。腕6本）1 / pray（合掌。数珠の玉の予告）2 / cast（数珠を向ける）2 / spread（腕を広げる。光の柱）2
  hold（数珠を持つ。数珠の輪の予告）1 / roar（怒る。2コマ目は、赤い目。怒ったあとの「浮く」にも使う）2 / death（崩れる）3
元絵の「天を指す」は、下半身が切れていて、使えない。
全コマ同じ縮尺（合掌の高さが --height ドット）・同じ少数色。横は、蓮の台座の中心で、縦は、台座の下端で、そろえる（腕を上げた姿でも、体がずれない）。
出力: 出力フォルダ/boss4_動き_番号.png と、確認用の boss4_sheet.png。大きさが変わったら、config.py の ENEMY_ART["boss4"] を直す。
"""
import argparse
import os
import statistics
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import make_boss3 as b3  # noqa: E402
import make_enemy as me  # noqa: E402

NAMES = {"idle": (1,), "pray": (3, 4), "cast": (5, 6), "spread": (9, 10), "hold": (2,), "roar": (11, 12), "death": (13, 14, 14)}
COLORS = 16
KEEP = [(232, 40, 40), (150, 28, 32), (170, 226, 236)]      # 赤い目・青白い目（面積が小さくて、色を絞ると消えるので、必ず残す）


def base_x(img):
    """蓮の台座（絵の下 1/4）の、横の中心"""
    px = img.load()
    xs = [x for y in range(img.height * 3 // 4, img.height) for x in range(img.width) if px[x, y][3]]
    return (min(xs) + max(xs) + 1) // 2 if xs else img.width // 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("out")
    ap.add_argument("--height", type=int, default=84)
    ap.add_argument("--colors", type=int, default=COLORS)
    a = ap.parse_args()
    img = me.remove_white_bg(me.clean(me.remove_white_bg(Image.open(a.sheet))), erode=False)
    poses = b3.find_poses(img)
    os.makedirs(a.out, exist_ok=True)
    crops = {anim: [b3.crop_of(img, poses[i]) for i in idx] for anim, idx in NAMES.items()}
    scale = a.height / statistics.median(c.height for c in crops["pray"])
    pal = me.palette_from([c for cs in crops.values() for c in cs], a.colors) + KEEP
    placed = []
    for anim, cs in crops.items():
        for i, c in enumerate(cs):
            d = me.to_dots(c, scale, pal)
            placed.append((anim, i, d, base_x(d)))
    left = max(p[3] for p in placed)
    right = max(p[2].width - p[3] for p in placed)
    cw, ch = left + right, max(p[2].height for p in placed)
    print("縮尺 %.2f 枠 %d x %d 基準(左,下) = %s" % (scale, cw, ch, (left, ch)))
    frames = []
    for anim, i, d, ax in placed:
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.paste(d, (left - ax, ch - d.height), d)
        canvas.save(os.path.join(a.out, "boss4_%s_%d.png" % (anim, i)))
        frames.append((anim, canvas))
    S, G = 3, 8
    per_row = max(len(v) for v in crops.values())
    sheet = Image.new("RGB", (per_row * (cw * S + G) + G, len(crops) * (ch * S + G) + G), (40, 30, 16))
    for r, anim in enumerate(crops):
        for c, (_, f) in enumerate([f for f in frames if f[0] == anim]):
            big = f.resize((cw * S, ch * S), Image.NEAREST)
            sheet.paste(big, (G + c * (cw * S + G), G + r * (ch * S + G)), big)
    sheet.save(os.path.join(a.out, "boss4_sheet.png"))


if __name__ == "__main__":
    main()
