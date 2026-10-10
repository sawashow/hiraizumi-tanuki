"""中景（杉並木・灯籠・堂。白背景）の絵を、画面の高さに合わせて透過PNGにする。

使い方: python tools/make_mid.py 元絵.jpg 出力.png [高さ=270] [色数=24]
  - 白に近い画素はすべて透明にする（この絵に白い物体はない）。JPEGの縁の白いにじみは1px削る
  - 高さに合わせて縮小し、色数を絞る。半透明は作らず、透明か不透明のどちらかにする
"""
import sys

from PIL import Image, ImageFilter

BG_MIN = 225


LAMP = (255, 176, 64)  # 灯籠の灯り。小さくて縮小で消えるので、専用に塗り直す


def is_lamp(c):
    r, g, b = c[:3]
    return r > 215 and 120 < g < 215 and b < 140 and r - b > 110


def main(src, dst, height=270, colors=24):
    img = Image.open(src).convert("RGBA")
    px = img.load()
    lamp = Image.new("L", img.size, 0)
    lp = lamp.load()
    for y in range(img.height):
        for x in range(img.width):
            if is_lamp(px[x, y]):
                lp[x, y] = 255
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, _ = px[x, y]
            if min(r, g, b) > BG_MIN:
                px[x, y] = (0, 0, 0, 0)
    img.putalpha(img.getchannel("A").filter(ImageFilter.MinFilter(3)))
    w = round(img.width * height / img.height)
    small = img.resize((w, height), Image.BOX)
    alpha = small.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
    rgb = small.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGBA")
    rgb.putalpha(alpha)
    lamp_small = lamp.resize((w, height), Image.BOX).point(lambda v: 255 if v >= 40 else 0)
    rp, lsp = rgb.load(), lamp_small.load()
    for y in range(height):
        for x in range(w):
            if lsp[x, y]:
                rp[x, y] = LAMP + (255,)
    rgb.save(dst)
    print("出力:", rgb.size)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2],
         int(sys.argv[3]) if len(sys.argv) > 3 else 270,
         int(sys.argv[4]) if len(sys.argv) > 4 else 24)
