"""金色堂の絵（堂の中の背景・柱・床タイル・光る足場）を、元絵（Gemini）から、ゲーム用に変換する。

使い方: python tools/make_stage4.py 元絵フォルダ 出力フォルダ
  元絵フォルダに、stage4_bg.jpg・stage4_tiles.jpg を置く（assets/concept/source/）。
  出力: bg_sky.png・bg_mid.png・tile_00〜05.png・stone_0〜2.png（assets/images/stage4/）

  - 遠景（bg_sky）: 堂の中の絵。高さ 270 に合わせ、少し大きくして下を切り、左右に流せる幅（約 540）にする
  - 中景（bg_mid）: 絵の両端の、金の柱を切り出して、間をあけて並べる（奥行きが出る）
  - タイル: 床の上端は、金の蓮の文様（tile_01）。下は、黒漆・朱の漆・古い石（tile_00・03・04・05）
  - 足場: 光る蓮の台（stone_0〜2）。「照らされた場所だけ乗れる」仕掛けは、まだ無い（見た目だけ）
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import make_stage3 as m3  # noqa: E402

SKY_H = 300
PILLARS = ((135, 235), (1145, 1245))      # 元絵の、柱の横の範囲（左・右）
MID_W = 1500
PILLAR_AT = (60, 380, 700, 1020, 1340)


def make_sky(src, out):
    im = Image.open(src).convert("RGB")
    im = im.resize((round(im.width * SKY_H / im.height), SKY_H), Image.LANCZOS).crop((0, 0, round(im.width * SKY_H / im.height), 270))
    im = im.quantize(colors=56, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    im.save(out, optimize=True)
    return im.size


def make_mid(src, out):
    big = Image.open(src).convert("RGB")
    scale = 270 / big.height
    canvas = Image.new("RGBA", (MID_W, 270), (0, 0, 0, 0))
    for i, x in enumerate(PILLAR_AT):
        x0, x1 = PILLARS[i % 2]
        col = big.crop((x0, 0, x1, big.height)).resize((max(1, round((x1 - x0) * scale)), 270), Image.BOX)
        rgba = col.convert("RGBA")
        px = rgba.load()
        for yy in range(rgba.height):
            for xx in range(rgba.width):
                r, g, b, _ = px[xx, yy]
                px[xx, yy] = (r, g, b, 255 if r + g > 150 else 0)    # 金の部分だけ残す（暗い奥は、透明）
        canvas.alpha_composite(rgba, (x, 0))
    canvas = canvas.convert("RGBA")
    q = canvas.convert("RGB").quantize(colors=24, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGBA")
    q.putalpha(canvas.getchannel("A"))
    q.save(out, optimize=True)
    return q.size


def make_tiles(src, out_dir):
    img = Image.open(src).convert("RGB")
    bs = m3.boxes(img, row_gap=12)
    # 並びは、行→列: 0木の板 1金の蓮の文様 2黒漆 / 3朱の漆（飾り） 4光る蓮 5古い石 / 6朱の漆 7光る蓮（台） 8古い石
    if len(bs) != 9:
        raise SystemExit("タイルが9枚見つかりません（%d枚）: %s" % (len(bs), bs))
    os.makedirs(out_dir, exist_ok=True)
    x0, y0, x1, y1 = bs[1]
    top = m3.fit_width(img, (x0, y0, x1, y0 + round((y1 - y0) * 0.78)), 32, 20)   # 床の上端: 金の蓮の文様の上のほう
    top.save(os.path.join(out_dir, "tile_01.png"))
    for i, k in {0: 2, 3: 3, 4: 5, 5: 6, 2: 8}.items():
        m3.square_tile(img, bs[k]).save(os.path.join(out_dir, "tile_%02d.png" % i))
    stones = [m3.stone(img, bs[4], 45, 0.7), m3.stone(img, bs[7], 48, 0.7)]
    stones.append(stones[0].transpose(Image.FLIP_LEFT_RIGHT))
    for i, s in enumerate(stones):
        s.save(os.path.join(out_dir, "stone_%d.png" % i))
    return top.size, [s.size for s in stones]


if __name__ == "__main__":
    src, out = sys.argv[1:3]
    os.makedirs(out, exist_ok=True)
    print("遠景", make_sky(os.path.join(src, "stage4_bg.jpg"), os.path.join(out, "bg_sky.png")))
    print("中景（柱）", make_mid(os.path.join(src, "stage4_bg.jpg"), os.path.join(out, "bg_mid.png")))
    print("タイル（上端・足場）", make_tiles(os.path.join(src, "stage4_tiles.jpg"), out))
