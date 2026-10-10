"""地面タイルのシート（白背景・2行3列）を、32ドット幅のタイルに変換する。

使い方: python tools/make_tiles.py シート.jpg 出力フォルダ [タイルの幅=32] [色数=14] [色味=R,G,B の倍率 例 0.75,0.68,0.8]
  - 白い背景を除いて、行→列の順に6枚を切り出す
  - 全タイル同じ縮尺（最も幅の広いタイルが指定の幅）。高さが半分ほどの断面タイルは、高さも自動で半分になる
出力: tile_00.png ... と、確認用の tiles_sheet.png（6倍）
"""
import os
import sys

from PIL import Image

BG_MIN = 235


def runs(flags, merge_gap=0):
    out, start, last = [], None, None
    for i, f in enumerate(flags):
        if f:
            if start is None:
                start = i
            elif merge_gap and i - last > merge_gap:
                out.append((start, last + 1))
                start = i
            last = i
    if start is not None:
        out.append((start, last + 1))
    return out


def boxes(img):
    w, h = img.size
    px = img.load()
    m = [[min(px[x, y]) < BG_MIN for x in range(w)] for y in range(h)]
    rows = [r for r in runs([any(m[y]) for y in range(h)], 30) if r[1] - r[0] > 40]
    out = []
    for y0, y1 in rows:
        cols = [c for c in runs([any(m[y][x] for y in range(y0, y1)) for x in range(w)], 8) if c[1] - c[0] > 40]
        for x0, x1 in cols:
            ys = [y for y in range(y0, y1) if any(m[y][x] for x in range(x0, x1))]
            out.append((x0, ys[0], x1, ys[-1] + 1))
    return out


def main(src, out_dir, width=32, colors=14, tint=(1.0, 1.0, 1.0)):
    img = Image.open(src).convert("RGB")
    bs = boxes(img)
    print("タイル数:", len(bs), [(b[2] - b[0], b[3] - b[1]) for b in bs])
    scale = width / max(b[2] - b[0] for b in bs)
    os.makedirs(out_dir, exist_ok=True)
    tiles = []
    for i, b in enumerate(bs):
        c = img.crop(b)
        w, h = round(c.width * scale), round(c.height * scale)
        small = c.resize((w, h), Image.BOX)
        q = small.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGBA")
        # 縮小の丸めで 31 になったものは、並べたときに隙間が出ないよう 32 にそろえる
        if abs(q.width - width) <= 1:
            q = q.resize((width, q.height if abs(q.height - width) > 3 else width), Image.NEAREST)
        qp = q.load()
        for y in range(q.height):
            for x in range(q.width):
                r, g, b, a = qp[x, y]
                qp[x, y] = (round(r * tint[0]), round(g * tint[1]), round(b * tint[2]), a)
        q.save(os.path.join(out_dir, f"tile_{i:02d}.png"))
        tiles.append(q)
    S, G = 6, 8
    sheet = Image.new("RGB", (len(tiles) * (width * S + G) + G, width * S + 2 * G), (92, 148, 252))
    for i, t in enumerate(tiles):
        big = t.resize((t.width * S, t.height * S), Image.NEAREST)
        sheet.paste(big, (G + i * (width * S + G), G))
    sheet.save(os.path.join(out_dir, "tiles_sheet.png"))


if __name__ == "__main__":
    tint = tuple(float(v) for v in sys.argv[5].split(",")) if len(sys.argv) > 5 else (1.0, 1.0, 1.0)
    main(sys.argv[1], sys.argv[2],
         int(sys.argv[3]) if len(sys.argv) > 3 else 32,
         int(sys.argv[4]) if len(sys.argv) > 4 else 14, tint)
