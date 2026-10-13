"""面の名前の画像（縦書き）と、石碑に地名を彫った画像を、ドット風フォントで作る。
使い方: python tools/make_stage_text.py フォント.ttf 石碑の元絵フォルダ 出力フォルダ
  - stage_title_N.png: 面の始まりに出す、縦書きの名前（右に「第N面」、中央に地名、左に副題）
  - stele_N.png: 石碑の絵の、平らな面に、地名を縦書きで彫ったもの
使っているフォント: DotGothic16（SIL Open Font License 1.1）
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

STAGES = (
    # (番号, 第N面, 地名, 副題, 石碑の地名)
    # 遊ぶ順は、実際の地理に合わせる（南から北へ。月見坂の上が金色堂）
    (1, "第一面", "毛越寺", "浄土の庭", "毛越寺"),
    (2, "第二面", "高館", "衣川を望む", "高館"),
    (3, "第三面", "月見坂", "杉の参道", "月見坂"),
    (4, "第四面", "金色堂", "黄金の眠り", "金色堂"),
)


def glyph(font, ch, size):
    """1文字を、アンチエイリアスなしで、size×size の白いマスクにする"""
    img = Image.new("L", (size + 4, size + 4), 0)
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    l, t, r, b = font.getbbox(ch)
    d.text((2 + (size - (r - l)) // 2 - l, 2 + (size - (b - t)) // 2 - t), ch, font=font, fill=255)
    return img.point(lambda v: 255 if v >= 128 else 0)


def column(font_path, text, size, scale):
    """縦書きの1列（白い字）。1文字ごとに積む"""
    font = ImageFont.truetype(font_path, size)
    gs = [glyph(font, c, size) for c in text]
    w, h = gs[0].size
    col = Image.new("L", (w, h * len(gs) - 2 * (len(gs) - 1)), 0)
    for i, g in enumerate(gs):
        col.paste(g, (0, i * (h - 2)), g)
    return col.resize((col.width * scale, col.height * scale), Image.NEAREST)


def outlined(mask, pad=2):
    """白い字に、暗い縁取りを付けた RGBA にする"""
    w, h = mask.size
    out = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    dark = Image.new("L", (w + pad * 2, h + pad * 2), 0)
    for dx in range(-pad, pad + 1):
        for dy in range(-pad, pad + 1):
            dark.paste(255, (pad + dx, pad + dy), mask)
    out.paste((12, 10, 20, 255), (0, 0), dark)
    out.paste((252, 252, 252, 255), (pad, pad), mask)
    return out


def stage_title(font_path, num, name, sub, path):
    cols = [(column(font_path, sub, 16, 2), "left"), (column(font_path, name, 16, 4), "mid"), (column(font_path, num, 16, 2), "right")]
    imgs = [outlined(c) for c, _ in cols]
    gap = 14
    W = sum(i.width for i in imgs) + gap * 2
    tops = (36, 0, 10)      # 上端は、地名にそろえる（副題は少し下げる）
    H = max(i.height + t for i, t in zip(imgs, tops))     # 下げた分も入れる（副題が長い面で、下が切れないように）
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = 0
    # 右から左へ読むので、左に副題、中央に地名、右に「第N面」。上端は、地名にそろえる（副題は少し下げる）
    for k, img in enumerate(imgs):
        top = tops[k]
        out.alpha_composite(img, (x, top))
        x += img.width + gap
    out.save(path)
    return out.size


PANEL_B = (8, 15, 21, 49)    # 角柱の石碑（stele_b）の、枠の内側（左, 上, 右, 下）。字は、この真ん中に置く


def stele(font_path, base, text, path, panel=None):
    """石碑の平らな面（絵の中央の、少し濃い四角）に、地名を縦書きで彫る。
    panel（枠の内側）を渡すと、字そのものの範囲を、その真ん中に合わせる（枠の線に、字が重ならないように）"""
    img = Image.open(base).convert("RGBA")
    mask = column(font_path, text, 12, 1)
    w, h = img.size
    x = (w - mask.width) // 2
    y = (h - mask.height) // 2 - 3
    if panel:
        l, t, r, b = mask.getbbox()
        x = panel[0] + (panel[2] - panel[0] - (r - l) + 1) // 2 - l
        y = panel[1] + (panel[3] - panel[1] - (b - t)) // 2 - t
    edge = (158, 152, 134, 255) if panel else (205, 196, 170, 255)   # 枠の中の小さい字は、光を弱くする（字の形が、つぶれないように）
    px = img.load()
    mp = mask.load()
    for yy in range(mask.height):
        for xx in range(mask.width):
            if mp[xx, yy]:
                px[x + xx, y + yy + 1] = edge   # 彫った文字の、下の縁（光を受ける）
    for yy in range(mask.height):
        for xx in range(mask.width):
            if mp[xx, yy]:
                px[x + xx, y + yy] = (52, 46, 38, 255)          # 文字（くぼみ）
    img.save(path)


def lacquer(path):
    """石碑を、堂の中に合う「黒漆に金文字の碑」に塗り替える（金色堂用。苔むした石は、堂の中では浮く）。
    草・苔（緑）は消す。暗い所（輪郭・彫った字）は金に、石の面は、黒漆（明るい所ほど、朱がかった艶）にする"""
    img = Image.open(path).convert("RGBA")
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            lum = (r + g + b) / 3
            if g > r + 10 and g > b + 10 or y >= img.height - 11 and not 9 <= x <= 30:     # 草・苔と、足元の左右にはみ出した草の影
                px[x, y] = (0, 0, 0, 0)
            elif lum < 70:
                px[x, y] = (236, 196, 84, 255)
            elif lum < 105:
                px[x, y] = (170, 122, 40, 255)
            else:
                k = min(1.0, (lum - 105) / 110)
                px[x, y] = (round(26 + 44 * k), round(16 + 16 * k), round(16 + 8 * k), 255)
    for y in range(img.height):     # 草を消して、離れ小島になった点を、消す
        for x in range(img.width):
            if px[x, y][3] and not any(0 <= x + dx < img.width and 0 <= y + dy < img.height and px[x + dx, y + dy][3]
                                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = (0, 0, 0, 0)
    img.save(path)


if __name__ == "__main__":
    font, src, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    for n, num, name, sub, stone in STAGES:
        size = stage_title(font, num, name, sub, os.path.join(out, f"stage_title_{n}.png"))
        wide = len(stone) >= 3      # 3文字は、自然石の石碑。2文字は、角柱の石碑
        base = os.path.join(src, "stele_a.png" if wide else "stele_b.png")
        stele(font, base, stone, os.path.join(out, f"stele_{n}.png"), None if wide else PANEL_B)
        if n == 4:
            lacquer(os.path.join(out, f"stele_{n}.png"))
        print(n, name, size)
