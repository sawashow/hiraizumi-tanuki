"""団子の絵（縦の串）を、斜めに傾けた絵にする。美味しそうに見せるため。

使い方: python tools/make_dango_tilt.py [元の絵] [出力]     （既定: assets/images/items/dango.png → dango_tilt.png）
  回転すると、輪郭が崩れる（小さな絵）ので、1行ずつ、横にずらして、傾ける（上ほど右へ。1行で 0.6 ドット、約 31 度）。
  ゲームは、拾える団子と、頭の上の吹き出しに、この絵を使う。団子のゲージ（左上）は、元の縦の絵のまま。
"""
import os
import sys

from PIL import Image

K = 0.6     # 1行あたり、ずらすドット数


def main(src, out):
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    res = Image.new("RGBA", (w + int(h * K) + 1, h), (0, 0, 0, 0))
    for y in range(h):
        res.alpha_composite(im.crop((0, y, w, y + 1)), (round((h - 1 - y) * K), y))
    res.save(out)
    print("書き出し:", out, res.size)


if __name__ == "__main__":
    d = os.path.join(os.path.dirname(__file__), "..", "assets", "images", "items")
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(d, "dango.png"),
         sys.argv[2] if len(sys.argv) > 2 else os.path.join(d, "dango_tilt.png"))
