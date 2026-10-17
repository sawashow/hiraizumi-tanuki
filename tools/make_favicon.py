"""ファビコン（ブラウザのタブの絵）を作る。タヌキ侍（player_00）の顔を、正方形に切り出して、整数倍に大きくする。
ゲームの公開（.github/workflows/pages.yml）と、成果発表のスライド（docs/slide.html）の両方で使う。

使い方: python tools/make_favicon.py   → assets/images/favicon.png
"""
import os

from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..")
IMG = os.path.join(ROOT, "assets", "images")
FACE = (17, 3, 47, 33)      # player_00 の中の、顔（兜を含む）の所。正方形
K = 4                       # 拡大の倍率（整数。ドットがにじまない）


def main():
    im = Image.open(os.path.join(IMG, "player_00.png")).convert("RGBA").crop(FACE)
    im = im.resize((im.width * K, im.height * K), Image.NEAREST)
    out = os.path.join(IMG, "favicon.png")
    im.save(out)
    print("書き出し:", os.path.normpath(out), im.size)


if __name__ == "__main__":
    main()
