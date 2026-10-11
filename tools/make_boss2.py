"""2面ボス（基衡）のシート（白背景・動きが行ごとに並ぶ）を、コマごとに切り出して、ゲーム用に縮める。

使い方:  python tools/make_boss2.py シート.jpg 出力フォルダ [--height 76] [--list]
  --list   切り出したコマの位置だけ表示する（番号と、位置を確かめるため）

切り出したコマに、NAMES で名前を付け、全コマ同じ縮尺（待機の高さが --height ドット）・
同じ少数色・同じ枠（足元と、体の横の中心をそろえる）にして、出力フォルダに boss2_名前.png で書く。
扇（投げたあと）は、体と別の絵（boss2_fan.png）、花びらは、別の絵にして出す。
"""
import argparse
import os

from PIL import Image, ImageChops, ImageDraw


def background_mask(im):
    """外側とつながった、白い部分を消した、透明度（255=絵）"""
    r, g, b = im.split()
    m = ImageChops.darker(ImageChops.darker(r, g), b).point(lambda v: 255 if v > 235 else 0)
    ImageDraw.floodfill(m, (0, 0), 128)
    return m.point(lambda v: 0 if v == 128 else 255)


def segments(mask, y0, y1, gap=14):
    """行の中の、横に分かれたコマの範囲"""
    band = mask.crop((0, y0, mask.width, y1))
    cols = band.resize((mask.width, 1), Image.BOX).point(lambda v: 255 if v > 0 else 0)
    px = cols.load()
    segs, x = [], 0
    while x < mask.width:
        if px[x, 0]:
            s = x
            while x < mask.width and px[x, 0]:
                x += 1
            segs.append([s, x])
        else:
            x += 1
    out = []
    for s in segs:
        if out and s[0] - out[-1][1] < gap:
            out[-1][1] = s[1]
        else:
            out.append(s)
    return out


# 切り出した順番 → 名前（コマの数や順番が変わったら、--list で確かめて直す）
NAMES = ["idle_0", "idle_1", "idle_2", "walk_0", "walk_1", "fan_up", "fan_swing", "throw_0", "throw_1",
         "fan", None, "petal", "hurt", "down", "vanish"]
BODY = ("idle_0", "idle_1", "idle_2", "walk_0", "walk_1")   # この高さが、--height になる
CANVAS_W = 120
COLORS = 28
EYE = (120, 235, 245)   # 光る目（縮めると薄まるので、あとから、塗り直す）


def torso_x(img):
    """体の横の中心（霧の長いしっぽに引かれないよう、真ん中の高さの絵の重心）"""
    w, h = img.size
    a = img.split()[3]
    band = a.crop((0, int(h * 0.3), w, int(h * 0.7)))
    px = band.load()
    sx = n = 0
    for y in range(band.height):
        for x in range(band.width):
            if px[x, y]:
                sx += x
                n += 1
    return sx / n if n else w / 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("out")
    ap.add_argument("--rows", default="255,512", help="行の境目（元絵の縦の位置）")
    ap.add_argument("--height", type=int, default=76)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    im = Image.open(args.sheet).convert("RGB")
    mask = background_mask(im)
    cuts = [0] + [int(v) for v in args.rows.split(",")] + [im.height]
    tiles = []
    for y0, y1 in zip(cuts, cuts[1:]):
        for x0, x1 in segments(mask, y0, y1):
            box = (x0, y0, x1, y1)
            tile = im.crop(box).convert("RGBA")
            tile.putalpha(mask.crop(box))
            tiles.append(tile.crop(tile.getbbox()))
            print(len(tiles) - 1, box, "w,h", tiles[-1].size)
    if args.list:
        return
    named = {n: t for n, t in zip(NAMES, tiles) if n}
    body_h = sorted(named[n].height for n in BODY)[len(BODY) // 2]
    k = args.height / body_h
    small = {}
    for n, t in named.items():
        sm = t.resize((max(1, round(t.width * k)), max(1, round(t.height * k))), Image.BOX)
        eye = t.convert("RGB").point(lambda v: v)   # 元絵で、水色に光っている所を探す
        er, eg, eb = eye.split()
        m = ImageChops.multiply(ImageChops.multiply(eb.point(lambda v: 255 if v > 190 else 0), eg.point(lambda v: 255 if v > 170 else 0)),
                                er.point(lambda v: 255 if v < 140 else 0))
        m = m.resize(sm.size, Image.BOX).point(lambda v: 255 if v > 24 else 0)
        sm.paste(Image.new("RGBA", sm.size, EYE + (255,)), (0, 0), ImageChops.multiply(m, sm.split()[3].point(lambda v: 255 if v > 128 else 0)))
        small[n] = sm
    # 共通の少数色
    sheet = Image.new("RGB", (sum(t.width for t in small.values()), max(t.height for t in small.values())), (255, 0, 255))
    x = 0
    for t in small.values():
        sheet.paste(t.convert("RGB"), (x, 0), t.split()[3].point(lambda v: 255 if v > 128 else 0))
        x += t.width
    pal = sheet.quantize(COLORS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    os.makedirs(args.out, exist_ok=True)
    for n, t in small.items():
        alpha = t.split()[3].point(lambda v: 255 if v > 128 else 0)
        q = t.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE).convert("RGBA")
        q.putalpha(alpha)
        if n in ("fan", "petal"):
            q.save(os.path.join(args.out, "boss2_%s.png" % n))
            continue
        canvas = Image.new("RGBA", (CANVAS_W, args.height + 4), (0, 0, 0, 0))
        cx = round(CANVAS_W / 2 - torso_x(q))
        canvas.alpha_composite(q, (cx, canvas.height - q.height))
        canvas.save(os.path.join(args.out, "boss2_%s.png" % n))
        print(n, q.size)


if __name__ == "__main__":
    main()
