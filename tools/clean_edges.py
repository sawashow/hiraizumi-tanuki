"""ボスなどの絵の、縁のぎざぎざ（ばらばらの点・欠け・縁の色のまだら）を、整える。細い物（薙刀の柄・矢・扇の骨）は、消さない。

使い方: python tools/clean_edges.py 絵.png ... [--out 出力フォルダ]     （--out が無ければ、上書きする）
  (1) ばらばらの点を消す: 透明でない画素のうち、まわり（8方向）に、絵の画素が 1 つ以下のもの
  (2) 欠けを埋める: 透明な画素のうち、まわりの 6 つ以上が、絵の画素のもの（色は、まわりで、いちばん多い色）
  (3) 縁の色をそろえる: 縁（上下左右のどれかが透明）の画素の色を、まわり（5×5）の縁の画素の中で、いちばん多い色にする（縁の色の、まだらを消す）
  輪郭の形は、ほとんど変わらない。人物用の tools/make_roll_raise.py の --outline（多数決で、輪郭を作り直す）より、控えめ。
"""
import argparse
import os
from collections import Counter

from PIL import Image

N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def clean(im):
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()

    def solid(x, y):
        return 0 <= x < w and 0 <= y < h and px[x, y][3] > 0

    out = im.copy()
    op = out.load()
    for y in range(h):
        for x in range(w):
            n = sum(1 for dx, dy in N8 if solid(x + dx, y + dy))
            if px[x, y][3] and n <= 1:
                op[x, y] = (0, 0, 0, 0)                     # (1) ばらばらの点
            elif not px[x, y][3] and n >= 6:
                cols = Counter(px[x + dx, y + dy][:3] for dx, dy in N8 if solid(x + dx, y + dy))
                op[x, y] = cols.most_common(1)[0][0] + (255,)       # (2) 欠け
    q = out.copy()
    qp = q.load()
    edge = {}
    for y in range(h):
        for x in range(w):
            if qp[x, y][3] and any(not (0 <= x + dx < w and 0 <= y + dy < h and qp[x + dx, y + dy][3]) for dx, dy in N4):
                edge[(x, y)] = qp[x, y][:3]
    for (x, y), c in edge.items():                         # (3) 縁の色
        near = Counter(edge[(x + dx, y + dy)] for dx in range(-2, 3) for dy in range(-2, 3) if (x + dx, y + dy) in edge)
        op[x, y] = near.most_common(1)[0][0] + (qp[x, y][3],)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    for f in a.files:
        dst = os.path.join(a.out, os.path.basename(f)) if a.out else f
        if a.out:
            os.makedirs(a.out, exist_ok=True)
        clean(Image.open(f)).save(dst)
    print("整えた絵:", len(a.files), "枚")


if __name__ == "__main__":
    main()
