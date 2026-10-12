"""高館の絵（空・中景・地面タイル・足場）を、元絵（Gemini）から、ゲーム用に変換する。

使い方: python tools/make_stage3.py 元絵フォルダ 出力フォルダ
  元絵フォルダに、stage3_sky.jpg・stage3_mid_parts.jpg（部品）・stage3_mid_parts2.jpg（義経堂）・stage3_tiles.jpg・stage3_ledge.jpg（足場）を置く（assets/concept/source/）。
  出力: bg_sky.png・bg_mid.png・tile_00〜05.png・ledge_幅.png（assets/images/stage3/）

  - 空: 山と川の景色。幅 810 に合わせて縮め（縦横の比は保つ）、上を少し切って高さ 270 にする。2ドット角の粗さ、16色
  - 中景: 部品の絵（松2種・ススキと柵・岩。白背景に、離して並べてある）と、義経堂の絵から作る。部品を切り出して、間をあけて並べ、
    いちばん右に義経堂を置く（面の終わりに近づくと、堂が見えてくる）。2ドット角の粗さ、32色。足元の草を、地面の上端に合わせる
  - タイル: 草の上端（tile_01）と、岩・土の下の部分（tile_00・03・04・05）。足場の絵は作らない（草の上端のタイルを並べる）
"""
import os
import sys
from collections import deque

from PIL import Image

SKY_W = 810              # 空の幅（横に流せる余白を作る。毛越寺の空と同じ）
SKY_TOP = 100            # 縮めた空の、上から切り取りはじめる位置（雲の下のほうを残すため、上を少し切る）
CHUNK = 2                # ドットの粗さ（2ドット角。ドット絵基準の、背景の粗さ）
MID_H = 270
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


def split_parts(img, gap=6):
    """白を消した絵を、何も無い縦の列で区切って、部品に分ける（左から順）。各部品は、絵のある範囲だけに切り詰める"""
    a = img.getchannel("A")
    w, h = img.size
    ap = a.load()
    filled = [sum(1 for y in range(h) if ap[x, y]) >= 4 for x in range(w)]   # 点のようなごみは、無いものとして扱う
    parts, start, empty = [], None, 0
    for x in range(w + 1):
        on = x < w and filled[x]
        if on:
            if start is None:
                start = x
            empty = 0
        elif start is not None:
            empty += 1
            if empty >= gap or x == w:
                c = img.crop((start, 0, x - empty + 1, h))
                box = c.getbbox()
                if box and (box[2] - box[0]) * (box[3] - box[1]) > 4000:     # 小さなごみは、捨てる
                    parts.append((c.crop(box), box[3]))                      # (絵, もとの絵での下端の高さ)
                start, empty = None, 0
    return parts


def to_coarse(img, scale, pal):
    """部品を、CHUNK ドット角の粗さで、縮める。色は、共通の少数色に寄せる"""
    w, h = max(1, round(img.width * scale / CHUNK)), max(1, round(img.height * scale / CHUNK))
    rgb = img.convert("RGB").resize((w, h), Image.BOX)
    alpha = img.getchannel("A").resize((w, h), Image.BOX).point(lambda v: 255 if v >= 128 else 0)
    px = rgb.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = min(pal, key=lambda c: sum((u - v) ** 2 for u, v in zip(px[x, y], c)))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out.resize((w * CHUNK, h * CHUNK), Image.NEAREST)


def make_mid(parts_src, shrine_src, out):
    """中景: 部品の絵（松2種・ススキと柵・岩）と、義経堂の絵から作る。部品を、間をあけて並べ、いちばん右に義経堂を置く
    （面の終わりに近づくと、堂が見えてくる）。足元の草の高さを、地面の上端に合わせ、それより下（土の断面）は消す"""
    sheet = Image.open(parts_src).convert("RGB")
    sheet.paste((255, 255, 255), (0, 0, sheet.width, PARTS_TOP))       # 上の見出しの文字を、消す
    parts = split_parts(remove_outer_white(sheet))
    if len(parts) != 4:
        raise SystemExit("部品が4つ見つかりません（%d個）" % len(parts))
    shrine_img = remove_outer_white(Image.open(shrine_src).convert("RGB"))
    box = shrine_img.getbbox()
    shrine = (shrine_img.crop(box), box[3])
    # 色: 全部の部品から、共通の少数色を作る
    strip = Image.new("RGB", (sum(p.width for p, _ in parts + [shrine]), 1))
    data = []
    for p, _ in parts + [shrine]:
        small = p.resize((max(1, p.width // 6), max(1, p.height // 6)), Image.BOX)
        data += [c[:3] for c in small.getdata() if c[3] > 200]
    strip = Image.new("RGB", (len(data), 1))
    strip.putdata(data)
    q = strip.quantize(colors=COLORS_MID, method=Image.MEDIANCUT, dither=Image.NONE).getpalette()[: COLORS_MID * 3]
    pal = [tuple(q[i : i + 3]) for i in range(0, len(q), 3)]

    pine1, pine2, fence, rocks = [(to_coarse(p, MID_SCALE, pal), bottom) for p, bottom in parts]
    hall = (to_coarse(shrine[0], MID_SCALE, pal), shrine[1])
    flip = lambda part: (part[0].transpose(Image.FLIP_LEFT_RIGHT), part[1])    # noqa: E731
    # (部品, 左端, 元絵での草の高さ)。同じ部品が続かないように、種類と向きを変えて並べる
    layout = [
        (pine1, 30, PARTS_GRASS), (fence, 185, PARTS_GRASS), (pine2, 305, PARTS_GRASS), (rocks, 455, PARTS_GRASS),
        (flip(pine1), 565, PARTS_GRASS), (flip(fence), 720, PARTS_GRASS), (flip(pine2), 835, PARTS_GRASS), (flip(rocks), 985, PARTS_GRASS),
        (hall, 1085, SHRINE_GRASS),
    ]
    width = max(x + part[0].width for part, x, _ in layout) + 10
    canvas = Image.new("RGBA", (width + width % 2, MID_H), (0, 0, 0, 0))
    for (img, bottom), x, grass in layout:
        # 元絵の「草の高さ」を、地面の上端（GROUND_LINE の少し上）に合わせる
        y = GROUND_LINE - 4 - (img.height - round((bottom - grass) * MID_SCALE))
        canvas.alpha_composite(img, (x - x % CHUNK, y - y % CHUNK))
    px = canvas.load()
    for y in range(GROUND_LINE, MID_H):         # 地面より下（土の断面）は、消す（穴の上で、土が浮いて見えないように）
        for x in range(canvas.width):
            px[x, y] = (0, 0, 0, 0)
    canvas.save(out, optimize=True)
    return canvas.size


GROUND_LINE = 228        # 中景の、これより下は消す（地面のタイルに隠れる所）
MID_SCALE = 0.29         # 元絵から、中景への縮尺（松の高さが、約150ドットになる）
PARTS_TOP = 78           # 部品の絵の、上の見出し（文字）の高さ。ここまでを、白く塗って消す
PARTS_GRASS = 578        # 部品の絵の、足元の草の高さ（元絵の y）。ここを、地面の上端に合わせる
SHRINE_GRASS = 590       # 義経堂の絵の、手前の草の高さ（元絵の y）


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


LEDGE_H = 22             # 足場の厚み（草も入れて。2ドット角なので、偶数）
LEDGE_WIDTHS = (30, 50, 60, 70)     # 作る足場の幅（面の足場の幅 20・40・50・60 に、左右5ずつ足したもの。config の STONE_PAD）
COLORS_LEDGE = 12


def make_ledges(src, out_dir):
    """足場: 横に長い岩棚の絵（1本）から、幅ごとの足場を作る。絵を引き伸ばさず、**左の端から半分・右の端から半分**を切って、つなぐ
    （短い足場は、両端の丸みだけでできた、レンズの形になる。長い足場は、真ん中の平らな所まで入る）。
    草の乗った上の面は、どの幅でも、端から端まで続く。2ドット角の粗さ"""
    img = remove_outer_white(Image.open(src).convert("RGB"))
    img = img.crop(img.getbbox())
    scale = LEDGE_H / img.height                    # 厚みを LEDGE_H に合わせる縮尺（縦横とも、同じ）
    small = img.resize((max(1, img.width // 6), max(1, img.height // 6)), Image.BOX)
    data = [c[:3] for c in small.getdata() if c[3] > 200]
    strip = Image.new("RGB", (len(data), 1))
    strip.putdata(data)
    q = strip.quantize(colors=COLORS_LEDGE, method=Image.MEDIANCUT, dither=Image.NONE).getpalette()[: COLORS_LEDGE * 3]
    pal = [tuple(q[i : i + 3]) for i in range(0, len(q), 3)]
    sizes = []
    for width in LEDGE_WIDTHS:
        half = min(img.width // 2, round(width / scale / 2))     # 元絵での、片側の長さ
        joined = Image.new("RGBA", (half * 2, img.height), (0, 0, 0, 0))
        joined.paste(img.crop((0, 0, half, img.height)), (0, 0))
        joined.paste(img.crop((img.width - half, 0, img.width, img.height)), (half, 0))
        w, h = width // CHUNK, LEDGE_H // CHUNK
        rgb = joined.convert("RGB").resize((w, h), Image.BOX)
        alpha = joined.getchannel("A").resize((w, h), Image.BOX).point(lambda v: 255 if v >= 128 else 0)
        px = rgb.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = min(pal, key=lambda c: sum((u - v) ** 2 for u, v in zip(px[x, y], c)))
        out = rgb.convert("RGBA")
        out.putalpha(alpha)
        out = out.resize((w * CHUNK, h * CHUNK), Image.NEAREST)
        out.save(os.path.join(out_dir, "ledge_%03d.png" % width))
        sizes.append(out.size)
    return sizes


def clear_white_top(top, rows=4):
    """草の上端のタイルの、上の数行に残った白（元絵の背景）を、透明にする（白い柵のように見えていた）"""
    px = top.load()
    for y in range(min(rows, top.height)):
        for x in range(top.width):
            if min(px[x, y][:3]) >= 150:
                px[x, y] = (0, 0, 0, 0)
    return top


def make_tiles(src, out_dir):
    img = Image.open(src).convert("RGB")
    bs = boxes(img)
    # 並びは、行→列: 0草の上端 1岩 2斜面 / 3岩（苔） 4小さい足場 5土 / 6岩（苔） 7広い足場 8土
    if len(bs) != 9:
        raise SystemExit("タイルが9枚見つかりません（%d枚）: %s" % (len(bs), bs))
    top = fit_width(img, bs[0], 32)                       # 草の上端（幅32、高さは自動）
    clear_white_top(top)
    tiles = {
        0: square_tile(img, bs[1]), 3: square_tile(img, bs[3]),
        4: square_tile(img, bs[6]), 5: square_tile(img, bs[5]),
        2: square_tile(img, bs[8]),
    }
    os.makedirs(out_dir, exist_ok=True)
    top.save(os.path.join(out_dir, "tile_01.png"))
    for i, t in tiles.items():
        t.save(os.path.join(out_dir, f"tile_{i:02d}.png"))
    # 足場は、専用の絵（stage3_ledge.jpg → ledge_幅.png）から作る（make_ledges）。タイルのシートにある岩の塊は、使わない
    return top.size


if __name__ == "__main__":
    src, out = sys.argv[1:3]
    os.makedirs(out, exist_ok=True)
    print("空", make_sky(os.path.join(src, "stage3_sky.jpg"), os.path.join(out, "bg_sky.png")))
    print("中景", make_mid(os.path.join(src, "stage3_mid_parts.jpg"), os.path.join(src, "stage3_mid_parts2.jpg"), os.path.join(out, "bg_mid.png")))
    print("足場", make_ledges(os.path.join(src, "stage3_ledge.jpg"), out))
    print("タイル（上端）", make_tiles(os.path.join(src, "stage3_tiles.jpg"), out))
