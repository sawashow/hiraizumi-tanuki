"""エンドロールの「手を挙げて歩く」絵（白背景に、姿が並んだシート）を、ゲーム用のコマにする。タヌキ侍と姫の、両方に使う。

使い方: python tools/make_roll_raise.py シート.jpg 出力フォルダ 名前 --pitch 4.56 --ox 4.5 --oy 2.25 --use 1,2,3,4,6,7 [--flip] [--list]
  元絵は、もともとドット絵（1ドットが、何ピクセルかの四角）。縮めて平均するとぼやけるので、元絵のドットの刻み（--pitch）とずれ（--ox・--oy）に合わせて、
  ますの真ん中の色を拾う（make_hime_walk.py と同じ方式）。刻みとずれは、`python tools/make_hime_walk.py シート.jpg x --measure` で、目安が出る
  （刻みの範囲が合わないときは、その半分・2倍も試す。元絵の1ドットが、実際に何ピクセルかは、絵を拡大して確かめる）。
  背景の白は、外から塗りつぶして透明にする。大きい塊（高さ 30 ドット以上）を、上の行から・左から順に、姿 0〜 として切り出す（見出しの文字は、小さいので入らない）。
  --list: 姿の番号を振った確認画像（出力フォルダ/名前_list.png）を書く
  --use: 使う姿の番号を、コマの順に書く。--flip: 左右を反転する（元絵が右向きで、ゲームが左向きのとき。姫は、左向きの絵）
  --match: 色の平均と広がりを、ゲームの絵に合わせる（元絵が暗い・くすんでいるとき。--palette の前に行う）
  --outline: 縁をなめらかにして、黒に近い色で縁取る（輪郭の欠け・ばらばらの点を消す）
  --palette: 色を、ゲームの絵の色に寄せる（操作時の絵と、色が変わって見えないように）
  --tight: 姿をそろえず、1つずつ、ぴったり切り出す（車など）
  --clean-feet: 足元の白っぽい影（元絵の地面の影）を消す。人物用（車に付けると、ホイールや白い車体も消える）
  足元と、頭の横の位置（上から 3 割の、画素の平均）を、全コマそろえる
実際に使った指定（assets/concept/source/ の元絵。--match と --palette の参照は、assets/images の、ゲーム中の絵）:
  タヌキ侍: tanuki_raise.jpg --pitch 4.56 --ox 4.5 --oy 2.25 --use 0,1,2,3,5,6 --clean-feet --match player_00,02〜07 --palette player_00,02〜07
  姫（2026-10-13 の絵）: hime_chappy2.png --pitch 5.5 --colors 16 --use 0〜14 --outline 24,16,16   （0=立つ 1=喜ぶ 2=驚く 3〜8=歩く 9〜14=手を挙げて歩く）
  車:       ending_cars.jpg  --pitch 9.12 --ox 6.25 --oy 4.75 --colors 20 --use 0,1,2 --tight
出力: 出力フォルダ/名前_0〜.png、確認用の 名前_sheet.png（ゲームは読まない）
"""
import argparse
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from slice_sheet import components, remove_white_bg  # noqa: E402

MIN_H = 30      # 姿とみなす、高さ（ドット）


def sample(raw, pitch, ox, oy, colors):
    """ドットの格子に合わせて、ますの真ん中の色を拾う。少数色にまとめる"""
    img = remove_white_bg(raw, erode=False)
    src = img.load()
    w, h = int((img.width - ox) / pitch), int((img.height - oy) / pitch)
    dots = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dp = dots.load()
    r = max(1, int(pitch / 4))
    for j in range(h):
        for i in range(w):
            cx, cy = int(ox + (i + 0.5) * pitch), int(oy + (j + 0.5) * pitch)
            near = [src[cx + dx, cy + dy] for dx in (-r, 0, r) for dy in (-r, 0, r)]
            solid = [c for c in near if c[3]]
            if len(solid) >= 5:        # ますの真ん中が、絵の中
                dp[i, j] = tuple(sum(c[k] for c in solid) // len(solid) for k in range(3)) + (255,)
    q = dots.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGBA")
    q.putalpha(dots.getchannel("A"))
    return q


def poses(q, clean_feet=False):
    """姿の一覧（上の行から、左から）。(切り出した絵) のリスト"""
    qp = q.load()
    found = [c for c in components(q) if c["box"][3] - c["box"][1] >= MIN_H]
    found.sort(key=lambda c: (round((c["box"][1] + c["box"][3]) / 2 / 40), c["box"][0]))   # 同じ行は、上下が40ドット以内にそろっている
    out = []
    for c in found:
        xs, ys = [p[0] for p in c["pts"]], [p[1] for p in c["pts"]]
        x0, y0 = min(xs), min(ys)
        crop = Image.new("RGBA", (max(xs) - x0 + 1, max(ys) - y0 + 1), (0, 0, 0, 0))
        px = crop.load()
        for x, y in c["pts"]:
            px[x - x0, y - y0] = qp[x, y]
        for y in range(crop.height * 4 // 5, crop.height) if clean_feet else ():      # 足元に残った、白っぽい影を消す
            for x in range(crop.width):
                if px[x, y][3] and min(px[x, y][:3]) > 120:
                    px[x, y] = (0, 0, 0, 0)
        out.append(crop)
    return out


def palette_of(files):
    """ゲームの絵（透明でない画素）に使われている色の一覧"""
    return sorted({p[:3] for f in files for p in Image.open(f).convert("RGBA").getdata() if p[3]})


def stats(ims):
    """透明でない画素の、色の平均と広がり（R・G・B ごと）"""
    px = [p[:3] for im in ims for p in im.getdata() if p[3]]
    n = len(px)
    mean = [sum(p[k] for p in px) / n for k in range(3)]
    std = [(sum((p[k] - mean[k]) ** 2 for p in px) / n) ** 0.5 or 1.0 for k in range(3)]
    return mean, std


def transfer(ims, ref_files):
    """色の平均と広がりを、ゲームの絵に合わせる（元絵のほうが暗い・くすんでいるのを、そろえる）"""
    m1, s1 = stats(ims)
    m2, s2 = stats([Image.open(f).convert("RGBA") for f in ref_files])
    for im in ims:
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                c = px[x, y]
                if c[3]:
                    px[x, y] = tuple(max(0, min(255, round((c[k] - m1[k]) / s1[k] * s2[k] + m2[k]))) for k in range(3)) + (255,)
    return ims


def remap(im, pal):
    """各画素を、いちばん近い色（人の目に近い重みの距離）に置き換える"""
    px = im.load()
    cache = {}
    for y in range(im.height):
        for x in range(im.width):
            c = px[x, y]
            if c[3]:
                if c[:3] not in cache:
                    cache[c[:3]] = min(pal, key=lambda q: 2 * (q[0] - c[0]) ** 2 + 4 * (q[1] - c[1]) ** 2 + 3 * (q[2] - c[2]) ** 2)
                px[x, y] = cache[c[:3]] + (255,)
    return im


def smooth_edges(im, outline):
    """輪郭をなめらかにして、黒に近い線で縁取る。
    (1) 3×3 の多数決で、ばらばらの点を消し、欠けを埋める  (2) 縁の画素のうち、明るいものを、輪郭の色にする（縁取りを、1ドットの太さにそろえる）"""
    w, h = im.size
    px = im.load()
    solid = [[px[x, y][3] > 0 for x in range(w)] for y in range(h)]

    def count(m, x, y):
        return sum(1 for dy in (-1, 0, 1) for dx in (-1, 0, 1) if 0 <= x + dx < w and 0 <= y + dy < h and m[y + dy][x + dx])

    new = [[count(solid, x, y) >= 5 for x in range(w)] for y in range(h)]
    out = im.copy()
    op = out.load()
    for y in range(h):
        for x in range(w):
            if new[y][x] and not solid[y][x]:
                op[x, y] = outline + (255,)         # 埋めた画素は、輪郭の色
            elif not new[y][x]:
                op[x, y] = (0, 0, 0, 0)             # ばらばらの点・とび出た画素は、消す
    for y in range(h):
        for x in range(w):
            if not new[y][x]:
                continue
            edge = any(not (0 <= x + dx < w and 0 <= y + dy < h and new[y + dy][x + dx]) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge and sum(op[x, y][:3]) > 3 * 70:      # 縁で、暗くない画素は、輪郭の色にする
                op[x, y] = outline + (255,)
    return out


def head_x(d):
    """頭の横の位置: 上から 3 割の範囲の、画素の平均"""
    px = d.load()
    xs = [x for y in range(max(1, d.height * 3 // 10)) for x in range(d.width) if px[x, y][3]]
    return round(sum(xs) / len(xs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("out")
    ap.add_argument("name")
    ap.add_argument("--pitch", type=float, required=True)
    ap.add_argument("--ox", type=float, default=0.0)
    ap.add_argument("--oy", type=float, default=0.0)
    ap.add_argument("--colors", type=int, default=16)
    ap.add_argument("--use", default="")
    ap.add_argument("--flip", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--match", default="", help="色の平均と広がりを、この画像（「,」区切り。ゲームの絵）に合わせる")
    ap.add_argument("--palette", default="", help="色を、この画像（「,」区切り。ゲームの絵）の色に寄せる。操作時の絵と、色をそろえるため")
    ap.add_argument("--outline", default="", help="縁を、なめらかにして、この色（R,G,B）で縁取る。人物用（ばらばらの点・欠けが消える）")
    ap.add_argument("--tight", action="store_true", help="そろえずに、1つずつ、ぴったり切り出す（車など。足元は、絵の下端）")
    ap.add_argument("--clean-feet", action="store_true", help="足元の白っぽい影を消す（人物用。車には付けない。ホイールや白い車体も消えるため）")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    crops = poses(sample(Image.open(a.sheet), a.pitch, a.ox, a.oy, a.colors), a.clean_feet)
    if a.list or not a.use:
        sheet = Image.new("RGB", (sum(c.width * 4 + 8 for c in crops) + 8, max(c.height for c in crops) * 4 + 24), (120, 170, 230))
        x = 8
        for i, c in enumerate(crops):
            big = c.resize((c.width * 4, c.height * 4), Image.NEAREST)
            sheet.paste(big, (x, 20), big)
            x += big.width + 8
            print(i, c.size)
        sheet.save(os.path.join(a.out, a.name + "_list.png"))
        return
    picked = [crops[int(u)] for u in a.use.split(",")]
    if a.outline:
        picked = [smooth_edges(d, tuple(int(v) for v in a.outline.split(","))) for d in picked]
    if a.match:
        picked = transfer(picked, a.match.split(","))
    if a.palette:
        pal = palette_of(a.palette.split(","))
        picked = [remap(d, pal) for d in picked]
    if a.flip:
        picked = [d.transpose(Image.FLIP_LEFT_RIGHT) for d in picked]
    if a.tight:
        for i, d in enumerate(picked):
            d.save(os.path.join(a.out, "%s_%d.png" % (a.name, i)))
            print(i, d.size)
        return
    hx = [head_x(d) for d in picked]
    pad = max(hx)
    cw = max(d.width + pad - h for d, h in zip(picked, hx))
    ch = max(d.height for d in picked)
    sheet = Image.new("RGB", (len(picked) * (cw * 4 + 8) + 8, ch * 4 + 16), (120, 170, 230))
    for i, (d, h) in enumerate(zip(picked, hx)):
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.paste(d, (pad - h, ch - d.height), d)
        canvas.save(os.path.join(a.out, "%s_%d.png" % (a.name, i)))
        big = canvas.resize((cw * 4, ch * 4), Image.NEAREST)
        sheet.paste(big, (8 + i * (cw * 4 + 8), 8), big)
    sheet.save(os.path.join(a.out, a.name + "_sheet.png"))
    print("枠 %d x %d" % (cw, ch))


if __name__ == "__main__":
    main()
