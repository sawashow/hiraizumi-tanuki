"""崖登り（画面が上下に動く区画）のための、縦に長い空と、崖の岩肌を作る。

使い方: python tools/make_climb_bg.py sky  縦長の絵.jpg 出力.png [--width 600] [--bottom 60] [--height 570] [--colors 20] [--chunk 2] [--shade 1.0] [--sat 1.0]
        python tools/make_climb_bg.py cliff 岩肌のシート.jpg 出力フォルダ [--use 0,3,4,5,6,7]
  sky:   横 --width に縮めて、下から --bottom を捨て、そこから上へ --height を残す。2ドット角の粗いドットにして、色数を絞る。
         画面の高さは 270。残した高さとの差（height - 270）が、登るにつれて、景色が下へ流れる量になる。
         --chunk は、ドットの粗さ。--shade は明るさ、--sat は色の濃さの倍率（堂の中の、まぶしい金を、抑える）
  cliff: 白背景に並んだ正方形の岩肌を、32x32 のタイルにする（黒い枠は、削る）。--use で、使う番号を選ぶ（上の行から、左から）。
         出力: 出力フォルダ/cliff_0.png, cliff_1.png, ...
"""
import argparse
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))

CHUNK = 2


def make_sky(a):
    im = Image.open(a.src).convert("RGB")
    h = round(im.height * a.width / im.width)
    im = im.resize((a.width, h), Image.LANCZOS).crop((0, h - a.bottom - a.height, a.width, h - a.bottom))
    if a.chunk > 1:
        small = im.resize((a.width // a.chunk, a.height // a.chunk), Image.BOX)
        im = small.resize((a.width, a.height), Image.NEAREST)
    im = im.quantize(colors=a.colors, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    if a.shade != 1.0 or a.sat != 1.0:      # 金色堂のいまの背景と、同じ暗くし方（明るさを落として、色を薄くする）
        from make_stage4 import shade
        im = shade(im, (a.shade, a.sat))
    im.save(a.out, optimize=True)
    print("空", im.size, "登るにつれて流れる量", a.height - 270)


def make_cliff(a):
    from make_stage3 import boxes, square_tile
    img = Image.open(a.src).convert("RGB")
    bs = boxes(img)
    use = [int(n) for n in a.use.split(",")] if a.use else range(len(bs))
    os.makedirs(a.out, exist_ok=True)
    for k, n in enumerate(use):
        square_tile(img, bs[n], edge=10).save(os.path.join(a.out, "cliff_%d.png" % k))
    print("岩肌", len(bs), "枚のうち", list(use))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=("sky", "cliff"))
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--width", type=int, default=600)
    ap.add_argument("--bottom", type=int, default=60)
    ap.add_argument("--height", type=int, default=570)
    ap.add_argument("--colors", type=int, default=20)
    ap.add_argument("--shade", type=float, default=1.0)
    ap.add_argument("--sat", type=float, default=1.0)
    ap.add_argument("--chunk", type=int, default=CHUNK)
    ap.add_argument("--use", default="")
    a = ap.parse_args()
    make_sky(a) if a.kind == "sky" else make_cliff(a)


if __name__ == "__main__":
    main()
