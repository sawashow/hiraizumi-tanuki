"""風のエフェクト（基衡の扇の風・月見坂の山おろし）のシートを、ゲーム用のコマにする。

使い方: python tools/make_gust.py シート.jpg 出力フォルダ [--height 46] [--colors 8]
  シートは、白か黒の無地の背景に、右へ進む風が、2列×2行（左上 → 右上 → 左下 → 右下の順）で4コマ。
  背景を外から塗りつぶして透明にし（風の中の白は、輪郭に囲まれているので、残る）、大きい塊4つを、1コマずつ切り出す。
  離れて描かれた葉は、いちばん近いコマに入れる。全コマ同じ縮尺（いちばん高いコマが --height ドット）・同じ少数色。
  先頭（右端）と、下端を、そろえる。
出力: 出力フォルダ/gust_0〜3.png と、確認用の gust_sheet.png（ゲームは読まない）
"""
import argparse
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import make_enemy as me  # noqa: E402
from slice_sheet import components, remove_white_bg  # noqa: E402


LEAF = [(92, 148, 70), (52, 96, 48), (128, 90, 52)]     # 葉の緑と茶（面積が小さくて、色を絞ると消えるので、必ず残す）


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("out")
    ap.add_argument("--height", type=int, default=46)
    ap.add_argument("--colors", type=int, default=8)
    a = ap.parse_args()
    img = remove_white_bg(Image.open(a.sheet), erode=False)
    # 大きい塊4つが、風の本体。小さい塊（離れて描かれた葉）は、いちばん近い本体のコマに入れる
    comps = sorted(components(img), key=lambda c: -len(c["pts"]))
    main4 = sorted(comps[:4], key=lambda c: (c["box"][1] // (img.height // 2), c["box"][0]))    # 左上 → 右上 → 左下 → 右下
    groups = [list(c["pts"]) for c in main4]

    def gap(c, m):
        (a0, b0, a1, b1), (x0, y0, x1, y1) = c["box"], m["box"]
        return max(x0 - a1, a0 - x1, 0) + max(y0 - b1, b0 - y1, 0)

    for c in comps[4:]:
        k = min(range(4), key=lambda i: gap(c, main4[i]))
        if len(c["pts"]) >= 30 and gap(c, main4[k]) < 60:
            groups[k] += c["pts"]
    crops = []
    src = img.load()
    for pts in groups:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        x0, y0 = min(xs), min(ys)
        crop = Image.new("RGBA", (max(xs) - x0 + 1, max(ys) - y0 + 1), (0, 0, 0, 0))
        px = crop.load()
        for x, y in pts:
            px[x - x0, y - y0] = src[x, y]
        crops.append(crop)
    scale = a.height / max(c.height for c in crops)
    small = [c.resize((max(1, c.width // 4), max(1, c.height // 4)), Image.NEAREST) for c in crops]     # 色を選ぶだけなので、小さくして速くする
    pal = me.palette_from(small, a.colors) + LEAF
    dots = [me.to_dots(c, scale, pal) for c in crops]
    cw, ch = max(d.width for d in dots), max(d.height for d in dots)
    os.makedirs(a.out, exist_ok=True)
    sheet = Image.new("RGB", (len(dots) * (cw * 3 + 8) + 8, ch * 3 + 16), (60, 90, 70))
    for i, d in enumerate(dots):
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.paste(d, (cw - d.width, ch - d.height), d)
        canvas.save(os.path.join(a.out, "gust_%d.png" % i))
        big = canvas.resize((cw * 3, ch * 3), Image.NEAREST)
        sheet.paste(big, (8 + i * (cw * 3 + 8), 8), big)
    sheet.save(os.path.join(a.out, "gust_sheet.png"))
    print("枠 %d x %d（縮尺 %.2f）" % (cw, ch, scale))


if __name__ == "__main__":
    main()
