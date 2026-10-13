"""食べ物の絵（白背景に、並んだ物）を、ゲーム用の小さな絵（assets/images/items/food_*.png）にする。タヌキ侍の、頭の中の吹き出しに出る。

使い方: python tools/make_foods.py シート.jpg 出力フォルダ --pitch 6.5 [--list] [--use 0,1,... --names wanko,reimen,...]
  元絵: assets/concept/source/foods.jpg（Gemini。2列×6行。同じ物が2つずつある）
  元絵のドットの刻み（--pitch）に合わせて、ますの真ん中の色を拾い（縮めて平均するとぼやける）、少数色にまとめる。
  塊を、上の行から・左から順に、番号 0〜 として切り出す（湯気の小さな塊は、すぐそばの塊に入れる）。--list で、番号を振った確認画像を書く。
  --use に番号、--names に名前を、同じ数だけ書くと、出力フォルダ/food_名前.png を書く。
"""
import argparse
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import make_roll_raise as mr  # noqa: E402
from slice_sheet import components  # noqa: E402


def foods(raw, pitch, colors):
    q = mr.sample(raw, pitch, 0.0, 0.0, colors)
    found = sorted(components(q), key=lambda c: -len(c["pts"]))
    big = [c for c in found if len(c["pts"]) >= 40]
    for c in found:
        if c in big:
            continue
        for m in big:       # 湯気などの小さな塊は、すぐそばの大きな塊に入れる
            (a0, b0, a1, b1), (x0, y0, x1, y1) = c["box"], m["box"]
            if max(x0 - a1, a0 - x1, 0) + max(y0 - b1, b0 - y1, 0) <= 8:
                m["pts"] = list(m["pts"]) + list(c["pts"])
                break
    qp = q.load()
    out = []
    for c in big:
        xs, ys = [p[0] for p in c["pts"]], [p[1] for p in c["pts"]]
        x0, y0 = min(xs), min(ys)
        crop = Image.new("RGBA", (max(xs) - x0 + 1, max(ys) - y0 + 1), (0, 0, 0, 0))
        px = crop.load()
        for x, y in c["pts"]:
            px[x - x0, y - y0] = qp[x, y]
        out.append((((y0 + max(ys)) / 2, (x0 + max(xs)) / 2), crop))
    rows = []       # 行ごとにまとめる（行の中心が、12 ドット以内）
    for key, crop in sorted(out, key=lambda o: o[0]):
        if rows and abs(rows[-1][0] - key[0]) <= 12:
            rows[-1][1].append((key[1], crop))
        else:
            rows.append([key[0], [(key[1], crop)]])
    return [crop for _, r in rows for _, crop in sorted(r, key=lambda t: t[0])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("out")
    ap.add_argument("--pitch", type=float, required=True)
    ap.add_argument("--colors", type=int, default=24)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--use", default="")
    ap.add_argument("--names", default="")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    crops = foods(Image.open(a.sheet), a.pitch, a.colors)
    if a.list or not a.use:
        sheet = Image.new("RGB", (sum(c.width * 5 + 8 for c in crops) + 8, max(c.height for c in crops) * 5 + 24), (120, 170, 230))
        x = 8
        for i, c in enumerate(crops):
            big = c.resize((c.width * 5, c.height * 5), Image.NEAREST)
            sheet.paste(big, (x, 20), big)
            x += big.width + 8
            print(i, c.size)
        sheet.save(os.path.join(a.out, "foods_list.png"))
        return
    for i, name in zip((int(v) for v in a.use.split(",")), a.names.split(",")):
        crops[i].save(os.path.join(a.out, "food_%s.png" % name))
        print(name, crops[i].size)


if __name__ == "__main__":
    main()
