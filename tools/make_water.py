"""池の水面のタイル（白背景・横一列に、水面A・水面B・水中の3枚。見出しの文字は無視する）を、ゲーム用に変換する。
使い方: python tools/make_water.py シート.jpg 出力フォルダ [色数=14]
  - 白い背景で、3枚を見つけて、切り出す（下の見出しの文字は、四角の下の端で切り捨てる）
  - 水面は 32×16、水中は 32×32 に縮小する。3枚をまとめて減色し、水面Aと水面Bの色をそろえる
  - 横に並べても、継ぎ目が見えないように、左右の端をなじませる
出力: 出力フォルダ/water_top_0.png, water_top_1.png, water_fill.png
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from make_tiles import runs  # noqa: E402

BG_MIN = 238


def panels(img):
    w, h = img.size
    px = img.load()
    nonwhite = lambda x, y: min(px[x, y]) < BG_MIN
    cols = [c for c in runs([any(nonwhite(x, y) for y in range(0, h, 3)) for x in range(w)], 12) if c[1] - c[0] > 60]
    out = []
    for x0, x1 in cols:
        rows = runs([sum(nonwhite(x, y) for x in range(x0, x1, 3)) > (x1 - x0) // 12 for y in range(h)], 6)
        y0, y1 = max(rows, key=lambda r: r[1] - r[0])        # 四角の帯（見出しの文字は、その下の別の帯）
        out.append((x0, y0, x1, y1))
    return out


def seamless(img):
    """左右の端をなじませて、横につないでも継ぎ目が出ないようにする"""
    w, h = img.size
    px = img.load()
    out = img.copy()
    op = out.load()
    for x in range(w):
        k = 1 - abs(2 * x / w - 1)       # 端で0、中央で1
        for y in range(h):
            a, b = px[x, y], px[(x + w // 2) % w, y]
            op[x, y] = tuple(round(a[i] * k + b[i] * (1 - k)) for i in range(3))
    return out


def main(src, out_dir, colors=14):
    img = Image.open(src).convert("RGB")
    ps = panels(img)
    print("見つけた枚数:", len(ps), ps)
    sizes = [(32, 16), (32, 16), (32, 32)]
    small = [seamless(img.crop(b).resize(s, Image.BOX)) for b, s in zip(ps, sizes)]
    # 3枚をまとめて減色（水面Aと水面Bの色をそろえる）
    sheet = Image.new("RGB", (96, 32))
    for i, t in enumerate(small):
        sheet.paste(t, (i * 32, 0))
    q = sheet.quantize(colors, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    os.makedirs(out_dir, exist_ok=True)
    for i, (name, s) in enumerate(zip(("water_top_0", "water_top_1", "water_fill"), sizes)):
        q.crop((i * 32, 0, i * 32 + s[0], s[1])).save(os.path.join(out_dir, name + ".png"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 14)
