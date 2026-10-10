"""Geminiで作ったスプライトシート（白背景・複数コマ）を切り出し、粗いドット絵のコマに変換する。

使い方: python tools/slice_sheet.py シート.jpg 出力フォルダ 名前 [体の高さ(ドット)]
        [--layout 縮尺,左,上,枠幅,枠高] [--only 6-10] [--start 14] [--gain 1.4] [--per-row]
  --layout: 別のシートで変換済みのコマと同じ枠・頭の位置にそろえる（変換時に LAYOUT として表示される）。
            縮尺を 0 にすると、このシートの体の高さから縮尺を決める（シートごとに元絵の大きさが違うとき）
  --per-row: 行ごとに体の高さをそろえる（元絵の行ごとにキャラの大きさが違うとき）
  --gain:   色の明るさの倍率（元絵が暗いシート用）
  --only:   指定したコマ番号（0始まり、行→列の順）だけを変換する。--start は出力する番号の開始値
  - 白い背景を外側から塗りつぶして透過にする
  - 連結成分でコマを分ける。見出しの文字（黒い小さな塊）は捨て、斬撃・火花などは近いコマに付ける
  - 全コマ共通の縮尺（体の高さの中央値が指定のドット数）で縮小し、固定パレットに減色、黒の輪郭を付ける
  - 頭の位置（左右）と足元（上下）をそろえ、全コマ共通の大きさの枠に置く
出力: 出力フォルダ/名前_00.png ...（行→列の順）と、確認用の 名前_sheet.png（4倍）
"""
import collections
import os
import statistics
import sys

from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
from pixelize import add_outline, nearest  # noqa: E402

TARGET_H = 40
BIG_AREA = 5000       # これ以上の塊をキャラ本体とみなす（元絵のピクセル数）
ATTACH_DIST = 80      # 斬撃・火花をキャラに付ける最大距離（元絵のピクセル）
SMALL_AREA = 400      # これ未満で無彩色の塊は、文字のかけらとして捨てる
GRAY_SAT = 40
GROUND_RUN = 80       # 足元の、これ以上つながった黒い横線は地面の線として消す（元絵のピクセル）
GROUND_ROWS = 6       # 足元から何行まで調べるか
FOOT_WHITE = 0.22     # 本体の下からこの割合の範囲に残った白（足の間の背景）は消す
DARK_TEXT = 70        # 平均の明るさがこれ未満の小さな塊は文字として捨てる


def remove_white_bg(img):
    """画像の外周から、白に近い画素を塗りつぶして透過にする（内側の白い鼻や帯は残る）"""
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    seen = bytearray(w * h)
    dq = collections.deque()
    for x in range(w):
        dq.append((x, 0))
        dq.append((x, h - 1))
    for y in range(h):
        dq.append((0, y))
        dq.append((w - 1, y))
    while dq:
        x, y = dq.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or seen[y * w + x]:
            continue
        r, g, b, _ = px[x, y]
        if not (r > 225 and g > 225 and b > 225):
            continue
        seen[y * w + x] = 1
        px[x, y] = (0, 0, 0, 0)
        dq.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    # 縁に残る白とのにじみを1px削る
    img.putalpha(img.getchannel("A").filter(ImageFilter.MinFilter(3)))
    return img


def components(img):
    """不透明画素の連結成分（8近傍）を返す"""
    w, h = img.size
    px = img.load()
    seen = bytearray(w * h)
    comps = []
    for y0 in range(h):
        for x0 in range(w):
            if not px[x0, y0][3] or seen[y0 * w + x0]:
                continue
            pts, dq = [], collections.deque([(x0, y0)])
            seen[y0 * w + x0] = 1
            while dq:
                x, y = dq.popleft()
                pts.append((x, y))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and px[nx, ny][3]:
                            seen[ny * w + nx] = 1
                            dq.append((nx, ny))
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            sample = pts[:: max(1, len(pts) // 200)]
            bright = sum(sum(px[x, y][:3]) / 3 for x, y in sample) / len(sample)
            sat = sum(max(px[x, y][:3]) - min(px[x, y][:3]) for x, y in sample) / len(sample)
            comps.append({"pts": pts, "box": (min(xs), min(ys), max(xs) + 1, max(ys) + 1), "bright": bright, "sat": sat})
    return comps


def box_dist(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return max(dx, dy)


def group_frames(comps):
    """大きい塊をコマの本体にし、斬撃・火花を近い本体に付ける。文字（暗い小塊）は捨てる"""
    bigs = [c for c in comps if len(c["pts"]) >= BIG_AREA]
    frames = [{"main": c, "parts": [c]} for c in bigs]
    for c in comps:
        if c in bigs or c["bright"] < DARK_TEXT:
            continue
        if len(c["pts"]) < SMALL_AREA and c["sat"] < GRAY_SAT:
            continue  # 見出し文字のかけら（小さく無彩色）。火花は彩度があるので残る
        best = min(frames, key=lambda f: box_dist(c["box"], f["main"]["box"]))
        if box_dist(c["box"], best["main"]["box"]) <= ATTACH_DIST:
            best["parts"].append(c)
    # 行→列の順に並べる
    frames.sort(key=lambda f: (f["main"]["box"][1] + f["main"]["box"][3]) / 2)
    rows, last = [], None
    for f in frames:
        cy = (f["main"]["box"][1] + f["main"]["box"][3]) / 2
        if last is None or cy - last > 80:
            rows.append([])
        rows[-1].append(f)
        last = cy
    for r in rows:
        r.sort(key=lambda f: f["main"]["box"][0])
    return rows


def frame_image(src, frame):
    """本体と付属の塊だけを抜き出した RGBA 画像と、本体の bbox（切り出し内の座標）を返す"""
    boxes = [c["box"] for c in frame["parts"]]
    x0, y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
    x1, y1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
    out = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    sp, op = src.load(), out.load()
    for c in frame["parts"]:
        for x, y in c["pts"]:
            op[x - x0, y - y0] = sp[x, y]
    mb = (frame["main"]["box"][0] - x0, frame["main"]["box"][1] - y0,
          frame["main"]["box"][2] - x0, frame["main"]["box"][3] - y0)
    # 足の間などに閉じ込められた背景の白を消す（鼻や帯の白は上側にあるので残る）
    foot_top = mb[3] - round((mb[3] - mb[1]) * FOOT_WHITE)
    for y in range(foot_top, out.height):
        for x in range(out.width):
            r, g, b, a = op[x, y]
            if a and r > 225 and g > 225 and b > 225:
                op[x, y] = (0, 0, 0, 0)
    mb = remove_ground_line(out, frame, (x0, y0), mb)
    return out, mb


def remove_ground_line(out, frame, origin, mb):
    """本体の足元にある、足より横に長い黒い線を消し、本体の下端 (mb) を引き直して返す"""
    op = out.load()
    ox, oy = origin
    # 本体の下端から数行だけ調べる。1行が1本の長い黒い連続なら地面の線
    for y in range(mb[3] - 1, max(mb[1], mb[3] - GROUND_ROWS) - 1, -1):
        xs = [x for x in range(out.width) if op[x, y][3]]
        if not xs:
            continue
        runs, start = [], xs[0]
        for a, b in zip(xs, xs[1:] + [None]):
            if b != a + 1:
                runs.append((start, a))
                start = b
        long_black = [r for r in runs if r[1] - r[0] + 1 >= GROUND_RUN
                      and all(sum(op[x, y][:3]) < 180 for x in range(r[0], r[1] + 1))]
        if not long_black:
            break
        for r in long_black:
            for x in range(r[0], r[1] + 1):
                op[x, y] = (0, 0, 0, 0)
    # 本体の下端を引き直す
    bottom = mb[1]
    for x, y in frame["main"]["pts"]:
        if op[x - ox, y - oy][3] and y - oy + 1 > bottom:
            bottom = y - oy + 1
    return (mb[0], mb[1], mb[2], bottom)


def to_pixels(img, scale, gain=1.0):
    w, h = max(1, round(img.width * scale)), max(1, round(img.height * scale))
    small = img.resize((w, h), Image.BOX)
    alpha = small.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
    rgb = small.convert("RGB")
    p = rgb.load()
    for y in range(h):
        for x in range(w):
            c = p[x, y]
            p[x, y] = nearest(tuple(min(255, round(v * gain)) for v in c))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return add_outline(out)


def main(src_path, out_dir, name, target_h=TARGET_H, layout=None, only=None, start=0, gain=1.0, per_row=False):
    src = remove_white_bg(Image.open(src_path))
    rows = group_frames(components(src))
    print("コマ数:", [len(r) for r in rows])
    items = [(ri, f) for ri, r in enumerate(rows) for f in r]

    if layout and layout[0] > 0:
        scale = layout[0]
    else:
        scale = target_h / statistics.median(f["main"]["box"][3] - f["main"]["box"][1] for _, f in items)
    print("縮尺: 元絵の1ドット相当 = %.1fpx" % (1 / scale))
    if only is not None:
        items = [items[i] for i in only]
        rows = [[f for _, f in items]]
        if not (layout and layout[0] > 0):
            # 選んだコマだけの高さの中央値で縮尺を決める（行ごとに元絵の大きさが違うとき用）
            scale = target_h / statistics.median(f["main"]["box"][3] - f["main"]["box"][1] for _, f in items)
            print("縮尺（選んだコマ）: 元絵の1ドット相当 = %.1fpx" % (1 / scale))

    if per_row:
        # 元絵は行ごとにキャラの大きさが違うことがある。行ごとに体の高さをそろえる
        row_med = {}
        for ri in {r for r, _ in items}:
            row_med[ri] = statistics.median(f["main"]["box"][3] - f["main"]["box"][1] for r, f in items if r == ri)
        print("行ごとの高さの中央値:", {k: round(v) for k, v in sorted(row_med.items())})

    placed = []  # (行, 画像, 頭のx, 足元のy)
    for ri, f in items:
        img, mb = frame_image(src, f)
        sc = target_h / row_med[ri] if per_row else scale
        px = to_pixels(img, sc, gain)
        # 頭の位置: 本体の上から30%の画素の左右の平均。足元: 本体の下端（輪郭1px分をずらす）
        top_h = max(1, round((mb[3] - mb[1]) * 0.3))
        a = img.getchannel("A").load()
        xs = [x for y in range(mb[1], mb[1] + top_h) for x in range(mb[0], mb[2]) if a[x, y]]
        head_x = round(sum(xs) / len(xs) * sc) + 1
        foot_y = round(mb[3] * sc) + 1
        placed.append((ri, px, head_x, foot_y))

    left = max(p[2] for p in placed)
    right = max(p[1].width - p[2] for p in placed)
    up = max(p[3] for p in placed)
    down = max(p[1].height - p[3] for p in placed)
    cw, ch = left + right, up + down
    cw, ch = (cw + 7) // 8 * 8, (ch + 7) // 8 * 8  # 8の倍数に切り上げ
    if layout:
        if left > layout[1] or up > layout[2] or right > layout[3] - layout[1] or down > layout[4] - layout[2]:
            print("警告: 指定の枠からはみ出すコマがあります（左%d/%d 上%d/%d 右%d/%d 下%d/%d）" % (
                left, layout[1], up, layout[2], right, layout[3] - layout[1], down, layout[4] - layout[2]))
        left, up, cw, ch = layout[1], layout[2], layout[3], layout[4]
        down = ch - up
    print("枠:", cw, "x", ch)
    print("LAYOUT %r,%d,%d,%d,%d" % (scale, left, up, cw, ch))

    os.makedirs(out_dir, exist_ok=True)
    frames = []
    for i, (ri, px, hx, fy) in enumerate(placed):
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.paste(px, (left - hx, up - fy + (ch - up - down)), px)
        canvas.save(os.path.join(out_dir, f"{name}_{i + start:02d}.png"))
        frames.append(canvas)

    S, G = 4, 8
    per_row = max(len(r) for r in rows)
    sheet = Image.new("RGB", (per_row * (cw * S + G) + G, len(rows) * (ch * S + G) + G), (92, 148, 252))
    i = 0
    for ri, row in enumerate(rows):
        for ci in range(len(row)):
            big = frames[i].resize((cw * S, ch * S), Image.NEAREST)
            sheet.paste(big, (G + ci * (cw * S + G), G + ri * (ch * S + G)), big)
            i += 1
    sheet.save(os.path.join(out_dir, f"{name}_sheet.png"))


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out_dir")
    ap.add_argument("name")
    ap.add_argument("target_h", nargs="?", type=int, default=TARGET_H)
    ap.add_argument("--layout")
    ap.add_argument("--only")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--gain", type=float, default=1.0)
    ap.add_argument("--per-row", action="store_true")
    a = ap.parse_args()
    lay = [float(a.layout.split(",")[0])] + [int(v) for v in a.layout.split(",")[1:]] if a.layout else None
    only = None
    if a.only:
        lo, _, hi = a.only.partition("-")
        only = list(range(int(lo), int(hi or lo) + 1))
    main(a.src, a.out_dir, a.name, a.target_h, lay, only, a.start, a.gain, a.per_row)
