"""1UP のアイテムの絵（タヌキ侍の顔）を、生成した絵から作る。

使い方: python tools/make_oneup_item.py [元絵] [出力]
  既定の元絵は assets/concept/source/oneup_item.jpg（Gemini で生成。背景はマゼンタ）、出力は assets/images/items/oneup.png。
  マゼンタの背景を透明にし、絵のある所だけを切り出して、高さ H ドットに縮める（ドットの真ん中の色を拾う。にじませない）
"""
import os
import sys

from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..")
H = 20      # ゲームでの高さ（ほかのアイテムと同じくらい。金の葉 20・おにぎり 15）


def main(src, out):
    im = Image.open(src).convert("RGB")
    px = im.load()
    mask = Image.new("L", im.size, 0)
    mp = mask.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b = px[x, y]
            if not (r > 180 and b > 180 and g < 110):      # マゼンタ（JPEG のにじみを含む）以外が、絵
                mp[x, y] = 255
    box = mask.getbbox()
    im, mask = im.crop(box), mask.crop(box)
    w = round(im.width * H / im.height)
    small = im.resize((w, H), Image.NEAREST)
    alpha = mask.resize((w, H), Image.NEAREST)
    small.putalpha(alpha)
    small.save(out)
    print("書き出し:", os.path.normpath(out), small.size)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets", "concept", "source", "oneup_item.jpg"),
         sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "assets", "images", "items", "oneup.png"))
