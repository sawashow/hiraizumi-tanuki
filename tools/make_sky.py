"""遠景（空・月・山）の絵を、480×270 の画面に合わせて変換する。

使い方: python tools/make_sky.py 元絵.jpg 出力.png [月の縮小率=0.5] [色数=28]
  - 月（黄みがかった白い円）を見つけて消し、空の帯で埋めてから、縮小率で小さくして同じ中心に置き直す
  - 高さ 270 に合わせて縮小し、色数を絞る（月の色が潰れないよう、多めの色数にする）
"""
import sys

from PIL import Image

H = 270
MOON_COLORS = 4


def is_moon(c):
    r, g, b = c
    return r > 190 and g > 170 and b < 190 and r - b > 40


def find_moon(img):
    """月の画素の外接矩形と中心・半径を返す"""
    w, h = img.size
    px = img.load()
    xs, ys = [], []
    for y in range(h // 2):  # 月は上半分にある
        for x in range(w):
            if is_moon(px[x, y]):
                xs.append(x)
                ys.append(y)
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    return (x0, y0, x1 + 1, y1 + 1), ((x0 + x1) / 2, (y0 + y1) / 2), (x1 - x0 + 1) / 2


def main(src, dst, shrink=0.5, colors=28):
    img = Image.open(src).convert("RGB")
    (x0, y0, x1, y1), (cx, cy), r = find_moon(img)
    print("月: 中心(%.0f, %.0f) 半径 %.0f px" % (cx, cy, r))
    pad = 6
    box = (x0 - pad, y0 - pad, x1 + pad, y1 + pad)
    moon = img.crop(box).convert("RGBA")
    mp = moon.load()
    # 月の円の外は透明にする
    for y in range(moon.height):
        for x in range(moon.width):
            if (x + box[0] - cx) ** 2 + (y + box[1] - cy) ** 2 > (r + 1) ** 2:
                mp[x, y] = (0, 0, 0, 0)
    # 月のあった場所を、同じ高さの空の帯（月の左側の列）で埋める
    px = img.load()
    shift = (box[2] - box[0]) + 20
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            px[x, y] = px[x - shift, y]
    # 小さくした月を、同じ中心に置き直す
    small = moon.resize((max(1, round(moon.width * shrink)), max(1, round(moon.height * shrink))), Image.BOX)
    sp = small.load()
    for y in range(small.height):
        for x in range(small.width):
            sp[x, y] = sp[x, y][:3] + (255 if sp[x, y][3] >= 128 else 0,)
    img = img.convert("RGBA")
    img.paste(small, (round(cx - small.width / 2), round(cy - small.height / 2)), small)

    w = round(img.width * H / img.height)
    out = img.convert("RGB").resize((w, H), Image.BOX)
    # 月の色は面積が小さく、自動の減色だと橙に潰れるため、専用に確保して空の色と合わせる
    moon_px = [sp[x, y][:3] for y in range(small.height) for x in range(small.width) if sp[x, y][3]]
    strip = Image.new("RGB", (len(moon_px), 1))
    strip.putdata(moon_px)
    mq = strip.quantize(colors=MOON_COLORS, method=Image.MEDIANCUT, dither=Image.NONE)
    mpal = [tuple(mq.getpalette()[i : i + 3]) for i in range(0, MOON_COLORS * 3, 3)]
    sky = out.quantize(colors=colors - MOON_COLORS, method=Image.MEDIANCUT, dither=Image.NONE)
    spal = [tuple(sky.getpalette()[i : i + 3]) for i in range(0, (colors - MOON_COLORS) * 3, 3)]
    pal = spal + mpal
    op = out.load()
    cache = {}
    for y in range(H):
        for x in range(w):
            c = op[x, y]
            if c not in cache:
                cache[c] = min(pal, key=lambda q: sum((u - v) ** 2 for u, v in zip(c, q)))
            op[x, y] = cache[c]
    out.save(dst)
    print("出力:", out.size)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2],
         float(sys.argv[3]) if len(sys.argv) > 3 else 0.5,
         int(sys.argv[4]) if len(sys.argv) > 4 else 28)
