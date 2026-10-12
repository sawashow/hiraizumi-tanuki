"""白背景のシートに、姿がばらばらに描いてある絵（行がそろっていない・動きが同じ行に混ざっている）から、姿を番号で選んで、コマにする。
生成AI（Gemini）のシートは、行や見出しが指示どおりにならないことが多いので、位置ではなく、番号で選ぶ。

使い方:
  python tools/make_poses.py シート.jpg 出力フォルダ 名前 --list
      見つけた姿に番号を振って、出力フォルダ/名前_list.png に書く（上の行から、左から）
  python tools/make_poses.py シート.jpg 出力フォルダ 名前 --anim idle=0,1 --anim draw=2,3,4 --anim death=9,10,11+12 \\
      --height 40 [--ref idle] [--colors 12] [--keep-colors "232,40,40"] [--chunk 1] [--gain 1.2] [--raw 名前2=x0,y0,x1,y1]

  --anim 動き=番号,番号   動きごとに、使う姿の番号を、コマの順に書く。「11+12」のように + でつなぐと、1コマにまとめる（散った破片など）
  --height             基準の動き（--ref。無ければ、最初の --anim）の、高さの中央値を、このドット数にする。全コマ、同じ縮尺
  --keep-colors        必ず残す色（目の赤など、面積が小さくて、色を絞ると消える色）。「;」区切り
  --raw 名前=範囲       元絵の範囲を、そのまま切り出して、同じ縮尺・同じ色で 名前.png に書く（矢など。文字と間違えて消される、細くて暗い物に使う）
  足元の黒い線・見出しの文字・腕や弓のすき間に残った白は、消す。枠は全コマ同じ大きさ（足元と、体の横の中心をそろえる）
出力: 出力フォルダ/名前_動き_番号.png、確認用の 名前_sheet.png（3倍）
"""
import argparse
import os
import statistics
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import make_boss3 as b3  # noqa: E402
import make_enemy as me  # noqa: E402
from slice_sheet import remove_white_bg  # noqa: E402


def crop_many(img, poses, idx):
    """いくつかの姿を、位置関係を保ったまま、1枚にまとめて切り出す（すき間に残った白は、消す）"""
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("out")
    ap.add_argument("name")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--anim", action="append", default=[])
    ap.add_argument("--height", type=float, default=40)
    ap.add_argument("--ref", default="")
    ap.add_argument("--colors", type=int, default=12)
    ap.add_argument("--keep-colors", default="")
    ap.add_argument("--chunk", type=int, default=1)
    ap.add_argument("--gain", type=float, default=1.0, help="明るさの倍率（暗い絵を、背景から浮かせる）")
    ap.add_argument("--min-pts", type=int, default=150, help="これより小さい塊は、無視する（元絵のピクセル数）")
    ap.add_argument("--raw", action="append", default=[])
    a = ap.parse_args()
    b3.MIN_PTS = a.min_pts
    src = Image.open(a.sheet)
    img = remove_white_bg(me.clean(remove_white_bg(src)), erode=False)
    poses = b3.find_poses(img)
    os.makedirs(a.out, exist_ok=True)
    if a.list or not a.anim:
        vis = Image.new("RGBA", img.size, (230, 230, 230, 255))
        vis.alpha_composite(img)
        d = ImageDraw.Draw(vis)
        for i, (b, pts) in enumerate(poses):
            d.rectangle(b, outline=(255, 0, 0))
            d.text((b[0] + 2, b[1] + 2), str(i), fill=(255, 0, 0))
            print(i, b, len(pts))
        vis.save(os.path.join(a.out, a.name + "_list.png"))
        return
    crops = {}
    for spec in a.anim:
        anim, picks = spec.split("=")
        crops[anim] = [me.strip_ground_line(crop_many(img, poses, [int(v) for v in pick.split("+")])) for pick in picks.split(",")]
    ref = a.ref or next(iter(crops))
    scale = a.height / a.chunk / statistics.median(c.height for c in crops[ref])
    raws = {}
    plain = remove_white_bg(src)        # 文字を消す処理を、かけていない絵（細くて暗い物が、残っている）
    for spec in a.raw:
        name, box = spec.split("=")
        c = plain.crop(tuple(int(v) for v in box.split(",")))
        raws[name] = c.crop(c.getbbox())
    pal = me.palette_from([c for cs in crops.values() for c in cs] + list(raws.values()), a.colors)
    if a.gain != 1.0:
        pal = [tuple(min(255, round(v * a.gain)) for v in c) for c in pal]
    pal += [tuple(int(v) for v in c.split(",")) for c in a.keep_colors.split(";") if c]

    def dots(c):
        d = me.to_dots(c, scale, pal)
        return d.resize((d.width * a.chunk, d.height * a.chunk), Image.NEAREST) if a.chunk > 1 else d

    placed = []
    for anim, cs in crops.items():
        for i, c in enumerate(cs):
            d = dots(c)
            placed.append((anim, i, d, me.anchor_x(c, "bbox", scale) * a.chunk, d.height))
    left = max(p[3] for p in placed)
    right = max(p[2].width - p[3] for p in placed)
    up = max(p[4] for p in placed)
    cw, ch = left + right, up
    print("縮尺 %.3f（元絵の %.1f ピクセルが、1ドット） 枠 %d x %d 基準(左,上) = %s" % (scale, 1 / scale, cw, ch, (left, up)))
    frames = []
    for anim, i, d, ax, ay in placed:
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.paste(d, (left - ax, up - ay), d)
        canvas.save(os.path.join(a.out, "%s_%s_%d.png" % (a.name, anim, i)))
        frames.append((anim, canvas))
    for name, c in raws.items():
        d = dots(c)
        d.save(os.path.join(a.out, name + ".png"))
        print(name, d.size)
    S, G = 3, 8
    per_row = max(len(v) for v in crops.values())
    sheet = Image.new("RGB", (per_row * (cw * S + G) + G, len(crops) * (ch * S + G) + G), (92, 148, 252))
    for r, anim in enumerate(crops):
        for c, (_, f) in enumerate([f for f in frames if f[0] == anim]):
            big = f.resize((cw * S, ch * S), Image.NEAREST)
            sheet.paste(big, (G + c * (cw * S + G), G + r * (ch * S + G)), big)
    sheet.save(os.path.join(a.out, a.name + "_sheet.png"))


if __name__ == "__main__":
    main()
