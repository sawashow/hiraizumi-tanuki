"""1面のボス（泰衡「呪落武者」）のシート2枚（白背景）から、使う姿を選んで、ゲーム用のコマにする。

使い方: python tools/make_boss1.py シート1.jpg シート2.jpg 出力フォルダ [--height 80] [--chunk 1] [--colors 14] [--list]
  --list   見つけた姿の番号と位置だけ表示し、番号入りの確認画像（出力フォルダ/boss_list_1.png・_2.png）を書く

姿は「上の行 → 次の行」「左 → 右」の順に番号が付く。ゲームで使う姿は、NAMES に (シートの番号, 姿の番号) で書く:
  walk（歩く）4 / stance（立ち）3 / high（高い構え）2 / swing（振る）2 / crouch（かがむ）2 / leap（跳ぶ）2
  death（のけぞる・倒れる・倒れる）3。倒れた姿は、体と、そばに落ちた兜を、1コマにまとめる
足元に引かれた黒い線は、消す。全コマ同じ縮尺（立ちの高さが --height ドット）・同じ少数色・同じ枠（足元と、体の横の中心をそろえる）。
ドットの粗さは --chunk（既定は1。2ドット角にすると、細い体がつぶれて、目も消えたので、やめた）。出力は 出力フォルダ/boss_動き_番号.png と、確認用の boss_sheet.png。
"""
import argparse
import colorsys
import os
import statistics
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import make_boss3 as b3  # noqa: E402
import make_enemy as me  # noqa: E402

# 動き → 使う姿の (シート, 番号)。番号を + でつなぐと、1コマにまとめる（--list で確かめる）
NAMES = {
    "walk": ((0, 3), (0, 4), (0, 5), (0, 6)),
    "stance": ((0, 0), (0, 1), (0, 2)),
    "high": ((0, 7), (0, 8)),
    "swing": ((0, 9), (0, 10)),
    "crouch": ((1, 0), (1, 1)),
    "leap": ((1, 3), (1, 2)),               # 跳び上がる / 空中で、太刀を振り上げる
    "death": ((1, 6), (1, 7, 8), (1, 7, 8)),   # のけぞる / 倒れる（兜と体）。3コマ目は、使わない（ほかのボスと、数をそろえる）
}
NO_LINE = {"leap", "death"}     # 空中・倒れた姿には、足元の線が無い（消す処理を、かけない）
COLORS = 14


def load(path):
    img = me.remove_white_bg(me.clean(me.remove_white_bg(Image.open(path))), erode=False)
    return img, b3.find_poses(img)


def crop_many(img, poses, idx):
    """いくつかの姿を、位置関係を保ったまま、1枚にまとめて切り出す"""
    boxes = [poses[i][0] for i in idx]
    x0, y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
    x1, y1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
    out = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    sp, op = img.load(), out.load()
    for i in idx:
        for x, y in poses[i][1]:
            if min(sp[x, y][:3]) < b3.WHITE:
                op[x - x0, y - y0] = sp[x, y]
    return out


def vivid(color, sat, gain):
    """色を、鮮やかに・明るくする（暗い色は、あまり変えない。輪郭の黒を、保つ）"""
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in color))
    if v < 0.16:
        return color
    r, g, b = colorsys.hsv_to_rgb(h, min(1.0, s * sat), min(1.0, v * gain))
    return (round(r * 255), round(g * 255), round(b * 255))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet1")
    ap.add_argument("sheet2")
    ap.add_argument("out")
    ap.add_argument("--height", type=int, default=80)
    ap.add_argument("--chunk", type=int, default=1)
    ap.add_argument("--colors", type=int, default=COLORS)
    ap.add_argument("--sat", type=float, default=2.0, help="色の鮮やかさの倍率（元絵は、くすんだ紫。夜の背景に埋もれるので、少し上げる）")
    ap.add_argument("--gain", type=float, default=1.3, help="明るさの倍率")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    sheets = [load(a.sheet1), load(a.sheet2)]
    os.makedirs(a.out, exist_ok=True)
    if a.list:
        for n, (img, poses) in enumerate(sheets):
            vis = Image.new("RGBA", img.size, (230, 230, 230, 255))
            vis.alpha_composite(img)
            d = ImageDraw.Draw(vis)
            for i, (b, pts) in enumerate(poses):
                d.rectangle(b, outline=(255, 0, 0))
                d.text((b[0] + 2, b[1] + 2), str(i), fill=(255, 0, 0))
                print(n, i, b, len(pts))
            vis.save(os.path.join(a.out, "boss_list_%d.png" % (n + 1)))
        return
    crops = {}
    for anim, picks in NAMES.items():
        crops[anim] = []
        for sheet, *idx in picks:
            c = crop_many(*sheets[sheet], idx)
            crops[anim].append(c if anim in NO_LINE else me.strip_ground_line(c))
    scale = a.height / a.chunk / statistics.median(c.height for c in crops["stance"])
    pal = me.palette_from([c for cs in crops.values() for c in cs], a.colors)
    pal = [vivid(c, a.sat, a.gain) for c in pal]
    pal += [(232, 40, 40), (150, 28, 32)]      # 赤く光る目（面積が小さくて、色を絞ると消えるので、必ず残す）
    placed = []
    for anim, cs in crops.items():
        for i, c in enumerate(cs):
            d = me.to_dots(c, scale, pal)
            ax = me.anchor_x(c, "bbox", scale)
            d = d.resize((d.width * a.chunk, d.height * a.chunk), Image.NEAREST)
            placed.append((anim, i, d, ax * a.chunk, d.height))
    left = max(p[3] for p in placed)
    right = max(p[2].width - p[3] for p in placed)
    up = max(p[4] for p in placed)
    cw, ch = left + right, up
    print("縮尺 %.2f 枠 %d x %d 基準(左,上) = %s" % (scale, cw, ch, (left, up)))
    frames = []
    for anim, i, d, ax, ay in placed:
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.paste(d, (left - ax, up - ay), d)
        canvas.save(os.path.join(a.out, "boss_%s_%d.png" % (anim, i)))
        frames.append((anim, canvas))
    S, G = 3, 8
    per_row = max(len(v) for v in crops.values())
    sheet = Image.new("RGB", (per_row * (cw * S + G) + G, len(crops) * (ch * S + G) + G), (92, 148, 252))
    for r, anim in enumerate(crops):
        for c, (_, f) in enumerate([f for f in frames if f[0] == anim]):
            big = f.resize((cw * S, ch * S), Image.NEAREST)
            sheet.paste(big, (G + c * (cw * S + G), G + r * (ch * S + G)), big)
    sheet.save(os.path.join(a.out, "boss_sheet.png"))


if __name__ == "__main__":
    main()
