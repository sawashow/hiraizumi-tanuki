"""手裏剣シート（葉の回転4コマ＋命中の破片3コマ）を、小さな枠のドット絵に変換する。

使い方: python tools/make_shuriken.py シート.jpg 出力フォルダ [葉の大きさ(ドット)] [枠]
  - シートの上から1行目が葉、2行目が破片（行の位置は白でない画素の分布で自動検出）
  - 葉も破片も同じ縮尺（葉の最大の辺が指定のドット数）。色は葉から取った緑中心のパレットに寄せる
出力: shuriken_00..03.png, hit_00..02.png, shuriken_sheet.png（8倍）
"""
import os
import sys

from PIL import Image

BG_MIN = 235  # 全チャンネルがこれより大きい画素は背景


def mask_of(img):
    w, h = img.size
    px = img.load()
    return [[min(px[x, y]) < BG_MIN for x in range(w)] for y in range(h)]


def runs(flags, merge_gap=0):
    out, start, last = [], None, None
    for i, f in enumerate(flags):
        if f:
            if start is None:
                start = i
            elif merge_gap and last is not None and i - last > merge_gap:
                out.append((start, last + 1))
                start = i
            last = i
    if start is not None:
        out.append((start, last + 1))
    return out


def split(img, gap_y=25, gap_x=20):
    """行 → 列の順に bbox を返す（散らばる破片は gap_x を大きめに取る）"""
    m = mask_of(img)
    h, w = len(m), len(m[0])
    rows = runs([any(m[y]) for y in range(h)], gap_y)
    rows = [r for r in rows if r[1] - r[0] > 20][:2]  # 下のキャラの行は使わない
    boxes = []
    for ri, (y0, y1) in enumerate(rows):
        gx = gap_x if ri == 0 else 42
        cols = runs([any(m[y][x] for y in range(y0, y1)) for x in range(w)], gx)
        boxes.append([(x0, y0, x1, y1) for x0, x1 in cols if x1 - x0 > 8])
    return boxes


def palette_from(crops, n=7):
    px = [c.getpixel((x, y)) for c in crops for y in range(c.height) for x in range(c.width)
          if min(c.getpixel((x, y))) < BG_MIN]
    strip = Image.new("RGB", (len(px), 1))
    strip.putdata(px)
    q = strip.quantize(colors=n, method=Image.MEDIANCUT, dither=Image.NONE)
    pal = q.getpalette()[: n * 3]
    return [tuple(pal[i : i + 3]) for i in range(0, len(pal), 3)]


def to_dots(crop, scale, pal):
    w, h = max(1, round(crop.width * scale)), max(1, round(crop.height * scale))
    rgba = crop.convert("RGBA")
    p = rgba.load()
    for y in range(crop.height):
        for x in range(crop.width):
            if min(p[x, y][:3]) >= BG_MIN:
                p[x, y] = (255, 255, 255, 0)
    small = rgba.resize((w, h), Image.BOX)
    a = small.getchannel("A").point(lambda v: 255 if v >= 110 else 0)
    rgb = small.convert("RGB")
    q = rgb.load()
    for y in range(h):
        for x in range(w):
            q[x, y] = min(pal, key=lambda c: sum((u - v) ** 2 for u, v in zip(q[x, y], c)))
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


def main(src, out_dir, leaf_dots=22, canvas=24):
    img = Image.open(src).convert("RGB")
    rows = split(img)
    leaves = [img.crop(b) for b in rows[0]]
    hits = [img.crop(b) for b in rows[1]]
    print("葉:", len(leaves), "破片:", len(hits))
    scale = leaf_dots / max(max(c.size) for c in leaves)
    pal = palette_from(leaves)
    os.makedirs(out_dir, exist_ok=True)
    frames = []
    for name, crops in (("shuriken", leaves), ("hit", hits)):
        for i, c in enumerate(crops):
            d = to_dots(c, scale, pal)
            cv = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
            cv.paste(d, ((canvas - d.width) // 2, (canvas - d.height) // 2), d)
            cv.save(os.path.join(out_dir, f"{name}_{i:02d}.png"))
            frames.append(cv)
    S, G = 8, 8
    sheet = Image.new("RGB", (len(frames) * (canvas * S + G) + G, canvas * S + 2 * G), (92, 148, 252))
    for i, f in enumerate(frames):
        b = f.resize((canvas * S, canvas * S), Image.NEAREST)
        sheet.paste(b, (G + i * (canvas * S + G), G), b)
    sheet.save(os.path.join(out_dir, "shuriken_sheet.png"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2],
         int(sys.argv[3]) if len(sys.argv) > 3 else 22,
         int(sys.argv[4]) if len(sys.argv) > 4 else 24)
