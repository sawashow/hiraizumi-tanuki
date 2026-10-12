"""3面ボス（秀衡「鬼角薙将」）のシート（白背景・いろいろな姿が散らばっている）から、使う姿を選んで、ゲーム用のコマにする。

使い方: python tools/make_boss3.py シート.jpg 出力フォルダ [--height 96] [--chunk 1] [--colors 16] [--list]
  --list   見つけた姿の番号と位置だけ表示し、番号入りの確認画像（出力フォルダ/boss3_list.png）を書く

姿は、背の高い順ではなく、「上の行 → 次の行」、「左 → 右」の順に番号が付く。ゲームで使う姿は、NAMES に番号で書く:
  walk（歩き）3 / stance（構え。光波の予告）3 / swing（薙刀を振り上げる・振り下ろす）2 / death（のけぞる・倒れる・消える）3
どの姿も、そのコマだけの画素を使う（隣の絵と重なっていても、混ざらない）。
ドットの粗さは --chunk（既定は1。泰衡・基衡と同じ。2にすると、2ドット角になって、秀衡だけ粗く見える）。
全コマ同じ縮尺（歩きの高さが --height ドット）・同じ少数色・同じ枠（足元と、体の横の中心をそろえる）にして、
出力フォルダに boss3_動き_番号.png と、確認用の boss3_sheet.png を書く。
"""
import argparse
import colorsys
import os
import statistics
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import make_enemy as me  # noqa: E402
from slice_sheet import components  # noqa: E402

# 動き → 使う姿の番号（--list で確かめる）
# 元絵は boss3_sheet2.jpg（2026-10-12。泰衡と同じ条件で描き直したもの）。前の boss3_sheet.jpg は、絵画ふうで、ほかの絵から浮いた
NAMES = {"walk": (3, 4, 5, 6), "stance": (0, 1, 2), "low": (7, 8), "high": (9, 10), "swing": (11, 12),
         "crouch": (13, 14), "leap": (15, 16), "death": (17, 18, 18)}
# 左を向いている姿があれば、番号をここに書く（反転して、右向きにそろえる。ゲームは、右向きを元にして、左向きは反転する）
FLIP = set()
WHITE = 225       # 腕と体のすき間などに、囲まれて残った白（背景）は、消す
MIN_PTS = 800     # これより小さい塊は、飾り（炎の粒など）として、無視する
COLORS = 14
RIM = (214, 132, 72)   # うすい橙の縁取り（暗い体を、夜の背景から浮かせる。泰衡の、うす紫の縁取りと同じ役目）


def tint(color, sat, gain):
    """元絵は、全身が同じこげ茶。明るい色（角・包帯）は骨の色に、中間の色（鎧）は朱に寄せて、部位を見分けられるようにする。
    暗い色（輪郭）は、変えない"""
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in color))
    if v < 0.16:
        return color
    if v > 0.36:
        h, s, v = 0.11, s * 0.55, min(1.0, v * gain)          # 骨の色
    else:
        h, s, v = h * 0.35, min(1.0, s * sat), min(1.0, v * gain)   # 朱
    return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))


def find_poses(img):
    """姿の一覧（番号順）: (外接矩形, 画素の一覧)。大きい見本の1枚絵（巨大な塊）は、除く"""
    poses = []
    for c in components(img):
        pts = c["pts"]
        if len(pts) < MIN_PTS:
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        poses.append(((min(xs), min(ys), max(xs) + 1, max(ys) + 1), pts))
    poses.sort(key=lambda p: (p[0][1] // 150, p[0][0]))
    return poses


def crop_of(img, pose):
    (x0, y0, x1, y1), pts = pose
    out = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    sp, op = img.load(), out.load()
    for x, y in pts:
        if min(sp[x, y][:3]) < WHITE:
            op[x - x0, y - y0] = sp[x, y]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("out")
    ap.add_argument("--height", type=int, default=96)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--chunk", type=int, default=1, help="ドットの粗さ（1 が、ほかのボスと同じ。2 にすると、2ドット角で、秀衡だけ粗く見える）")
    ap.add_argument("--colors", type=int, default=COLORS)
    ap.add_argument("--sat", type=float, default=1.3, help="色の鮮やかさの倍率（元絵は、くすんだ茶。背景に埋もれるので、少し上げる）")
    ap.add_argument("--gain", type=float, default=1.7, help="明るさの倍率")
    a = ap.parse_args()
    img = me.remove_white_bg(me.clean(me.remove_white_bg(Image.open(a.sheet))), erode=False)
    poses = find_poses(img)
    os.makedirs(a.out, exist_ok=True)
    if a.list:
        vis = Image.new("RGBA", img.size, (230, 230, 230, 255))
        vis.alpha_composite(img)
        d = ImageDraw.Draw(vis)
        for i, (b, pts) in enumerate(poses):
            d.rectangle(b, outline=(255, 0, 0))
            d.text((b[0] + 2, b[1] + 2), str(i), fill=(255, 0, 0))
            print(i, b, len(pts))
        vis.save(os.path.join(a.out, "boss3_list.png"))
        return
    crops = {}
    for anim, idx in NAMES.items():
        crops[anim] = []
        for i in idx:
            c = crop_of(img, poses[i])
            crops[anim].append(c.transpose(Image.FLIP_LEFT_RIGHT) if i in FLIP else c)
    # 粗さ（chunk）ぶん小さく作って、あとで、そのぶん拡大する（1ドットが、chunk ドット角になる）
    scale = a.height / a.chunk / statistics.median(c.height for c in crops["walk"])
    pal = me.palette_from([c for cs in crops.values() for c in cs], a.colors)
    print("元の色", pal)
    pal = [tint(c, a.sat, a.gain) for c in pal]
    pal += [(232, 40, 40), (150, 28, 32)]      # 赤く光る目（面積が小さくて、色を絞ると消えるので、必ず残す）
    placed = []
    for anim, cs in crops.items():
        for i, c in enumerate(cs):
            d = me.add_rim(me.to_dots(c, scale, pal), RIM)     # 縁取りのぶん、絵が外へ1ドット広がる
            placed.append((anim, i, d, me.anchor_x(c, "bbox", scale) + 1, d.height))
    left = max(p[3] for p in placed)
    right = max(p[2].width - p[3] for p in placed)
    up = max(p[4] for p in placed)
    cw, ch = left + right, up
    if a.chunk > 1:
        placed = [(anim, i, d.resize((d.width * a.chunk, d.height * a.chunk), Image.NEAREST), ax * a.chunk, ay * a.chunk)
                  for anim, i, d, ax, ay in placed]
        left, up, cw, ch = left * a.chunk, up * a.chunk, cw * a.chunk, ch * a.chunk
    print("縮尺 %.2f 枠 %d x %d 基準(左,上) = %s" % (scale, cw, ch, (left, up)))
    frames = []
    for anim, i, d, ax, ay in placed:
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.paste(d, (left - ax, up - ay), d)
        canvas.save(os.path.join(a.out, "boss3_%s_%d.png" % (anim, i)))
        frames.append((anim, canvas))
    S, G = 3, 8
    per_row = max(len(v) for v in crops.values())
    sheet = Image.new("RGB", (per_row * (cw * S + G) + G, len(crops) * (ch * S + G) + G), (92, 148, 252))
    for r, anim in enumerate(crops):
        for c, (_, f) in enumerate([f for f in frames if f[0] == anim]):
            big = f.resize((cw * S, ch * S), Image.NEAREST)
            sheet.paste(big, (G + c * (cw * S + G), G + r * (ch * S + G)), big)
    sheet.save(os.path.join(a.out, "boss3_sheet.png"))


if __name__ == "__main__":
    main()
