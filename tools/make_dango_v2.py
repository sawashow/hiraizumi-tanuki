"""団子（三色団子の串）の絵を、ゲームの大きさ（高さ25ドット）で、1ドットずつ描いて書き出す。

使い方: python tools/make_dango_v2.py [出力フォルダ=assets/images/items]
  dango.png      縦の串（左上のゲージ用）
  dango_tilt.png 斜めの串（面に置く団子・吹き出しの団子）。団子の形はそのまま、串に沿って位置を斜めに並べる
元は Gemini の絵（丸い団子3つ・白いハイライト・短い串）。細かすぎて縮めると崩れるので、見本にして描き直した（2026-10-16）。
"""
import os
import sys

from PIL import Image

PAL = {
    "K": (24, 16, 16),                                       # 輪郭
    "S": (210, 160, 96), "s": (150, 104, 56),                # 串
    "p": (232, 120, 128), "P": (180, 72, 84), "q": (252, 204, 204),     # 赤（ピンク）: 面・影・ハイライト
    "w": (244, 236, 214), "W": (208, 192, 164), "x": (255, 255, 255),   # 白
    "g": (132, 164, 76), "G": (88, 116, 52), "h": (184, 212, 124),      # 緑
}


# 団子1つ（幅9・高さ6。f=面 / s=影 / h=ハイライト）。上の輪郭は、上の団子の下の輪郭と共有する
BALL = [
    "..KhffffK..",
    ".KhfffffsK.",
    ".KfffffffK.",
    ".KffffffsK.",
    "..KsssssK..",
    "...KKKKK...",     # 下の輪郭（次の団子の上の輪郭を兼ねる）
]


def build():
    rows = ["....KKK....", "....KSK....", "...KKKKK..."]
    for f, s, h in (("p", "P", "q"), ("w", "W", "x"), ("g", "G", "h")):
        rows += [r.replace("f", f).replace("s", s).replace("h", h) for r in BALL]
    rows += ["....KSK....", "....KSK....", "....KsK....", "....KKK...."]
    return rows


def render(rows):
    h, w = len(rows), max(len(r) for r in rows)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c in PAL:
                px[x, y] = PAL[c] + (255,)
    return im


def balls_rows():
    """団子3つ（下から緑・白・赤）の、1つぶんの絵（上の輪郭つき。幅11・高さ7）"""
    out = []
    for f, s, h in (("g", "G", "h"), ("w", "W", "x"), ("p", "P", "q")):
        out.append(["...KKKKK..."] + [r.replace("f", f).replace("s", s).replace("h", h) for r in BALL])
    return out


def tilt_im(slope=0.5, w=20, h=25):
    """斜めの串。団子の形はそのまま（回転しない）、串に沿って位置だけを斜めに並べる。串は右上がり（1行で slope ドット）"""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()

    def put(x, y, c):
        if 0 <= x < w and 0 <= y < h:
            px[x, y] = PAL[c] + (255,)

    def sx(y):          # 串の、y 行目の中心の x
        return 3.5 + (h - 1 - y) * slope
    for y in range(h):  # 串（輪郭つき）
        x = round(sx(y))
        put(x - 1, y, "K")
        put(x + 1, y, "K")
        put(x, y, "S" if y < h - 3 else "s")
    put(round(sx(0)), 0, "K")
    put(round(sx(h - 1)) , h - 1, "K")
    for (rows, cy) in zip(balls_rows(), (18, 12, 6)):      # 緑・白・赤。下から重ねる
        cx = round(sx(cy))
        for j, r in enumerate(rows):
            for i, c in enumerate(r):
                if c in PAL:
                    put(cx - 5 + i, cy - 3 + j, c)
    return im


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "assets", "images", "items")
    a = render(build())
    a.save(os.path.join(out, "dango.png"))
    t = tilt_im()
    t.save(os.path.join(out, "dango_tilt.png"))
    print("書き出し:", out, a.size, t.size)
