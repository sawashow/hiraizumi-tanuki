"""姫を助ける場面の背景（夜明けの参道）を、ゲーム用（480×270）にする。

使い方: python tools/make_thanks_bg.py 元絵.jpg 出力.png
  元絵: assets/concept/source/thanks_bg.jpg（Gemini）。出力: assets/images/thanks_bg.png
  縮めて平均するとぼやけるので、480×270 の格子に合わせて、ますの真ん中の近くの色を拾い、少数色にまとめる。
  地面（石畳）の上端は、元絵では、下から約 24% のところ（高さ 206 ほど）。人物の足元の高さ（config.py の THANKS の floor）は、石畳の上に置く
"""
import sys

from PIL import Image

W, H, COLORS = 480, 270, 28


def main(src, out):
    img = Image.open(src).convert("RGB")
    px, py = img.width / W, img.height / H
    sp = img.load()
    dots = Image.new("RGB", (W, H))
    for j in range(H):
        for i in range(W):
            cx, cy = (i + 0.5) * px, (j + 0.5) * py
            pts = [sp[min(int(cx) + dx, img.width - 1), min(int(cy) + dy, img.height - 1)] for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
            dots.putpixel((i, j), tuple(sum(p[k] for p in pts) // len(pts) for k in range(3)))
    dots.quantize(colors=COLORS, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB").save(out)
    print("書き出し:", out, (W, H))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
