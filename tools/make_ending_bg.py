"""エンドロールの景色（いまの平泉の町なみ）を、ゲーム用にする。

使い方: python tools/make_ending_bg.py 町なみ.jpg 出力.png
  1. 山のふもとの、金色の堂を、杉の木立に描きかえる。実際の金色堂は、覆堂（おおいどう）の中にあって、外の景色としては見えないため。
     となりの杉を写して重ね、残った金色は、まわりの緑で埋める（HALL が、堂のある範囲。絵を作り直したら、ここを直す）
  2. 空の上のほうを切って、高さ HEIGHT に縮める。2ドット角の粗いドットにして、色数を絞る
  3. 左右を反転した絵を、右につなぐ（横にくり返して流しても、つなぎ目で、家が切れない）
"""
import sys

from PIL import Image

HALL = (636, 372, 736, 447)     # 金色の堂のある範囲（元絵の座標）
CEDAR = (742, 372, 842, 447)    # 写す杉（堂の右どなり）
TOP = 150                       # 空の、上から切る量
HEIGHT = 154                    # できあがりの高さ（歩道の上に見える範囲）
CHUNK, COLORS = 2, 40


def main(src, out):
    im = Image.open(src).convert("RGB")
    im.paste(im.crop(CEDAR).transpose(Image.FLIP_LEFT_RIGHT), HALL[:2])
    px = im.load()
    green = px[HALL[2] + 8, HALL[3] + 6]
    for y in range(HALL[1] - 6, HALL[3] + 16):
        for x in range(HALL[0] - 10, HALL[2] + 10):
            r, g, b = px[x, y]
            if r > 150 and g > 105 and b < 120 and r - b > 70:      # 残った金色
                px[x, y] = green
    im = im.crop((0, TOP, im.width, im.height))
    w = round(im.width * HEIGHT / im.height / CHUNK) * CHUNK
    small = im.resize((w // CHUNK, HEIGHT // CHUNK), Image.BOX)
    im = small.resize((w, HEIGHT), Image.NEAREST).quantize(colors=COLORS, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    both = Image.new("RGB", (w * 2, HEIGHT))
    both.paste(im, (0, 0))
    both.paste(im.transpose(Image.FLIP_LEFT_RIGHT), (w, 0))
    both.save(out, optimize=True)
    print("景色", both.size)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
