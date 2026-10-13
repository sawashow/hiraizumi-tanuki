"""エンドロールの道（真上から見た、歩道・縁石・車道・中央線・マンホール）と、横断歩道の、生成AI（Gemini）の絵を、ゲーム用にする。

使い方: python tools/make_roll_road_ai.py 道の帯.jpg 横断歩道.jpg [出力フォルダ]     （既定: assets/images）
  元絵: assets/concept/source/road_a.jpg（道の帯）・road_b.jpg（横断歩道）
出力:
  roll_road.png   192×116。横にくり返して流す帯（左右が、つながる絵）。上の端は、奥の歩道の上端 = ROLL の road の上端 − 22
  roll_zebra.png  192×116 と同じ高さ（帯と同じ位置に重ねる）。白線だけが残り、ほかは透明（道の中央線や汚れは、帯のまま見える）
道の帯は、元絵の全体を、192×116 の格子に合わせて、ますの真ん中の色を拾い（なめらかに縮めると、ぼやける）、少数色にまとめる。
横断歩道は、元絵のほうが、道が大きく描かれている（車道の高さが、約 1.9 倍）ので、その比で縮めて、白線（クリーム色）だけを拾う。
"""
import os
import sys

from PIL import Image

W, H = 192, 116                     # 帯の大きさ（ドット）
ROAD_TOP_SRC, ROAD_TOP_ROW = 175, 23     # 横断歩道の元絵で、車道が始まる高さ（ピクセル）と、帯の上で、車道が始まる行
ZEBRA_SCALE = 13.0                  # 横断歩道の元絵の、1ドットあたりのピクセル数（車道の高さが、帯の車道と同じになるように）
COLORS = 24


def grid_sample(img, xs, ys, radius):
    """(xs, ys) の位置（ピクセル）の、まわり radius の四角の平均色。範囲外は、はしの色"""
    px = img.load()
    out = []
    for cy in ys:
        row = []
        for cx in xs:
            pts = [px[min(max(int(cx) + dx, 0), img.width - 1), min(max(int(cy) + dy, 0), img.height - 1)]
                   for dx in range(-radius, radius + 1) for dy in range(-radius, radius + 1)]
            row.append(tuple(sum(p[k] for p in pts) // len(pts) for k in range(3)))
        out.append(row)
    return out


def road(src):
    img = Image.open(src).convert("RGB")
    px, py = img.width / W, img.height / H
    rows = grid_sample(img, [(i + 0.5) * px for i in range(W)], [(j + 0.5) * py for j in range(H)], 1)
    dots = Image.new("RGB", (W, H))
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            dots.putpixel((i, j), c)
    return dots.quantize(colors=COLORS, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGBA")


def zebra(src):
    """白線（クリーム色）だけを拾う。帯と同じ高さ・同じ行の位置に置く"""
    img = Image.open(src).convert("RGB")
    s = ZEBRA_SCALE
    cols = int(img.width / s)
    ys = [ROAD_TOP_SRC + (j - ROAD_TOP_ROW + 0.5) * s for j in range(H)]
    rows = grid_sample(img, [(i + 0.5) * s for i in range(cols)], ys, 2)
    cream = [c for row in rows for c in row if c[0] > 225 and c[1] > 220 and c[2] < 225 and c[0] - c[2] > 15]
    mean = tuple(sum(c[k] for c in cream) // len(cream) for k in range(3))
    out = Image.new("RGBA", (cols, H), (0, 0, 0, 0))
    for j, row in enumerate(rows):
        if ys[j] < ROAD_TOP_SRC or ys[j] > ROAD_TOP_SRC + 900:       # 車道の外（歩道）は、拾わない
            continue
        for i, c in enumerate(row):
            if c[0] > 225 and c[1] > 220 and c[2] < 225 and c[0] - c[2] > 15:
                out.putpixel((i, j), mean + (255,))
    box = out.getbbox()
    return out.crop((box[0], 0, box[2], H)), mean


def main(road_src, zebra_src, out):
    os.makedirs(out, exist_ok=True)
    road(road_src).save(os.path.join(out, "roll_road.png"))
    z, mean = zebra(zebra_src)
    z.save(os.path.join(out, "roll_zebra.png"))
    print("書き出し:", out, "道", (W, H), "横断歩道", z.size, "白線の色", mean)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(__file__), "..", "assets", "images"))
