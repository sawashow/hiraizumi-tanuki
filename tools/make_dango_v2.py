"""団子（三色団子の串）の絵を、ゲームの大きさ（高さ25ドット）で、1ドットずつ描いて書き出す。

使い方: python tools/make_dango_v2.py [出力フォルダ=assets/images/items]
  dango.png      縦の串（左上のゲージ用）
  dango_tilt.png 斜めの串（面に置く団子・吹き出しの団子）
縦は、Gemini の絵（丸い団子3つ・白いハイライト・短い串）を見本に、描き直した。斜めは、Gemini の斜めの絵を縮めて、手で直した（2026-10-16）。
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


# 斜めの串（19×20）。Gemini の斜めの絵（38×40）を、半分に縮めて、欠けた所（輪郭の穴・串）を、手で直したもの
TILT = [
    "..............KK.KK",
    "............KKppKSK",
    "...........KpppppK.",
    "...........KppppppK",
    "...........KpppppPK",
    ".........KKPPppppK.",
    "........KKwwPPPPPK.",
    ".......KKKKwwPPPK..",
    ".......KwwwwwWKK...",
    ".......KwwwwwK.....",
    "....KKKhWwwwWK.....",
    "...KKKKgGWWKK......",
    "...KgggggKK........",
    "..KggggggK.........",
    "..KGggggGK.........",
    "...KGgggK..........",
    "..KKKGGK...........",
    ".KSK.KK............",
    "KSK................",
    "s..................",
]


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "assets", "images", "items")
    a = render(build())
    a.save(os.path.join(out, "dango.png"))
    t = render(TILT)
    t.save(os.path.join(out, "dango_tilt.png"))
    print("書き出し:", out, a.size, t.size)
