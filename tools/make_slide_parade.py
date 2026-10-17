"""成果発表スライド（docs/slide.html）の、キャラクターの行列の絵を作る。
ゲームの絵を、2倍（ドットがにじまない、整数倍）にして、右へ向かって行進するように並べる。
敵とボスの絵は左向きなので、左右を反転する（清衡は正面なので、そのまま）。先頭のタヌキ侍の足元に、横断歩道を描く。

使い方: python tools/make_slide_parade.py   → docs/slide_parade.png
"""
import os

from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(__file__), "..")
IMG = os.path.join(ROOT, "assets", "images")
OUT = os.path.join(ROOT, "docs", "slide_parade.png")
K = 2               # 拡大の倍率（整数）
W, H = 1152, 252    # 絵の大きさ（スライドの、左右の余白を除いた幅）
BASE = H - 24       # 地面の高さ（足の位置）
GAP = 8             # キャラクターの間（2倍にしたあと）

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
ZEBRA_FROM = "hime_walk_0"      # この絵から先頭までの足元に、横断歩道


def load(name, flip):
    im = Image.open(os.path.join(IMG, name + ".png")).convert("RGBA")
    im = im.crop(im.getbbox())
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im.resize((im.width * K, im.height * K), Image.NEAREST)


def main():
    parts = [(name, load(name, flip), lift) for name, flip, lift in PARADE]
    total = sum(im.width for _, im, _ in parts) + GAP * (len(parts) - 1)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    x = W - total       # 右へ寄せる（先頭が、右の端）
    zebra_x = None
    for name, im, lift in parts:
        if name == ZEBRA_FROM:
            zebra_x = x - 8
        out.alpha_composite(im, (x, BASE - im.height - lift))
        x += im.width + GAP
    # 地面の線と、先頭の足元の横断歩道（足の下に、敷く）
    ground = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(ground)
    g.rectangle((0, BASE, W, BASE + 3), fill=(48, 44, 40, 255))
    if zebra_x is not None:     # 道路（灰色）に、白い縞。足は、道路の上に乗る
        g.rectangle((zebra_x, BASE - 14, W, H - 2), fill=(92, 92, 98, 255))
        for sx in range(zebra_x + 6, W - 6, 20):
            g.rectangle((sx, BASE - 12, sx + 10, H - 4), fill=(246, 244, 236, 255))
    ground.alpha_composite(out)
    del d
    ground.save(OUT)
    print("書き出し:", os.path.normpath(OUT), ground.size, "行列の幅", total)


if __name__ == "__main__":
    main()
