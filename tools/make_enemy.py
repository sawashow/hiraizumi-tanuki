"""敵のスプライトシート（白背景・動きごとに横一列）を、ゲーム用のコマに変換する。

使い方（例）:
  python tools/make_enemy.py シート.jpg assets/images/enemies ochimusha \\
      --names walk,stance,death --rows 0,1,2 --gaps 40,40,40 --anchors head,head,bbox \\
      --target-h 44 --valign bottom

  - 白い背景を外から塗りつぶして透過にする
  - 見出しの文字（無彩色で暗い小さな塊）と、足元の長い黒い横線（地面の線）を消す
  - 行を上から検出し、--rows で使う行を選ぶ（下に描き足された見本のキャラなどを除く）
  - 全コマ同じ縮尺（1行目のコマの高さの中央値が --target-h ドット）。色は共通の少数色に寄せる
  - 全コマ同じ大きさの枠に置く。横の基準は、head=頭の位置 / bbox=絵の中心。縦は、bottom=足元 / center=中心
出力: 出力フォルダ/名前_動き_番号.png と、確認用の 名前_sheet.png（4倍）
"""
import argparse
import os
import statistics
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from make_shuriken import runs  # noqa: E402
from slice_sheet import components, remove_white_bg  # noqa: E402

LINE_RUN = 300     # これ以上、横に暗い画素が続く行は、地面の線として消す（元絵のピクセル）
TEXT_BRIGHT = 120  # 無彩色で、これより暗い塊は、文字として消す
TEXT_SAT = 22      # 文字は、ほぼ真っ黒（RGBの差が小さい）。紺や藍の敵の体は、少し色がついているので残る
TEXT_MAX_H = 90    # 文字の1つ1つの塊の高さの上限（元絵のピクセル）
ROW_GAP = 8        # 行を分ける、縦の隙間（元絵のピクセル）


def clean(img):
    """地面の線と文字を消す"""
    px = img.load()
    w, h = img.size

    def dark(x, y):
        return px[x, y][3] and sum(px[x, y][:3]) / 3 < 110

    # 1) 足元の地面の線: 横に長く続く暗い画素で、真下が空いているもの（暗い鎧の下端は、これほど長くない）
    for y in range(h - 2, -1, -1):   # 下の行から順に消す（線が数行の厚みでも、上へ向かって消える）
        x = 0
        while x < w:
            if dark(x, y):
                x0 = x
                while x < w and dark(x, y):
                    x += 1
                if x - x0 >= LINE_RUN:
                    below = sum(1 for xx in range(x0, x) if not px[xx, y + 1][3])
                    if below >= (x - x0) * 0.8 or all(not px[xx, y + 1][3] for xx in range(x0, min(x, x0 + 20))):
                        for xx in range(x0, x):
                            px[xx, y] = (0, 0, 0, 0)
            else:
                x += 1
    # 2) 文字: 無彩色の小さな塊（色のついたキャラの体や、羽根は、残る）
    for c in components(img):
        pts = c["pts"]
        sample = pts[:: max(1, len(pts) // 300)]
        gray = sum(1 for x, y in sample if max(px[x, y][:3]) - min(px[x, y][:3]) < TEXT_SAT)
        ys = [y for _, y in pts]
        if gray / len(sample) >= 0.7 and max(ys) - min(ys) < TEXT_MAX_H and len(pts) < 3000:
            for x, y in pts:
                px[x, y] = (0, 0, 0, 0)
    return img


def detect_rows(img, gaps):
    a = img.getchannel("A").load()
    w, h = img.size
    rows = runs([any(a[x, y] for x in range(w)) for y in range(h)], ROW_GAP)
    out = []
    for (y0, y1) in rows:
        if y1 - y0 < 60:   # 見出しの文字の取り残しなど、背の低い行は捨てる
            continue
        out.append((y0, y1))
    return out


def frames_in_row(img, y0, y1, gap):
    a = img.getchannel("A").load()
    w, _ = img.size
    cols = runs([any(a[x, y] for y in range(y0, y1)) for x in range(w)], gap)
    boxes = []
    for x0, x1 in cols:
        ys = [y for y in range(y0, y1) if any(a[x, y] for x in range(x0, x1))]
        if x1 - x0 >= 6 and ys:
            boxes.append((x0, ys[0], x1, ys[-1] + 1))
    return boxes


def palette_from(crops, n):
    px = [c.getpixel((x, y))[:3] for c in crops for y in range(c.height) for x in range(c.width)
          if c.getpixel((x, y))[3]]
    strip = Image.new("RGB", (len(px), 1))
    strip.putdata(px)
    q = strip.quantize(colors=n, method=Image.MEDIANCUT, dither=Image.NONE)
    pal = q.getpalette()[: n * 3]
    return [tuple(pal[i : i + 3]) for i in range(0, len(pal), 3)]


def to_dots(crop, scale, pal):
    w, h = max(1, round(crop.width * scale)), max(1, round(crop.height * scale))
    small = crop.resize((w, h), Image.BOX)
    alpha = small.getchannel("A").point(lambda v: 255 if v >= 110 else 0)
    rgb = small.convert("RGB")
    q = rgb.load()
    for y in range(h):
        for x in range(w):
            q[x, y] = min(pal, key=lambda c: sum((u - v) ** 2 for u, v in zip(q[x, y], c)))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def add_rim(img, color):
    """不透明な画素に隣り合う透明な画素を、指定の色にする（外側に1ドット広がる）"""
    w, h = img.size
    out = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    out.paste(img, (1, 1))
    src = out.copy()
    sp, op = src.load(), out.load()
    for y in range(out.height):
        for x in range(out.width):
            if sp[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < out.width and 0 <= ny < out.height and sp[nx, ny][3]:
                    op[x, y] = color + (255,)
                    break
    return out


def anchor_x(crop, mode, scale):
    if mode == "bbox":
        return round(crop.width * scale / 2)
    a = crop.getchannel("A").load()
    top = max(1, round(crop.height * 0.3))
    xs = [x for y in range(top) for x in range(crop.width) if a[x, y]]
    return round((sum(xs) / len(xs)) * scale) if xs else round(crop.width * scale / 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out_dir")
    ap.add_argument("name")
    ap.add_argument("--names", required=True)
    ap.add_argument("--rows", required=True)
    ap.add_argument("--gaps", required=True)
    ap.add_argument("--anchors", required=True)
    ap.add_argument("--target-h", type=float, required=True)
    ap.add_argument("--valign", choices=["bottom", "center"], default="bottom")
    ap.add_argument("--colors", type=int, default=20)
    ap.add_argument("--gain", type=float, default=1.0)
    ap.add_argument("--rim", default="", help="暗い敵を背景から浮かせる、外側の縁取りの色 R,G,B（1ドット）")
    ap.add_argument("--foot-white", default="", help="足の間に残った白を消す動き。番号:しきい値 をコンマ区切り（例 0:195,2:232）。番号は --names の順で0始まり")
    a = ap.parse_args()
    names = a.names.split(",")
    rows_sel = [int(v) for v in a.rows.split(",")]
    gaps = [int(v) for v in a.gaps.split(",")]
    anchors = a.anchors.split(",")

    img = remove_white_bg(clean(remove_white_bg(Image.open(a.src))), erode=False)   # 線を消したあと、足の間に残った白をもう一度消す
    rows = detect_rows(img, gaps)
    print("検出した行:", [(r[0], r[1]) for r in rows])
    anims = []   # (動き名, アンカー, [crop...])
    for k, ri in enumerate(rows_sel):
        y0, y1 = rows[ri]
        crops = [img.crop(b) for b in frames_in_row(img, y0, y1, gaps[k])]
        foot = dict(v.split(":") for v in a.foot_white.split(",") if v)
        if str(k) in foot:
            thr = int(foot[str(k)])
            for c in crops:   # 足元（下から30%）に残った、白に近い画素を消す
                cp = c.load()
                for y in range(int(c.height * 0.7), c.height):
                    for x in range(c.width):
                        if cp[x, y][3] and min(cp[x, y][:3]) > thr:
                            cp[x, y] = (0, 0, 0, 0)
        print("  %s: %d コマ" % (names[k], len(crops)))
        anims.append((names[k], anchors[k], crops))

    ref = [c.height for c in anims[0][2]]
    scale = a.target_h / statistics.median(ref)
    print("縮尺: 元絵の1ドット相当 = %.1fpx" % (1 / scale))
    pal = palette_from([c for _, _, cs in anims for c in cs], a.colors)
    if a.gain != 1.0:
        pal = [tuple(min(255, round(v * a.gain)) for v in c) for c in pal]

    placed = []   # (動き名, 番号, dots, ax, ay)
    for name, mode, crops in anims:
        for i, c in enumerate(crops):
            d = to_dots(c, scale, pal)
            ax = anchor_x(c, mode, scale)
            if a.rim:
                d = add_rim(d, tuple(int(v) for v in a.rim.split(",")))
                ax += 1
            ay = d.height if a.valign == "bottom" else d.height // 2
            placed.append((name, i, d, ax, ay))
    left = max(p[3] for p in placed)
    right = max(p[2].width - p[3] for p in placed)
    up = max(p[4] for p in placed)
    down = max(p[2].height - p[4] for p in placed)
    cw, ch = left + right, up + down
    print("枠:", cw, "x", ch, " 基準(左,上) =", (left, up))

    os.makedirs(a.out_dir, exist_ok=True)
    frames = []
    for name, i, d, ax, ay in placed:
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.paste(d, (left - ax, up - ay), d)
        canvas.save(os.path.join(a.out_dir, "%s_%s_%d.png" % (a.name, name, i)))
        frames.append((name, canvas))

    S, G = 4, 8
    per_row = max(len([f for f in frames if f[0] == n]) for n in names)
    sheet = Image.new("RGB", (per_row * (cw * S + G) + G, len(names) * (ch * S + G) + G), (92, 148, 252))
    for r, n in enumerate(names):
        for c, (_, f) in enumerate([f for f in frames if f[0] == n]):
            big = f.resize((cw * S, ch * S), Image.NEAREST)
            sheet.paste(big, (G + c * (cw * S + G), G + r * (ch * S + G)), big)
    sheet.save(os.path.join(a.out_dir, "%s_sheet.png" % a.name))


if __name__ == "__main__":
    main()
