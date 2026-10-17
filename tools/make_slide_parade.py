"""成果発表スライド（docs/slide.html）の、キャラクターの行列の絵を作る。
ゲームの絵を、2倍（ドットがにじまない、整数倍）にして、右へ向かって行進するように並べる。
敵とボスの絵は左向きなので、左右を反転する（清衡は正面なので、そのまま）。地面（道路と横断歩道）は、スライドの側で描く。

使い方: python tools/make_slide_parade.py   → docs/slide_parade.png
"""
import os

from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..")
IMG = os.path.join(ROOT, "assets", "images")
OUT = os.path.join(ROOT, "docs", "slide_parade.png")
K = 2               # 拡大の倍率（整数）
W, H = 1152, 232    # 絵の大きさ（スライドの、左右の余白を除いた幅）。足は、絵のいちばん下

# 左から右へ（行進の後ろから先頭へ）: (絵, 反転するか, 地面からの浮き)
PARADE = [
    ("enemies/boss4_idle_0", False, 0),     # 清衡（正面）
    ("enemies/boss3_stance_0", True, 0),    # 秀衡
    ("enemies/boss2_idle_0", True, 0),      # 基衡
    ("enemies/boss_walk_0", True, 0),       # 泰衡
    ("enemies/tengu_walk_0", True, 0),
    ("enemies/yumihei_idle_0", True, 0),
    ("enemies/karasu_flap_0", True, 96),    # 烏は、空を飛ぶ
    ("enemies/ochimusha_walk_0", True, 0),
    ("enemies/kitsunebi_flicker_0", True, 56),
    ("enemies/miira_walk_0", True, 0),
    ("hime_walk_0", False, 0),
    ("roll_tanuki_raise_2", False, 0),      # 先頭: 手を挙げて、横断歩道を渡るタヌキ侍
]


def load(name, flip):
    im = Image.open(os.path.join(IMG, name + ".png")).convert("RGBA")
    im = im.crop(im.getbbox())
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im.resize((im.width * K, im.height * K), Image.NEAREST)


def main():
    parts = [(load(name, flip), lift) for name, flip, lift in PARADE]
    total = sum(im.width for im, _ in parts)
    gap = (W - total) // (len(parts) - 1)      # 幅いっぱいに、等しい間で並べる
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = 0
    for im, lift in parts:
        out.alpha_composite(im, (x, H - im.height - lift))     # 足は、絵のいちばん下（スライドの道路の上に、立つ）
        x += im.width + gap
    out.save(OUT)
    print("書き出し:", os.path.normpath(OUT), out.size, "行列の幅", total, "間", gap)


if __name__ == "__main__":
    main()
