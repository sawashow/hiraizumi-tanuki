"""タヌキ姫の歩く絵（白背景に、横に並んだ姿）を、ゲーム用のコマにする。

使い方: python tools/make_hime_walk.py シート.jpg 出力フォルダ [--pitch 9.38 --ox 9.0 --oy 7.25] [--measure]
  元絵は、もともとドット絵（1ドットが、何ピクセルかの四角）なので、縮めて平均すると、ぼやける（最初は、そうして、顔がつぶれた）。
  元絵のドットの刻み（--pitch）と、ずれ（--ox・--oy）に合わせて、ますの真ん中の色を、1つずつ拾う。
  --measure を付けると、刻みとずれを、輪郭の並び方から測って、出す（絵を作り直したら、これで測り直す）。
  背景の白は、外から塗りつぶして透明にする（着物の白いえりは、輪郭に囲まれているので、残る）。大きい塊を、左から順に、姿として切り出す。
  USE に、使う姿の番号（左から 0〜）を、コマの順に書く。番号の前に - を付けると、左右を反転する（右向きに描かれた姿を、左向きにそろえる）。
  足元と、頭の左端を、そろえる。姫の絵は、左向き
出力: 出力フォルダ/hime_walk_0〜3.png、hime_0.png・hime_1.png（姫を助ける場面の、立つ・跳ねる）、確認用の hime_walk_sheet.png（ゲームは読まない）
"""
import argparse
import os
import sys

from PIL import Image, ImageChops

sys.path.insert(0, os.path.dirname(__file__))
from slice_sheet import components, remove_white_bg  # noqa: E402

# 2026-10-13 の絵: 0 = 立つ（すそが長く、足が見えない）/ 1・2 = 歩く / 3 = 歩く（右向きに描かれている）
STAND = {"hime_0.png": 0, "hime_1.png": 2}
USE = ("1", "2", "-3", "2")     # 2 は、両足をそろえた姿。立っているときにも、これを使う（config.py の ROLL の stand）


def measure(im):
    """ドットの刻みと、ずれ: 色の変わり目（輪郭）が、いちばん多く乗る格子を探す。(刻み, 横のずれ, 縦のずれ)"""
    g = im.convert("L")
    w, h = g.size
    cols = list(ImageChops.difference(g, ImageChops.offset(g, 1, 0)).resize((w, 1), Image.BOX).getdata())
    rows = list(ImageChops.difference(g, ImageChops.offset(g, 0, 1)).resize((1, h), Image.BOX).getdata())

    def fit(v, pitches):
        best = (0, 0, 0)
        for p in pitches:
            o = 0.0
            while o < p:
                tot = n = 0
                x = o
                while x < len(v) - 1:
                    tot += v[int(round(x))]
                    n += 1
                    x += p
                best = max(best, (tot / n, p, o))
                o += 0.25
        return best

    _, p, ox = fit(cols, [8 + k * 0.02 for k in range(250)])
    _, _, oy = fit(rows, [p])
    return round(p, 2), ox, oy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("out")
    ap.add_argument("--pitch", type=float, default=9.38)
    ap.add_argument("--ox", type=float, default=9.0)
    ap.add_argument("--oy", type=float, default=7.25)
    ap.add_argument("--measure", action="store_true")
    a = ap.parse_args()
    raw = Image.open(a.sheet)
    if a.measure:
        print("刻み %.2f、ずれ 横 %.2f・縦 %.2f" % measure(raw))
        return
    img = remove_white_bg(raw, erode=False)
    src = img.load()
    p = a.pitch
    w, h = int((img.width - a.ox) / p), int((img.height - a.oy) / p)
    dots = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dp = dots.load()
    for j in range(h):
        for i in range(w):
            cx, cy = int(a.ox + (i + 0.5) * p), int(a.oy + (j + 0.5) * p)
            near = [src[cx + dx, cy + dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
            if sum(1 for c in near if c[3]) >= 5:       # ますの真ん中が、絵の中
                solid = [c for c in near if c[3]]
                dp[i, j] = tuple(sum(c[k] for c in solid) // len(solid) for k in range(3)) + (255,)
    q = dots.convert("RGB").quantize(colors=16, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGBA")   # JPEG のにじみを、少数色にまとめる
    q.putalpha(dots.getchannel("A"))
    found = sorted(components(q), key=lambda c: -len(c["pts"]))
    comps = sorted(found[:4], key=lambda c: c["box"][0])
    for c in found[4:]:         # 体から離れて描かれた小さな物（かんざし）は、すぐそばの姿に入れる
        for m in comps:
            (a0, b0, a1, b1), (x0, y0, x1, y1) = c["box"], m["box"]
            if len(c["pts"]) >= 2 and max(x0 - a1, a0 - x1, 0) + max(y0 - b1, b0 - y1, 0) <= 2:
                m["pts"] = list(m["pts"]) + list(c["pts"])
                break
    qp = q.load()
    crops = []
    for c in comps:
        xs, ys = [pt[0] for pt in c["pts"]], [pt[1] for pt in c["pts"]]
        x0, y0 = min(xs), min(ys)
        crop = Image.new("RGBA", (max(xs) - x0 + 1, max(ys) - y0 + 1), (0, 0, 0, 0))
        px = crop.load()
        for x, y in c["pts"]:
            px[x - x0, y - y0] = qp[x, y]
        crops.append(crop)
    picked = [crops[int(u.lstrip("-"))].transpose(Image.FLIP_LEFT_RIGHT) if u.startswith("-") else crops[int(u)] for u in USE]

    def head_left(d):       # 頭の左端（上から 4 割の範囲で、いちばん左の画素）
        px = d.load()
        return min(x for y in range(d.height * 4 // 10) for x in range(d.width) if px[x, y][3])

    lefts = [head_left(d) for d in picked]
    pad = max(lefts)
    cw = max(d.width + pad - l for d, l in zip(picked, lefts))
    ch = max(d.height for d in picked)
    os.makedirs(a.out, exist_ok=True)
    sheet = Image.new("RGB", (len(picked) * (cw * 4 + 8) + 8, ch * 4 + 16), (120, 170, 230))
    for i, (d, l) in enumerate(zip(picked, lefts)):
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.paste(d, (pad - l, ch - d.height), d)
        canvas.save(os.path.join(a.out, "hime_walk_%d.png" % i))
        big = canvas.resize((cw * 4, ch * 4), Image.NEAREST)
        sheet.paste(big, (8 + i * (cw * 4 + 8), 8), big)
    sheet.save(os.path.join(a.out, "hime_walk_sheet.png"))
    # 姫を助ける場面の絵も、同じ絵から作る（大きさを、歩く絵とそろえる）: hime_0 = 立つ（すその長い姿）/ hime_1 = 跳ねて喜ぶ（両足をそろえた姿）
    for name, n in STAND.items():
        crops[n].save(os.path.join(a.out, name))
    print("枠 %d x %d" % (cw, ch))


if __name__ == "__main__":
    main()
