"""絵の一番外側の黒い縁を、隣の体の色を暗くした色に置き換える（縁の黒さを減らす）。

使い方: python tools/thin_outline.py 入力.png ...      （上書きする。元に戻すときは git checkout）
  外側（透明に接する）の、黒に近いドットだけを置き換える。中の黒い線・影は、そのまま。
  タヌキ侍（player_00〜36）の縁が、ほかのキャラより黒く目立つので、これで弱めた（2026-10-16）。
  最初は置き換え（REMOVE = False）にしたが、変化がわかりにくかったので、消す（REMOVE = True）にした。絵が一回り小さく見える。
  やり直すときは、元の絵に戻してから流す: git checkout 06e6c33^ -- assets/images/player_*.png
"""
import sys

from PIL import Image

REMOVE = True        # True: 縁を消す（いまの設定）/ False: 縁を、体の色を暗くした色に置き換える
DARKEN = 0.6         # 置き換える色の明るさ（隣の色に掛ける）
NEAR = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1))


def is_dark(c):
    return c[0] + c[1] + c[2] < 120


def thin(path):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    src, out = im.load(), im.copy()
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3] < 128 or not is_dark(src[x, y]):
                continue
            if not any(not (0 <= x + dx < w and 0 <= y + dy < h) or src[x + dx, y + dy][3] < 128
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                continue        # 外側ではない
            if REMOVE:
                dst[x, y] = (0, 0, 0, 0)
                continue
            for dx, dy in NEAR:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and src[nx, ny][3] >= 128 and not is_dark(src[nx, ny]):
                    n = src[nx, ny]
                    dst[x, y] = (int(n[0] * DARKEN), int(n[1] * DARKEN), int(n[2] * DARKEN), 255)
                    break
    out.save(path)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        thin(p)
    print("処理:", len(sys.argv) - 1, "枚")
