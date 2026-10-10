"""変換済みのコマ（assets/images/player_XX.png）から、動きごとのプレビューGIFを作る。

使い方: python tools/make_gif.py
出力: assets/concept/anim_*.gif （空色の背景、6倍拡大）
"""
import os

from PIL import Image

BASE = os.path.join(os.path.dirname(__file__), "..", "assets")
SCALE = 6
BG = (92, 148, 252)

# コマ番号は行→列の順。(コマ番号, 表示ミリ秒)
MOTIONS = {
    "idle": [(0, 500), (1, 500)],
    "walk": [(i, 110) for i in range(2, 8)],
    "attack": [(8, 150), (9, 90), (10, 90), (11, 200)],
    "damage": [(12, 200), (13, 200)],
    "throw": [(19, 120), (20, 90), (21, 90), (22, 160)],
    "jump": [(14, 100), (15, 100), (16, 140), (17, 100), (18, 100)],
}


def load(i):
    im = Image.open(os.path.join(BASE, "images", f"player_{i:02d}.png"))
    big = im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)
    bg = Image.new("RGB", big.size, BG)
    bg.paste(big, (0, 0), big)
    return bg


def save(name, seq):
    frames = [load(i) for i, _ in seq]
    path = os.path.join(BASE, "concept", f"anim_{name}.gif")
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=[ms for _, ms in seq], loop=0, disposal=2)
    print(name, len(frames), "コマ", os.path.getsize(path) // 1024, "KB")


if __name__ == "__main__":
    for name, seq in MOTIONS.items():
        save(name, seq)
    # 全部つなぎ: 待機 → 歩き2周 → 攻撃 → 被ダメージ → 待機
    allseq = MOTIONS["idle"] * 2 + MOTIONS["walk"] * 2 + MOTIONS["attack"] + MOTIONS["damage"] + MOTIONS["idle"]
    save("all", allseq)
