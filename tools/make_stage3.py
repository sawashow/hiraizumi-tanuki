"""高館の絵（空・中景・地面タイル・足場）を、元絵（Gemini）から、ゲーム用に変換する。

使い方: python tools/make_stage3.py 元絵フォルダ 出力フォルダ
  元絵フォルダに、stage3_sky.jpg・stage3_mid.jpg・stage3_tiles.jpg を置く（assets/concept/source/）。
  出力: bg_sky.png・bg_mid.png・tile_00〜05.png・stone_0〜2.png（assets/images/stage3/）

  - 空: 山と川の景色。幅 810 に合わせて縮め（縦横の比は保つ）、上を少し切って高さ 270 にする。2ドット角の粗さ、16色
  - 中景: 義経堂の絵（白背景）。そのままだと 1 画面ぶんしかないので、松・草・柵を切り出して、間をあけて並べ、
    いちばん右に義経堂を置く（面の終わりに近づくと、堂が見えてくる）。足元が地面に重なるように、下げて置く
  - タイル: 草の上端（tile_01）と、岩・土の下の部分（tile_00・03・04・05）。足場は、岩の塊（stone_0〜2）
"""
import os
import sys
from collections import deque

from PIL import Image

SKY_W = 810              # 空の幅（横に流せる余白を作る。毛越寺の空と同じ）
SKY_TOP = 100            # 縮めた空の、上から切り取りはじめる位置（雲の下のほうを残すため、上を少し切る）
CHUNK = 2                # ドットの粗さ（2ドット角。ドット絵基準の、背景の粗さ）
MID_H = 270
MID_DROP = 60            # 中景を下げる量（義経堂の足元を、地面の上端のあたり（y 220）に合わせる）
MID_W = 1500
COLORS_SKY = 16
COLORS_MID = 32
COLORS_TILE = 16
WHITE = 225              # これより明るい（全チャンネル）なら、背景の白


def make_sky(src, out):
    """空: 横 SKY_W に合わせて縮め（縦横の比は保つ）、下の 270 を残す。ドットを粗く（CHUNK ドット角）して、色数を絞る"""
    im = Image.open(src).convert("RGB")
    h = round(im.height * SKY_W / im.width)
    im = im.resize((SKY_W, h), Image.LANCZOS).crop((0, SKY_TOP, SKY_W, SKY_TOP + 270))      # 雲の下半分と、山・川を残す
    small = im.resize((SKY_W // CHUNK, 270 // CHUNK), Image.BOX)
    im = small.resize((SKY_W, 270), Image.NEAREST)                                 # 2ドット角の、粗いドットにする
    im = im.quantize(colors=COLORS_SKY, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    im.save(out, optimize=True)
    return im.size


def remove_outer_white(im):
    """外側とつながっている白だけを透明にする（幟や紙の、囲まれた白は残す）"""
    w, h = im.size
    px = im.load()
    white = [[all(c >= WHITE for c in px[x, y][:3]) for x in range(w)] for y in range(h)]
    seen = [[False] * w for _ in range(h)]
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            if white[y][x] and not seen[y][x]:
                seen[y][x] = True
                dq.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if white[y][x] and not seen[y][x]:
                seen[y][x] = True
                dq.append((x, y))
    while dq:
        x, y = dq.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and white[ny][nx] and not seen[ny][nx]:
                seen[ny][nx] = True
                dq.append((nx, ny))
    # 縁のにじみ（白に近い画素）を、外側の白に接していれば、1画素ぶん削る
    out = Image.new("RGBA", im.size)
    op = out.load()
    for y in range(h):
        for x in range(w):
            near = any(0 <= x + dx < w and 0 <= y + dy < h and seen[y + dy][x + dx]
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if seen[y][x] or (near and min(px[x, y][:3]) >= 190):
                op[x, y] = (0, 0, 0, 0)
            else:
                op[x, y] = px[x, y][:3] + (255,)
    return out


def make_mid(src, out):
    big = remove_outer_white(Image.open(src).convert("RGB"))
    scale = MID_H / big.height
    w = round(big.width * scale)
    rgb = big.convert("RGB").resize((w, MID_H), Image.LANCZOS)
    alpha = big.getchannel("A").resize((w, MID_H), Image.BOX).point(lambda v: 255 if v >= 140 else 0)
    # 色数を絞る（透明な所は、絞る色に混ぜない）
    q = rgb.quantize(colors=COLORS_MID, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    scene = q.convert("RGBA")
    scene.putalpha(alpha)

    def piece(x0, x1, flip=False):
        c = scene.crop((round(x0 * scale), 0, round(x1 * scale), MID_H))
        return c.transpose(Image.FLIP_LEFT_RIGHT) if flip else c

    # 元絵の横位置（ピクセル）で切り出す: 松と灯籠 / 草と柵 / 義経堂まで全部 / 右端の崖
    pine = (650, 905)
    grass = (930, 1150)
    shrine = (0, 1040)
    cliff = (1100, big.width)
    layout = [
        (pine, False, 40), (grass, True, 190), (pine, True, 330), (grass, False, 480),
        (pine, False, 640), (grass, True, 800), (pine, True, 940), (grass, False, 1080),
        (shrine, False, 1060), (cliff, False, None),
    ]
    canvas = Image.new("RGBA", (MID_W, MID_H), (0, 0, 0, 0))
    x_end = 0
    for (x0, x1), flip, at in layout:
        p = piece(x0, x1, flip)
        if at is None:
            at = x_end
        canvas.alpha_composite(p, (at, MID_DROP))
        x_end = at + p.width
    canvas = canvas.crop((0, 0, x_end, MID_H))
    canvas.save(out, optimize=True)
    return canvas.size


def boxes(img, bg=235, row_gap=30):
    """白背景のシートから、絵の外接矩形を、行→列の順に返す"""
    w, h = img.size
    px = img.load()
    m = [[min(px[x, y][:3]) < bg for x in range(w)] for y in range(h)]

    def runs(flags, gap):
        out, start, last = [], None, None
        for i, f in enumerate(flags):
            if f:
                if start is None:
                    start = i
                elif i - last > gap:
                    out.append((start, last + 1))
                    start = i
                last = i
        if start is not None:
            out.append((start, last + 1))
        return out

    res = []
    for y0, y1 in [r for r in runs([any(m[y]) for y in range(h)], row_gap) if r[1] - r[0] > 40]:
        for x0, x1 in [c for c in runs([any(m[y][x] for y in range(y0, y1)) for x in range(w)], 8) if c[1] - c[0] > 40]:
            ys = [y for y in range(y0, y1) if any(m[y][x] for x in range(x0, x1))]
            res.append((x0, ys[0], x1, ys[-1] + 1))
    return res


def square_tile(img, box, edge=6, size=32):
    """絵の中央を正方形に切り出して、size に縮める（ぎざぎざの縁を、数ドット削る）"""
    x0, y0, x1, y1 = box
    s = min(x1 - x0, y1 - y0) - 2 * edge
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    c = img.crop((cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2)).resize((size, size), Image.BOX)
    return c.quantize(colors=COLORS_TILE, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGBA")


def fit_width(img, box, width, colors=COLORS_TILE):
    c = img.crop(box)
    h = round(c.height * width / c.width)
    c = c.resize((width, h), Image.BOX)
    return c.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGBA")


def stone(img, box, width, keep):
    """足場の岩: 上の keep の割合だけを使い（厚みを抑える）、まわりの白を透明にして、幅 width に縮める"""
    x0, y0, x1, y1 = box
    c = remove_outer_white(img.crop((x0 - 3, y0 - 3, x1 + 3, y0 + round((y1 - y0) * keep))))
    h = round(c.height * width / c.width)
    rgb = c.convert("RGB").resize((width, h), Image.BOX).quantize(colors=COLORS_TILE, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGBA")
    rgb.putalpha(c.getchannel("A").resize((width, h), Image.BOX).point(lambda v: 255 if v >= 140 else 0))
    return rgb


def make_tiles(src, out_dir):
    img = Image.open(src).convert("RGB")
    bs = boxes(img)
    # 並びは、行→列: 0草の上端 1岩 2斜面 / 3岩（苔） 4小さい足場 5土 / 6岩（苔） 7広い足場 8土
    if len(bs) != 9:
        raise SystemExit("タイルが9枚見つかりません（%d枚）: %s" % (len(bs), bs))
    top = fit_width(img, bs[0], 32)                       # 草の上端（幅32、高さは自動）
    tiles = {
        0: square_tile(img, bs[1]), 3: square_tile(img, bs[3]),
        4: square_tile(img, bs[6]), 5: square_tile(img, bs[5]),
        2: square_tile(img, bs[8]),
    }
    os.makedirs(out_dir, exist_ok=True)
    top.save(os.path.join(out_dir, "tile_01.png"))
    for i, t in tiles.items():
        t.save(os.path.join(out_dir, f"tile_{i:02d}.png"))
    stones = [stone(img, bs[4], 45, 0.62), stone(img, bs[7], 48, 0.55)]
    stones.append(stones[0].transpose(Image.FLIP_LEFT_RIGHT))
    for i, s in enumerate(stones):
        s.save(os.path.join(out_dir, f"stone_{i}.png"))
    return top.size, [s.size for s in stones]


if __name__ == "__main__":
    src, out = sys.argv[1:3]
    os.makedirs(out, exist_ok=True)
    print("空", make_sky(os.path.join(src, "stage3_sky.jpg"), os.path.join(out, "bg_sky.png")))
    print("中景", make_mid(os.path.join(src, "stage3_mid.jpg"), os.path.join(out, "bg_mid.png")))
    print("タイル（上端・足場）", make_tiles(os.path.join(src, "stage3_tiles.jpg"), out))
