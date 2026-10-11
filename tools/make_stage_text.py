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
    (1, "第一面", "月見坂", "杉の参道", "月見坂"),
    (2, "第二面", "毛越寺", "浄土の庭", "毛越寺"),
    (3, "第三面", "高館", "衣川を望む", "高館"),
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
    H = max(i.height for i in imgs)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = 0
    # 右から左へ読むので、左に副題、中央に地名、右に「第N面」。上端は、地名にそろえる（副題は少し下げる）
    for k, img in enumerate(imgs):
        top = {0: 36, 1: 0, 2: 10}[k]
        out.alpha_composite(img, (x, top))
        x += img.width + gap
    out.save(path)
    return out.size


def stele(font_path, base, text, path):
    """石碑の平らな面（絵の中央の、少し濃い四角）に、地名を縦書きで彫る"""
    img = Image.open(base).convert("RGBA")
    mask = column(font_path, text, 12, 1)
    w, h = img.size
    x = (w - mask.width) // 2
    y = (h - mask.height) // 2 - 3
    px = img.load()
    mp = mask.load()
    for yy in range(mask.height):
        for xx in range(mask.width):
            if mp[xx, yy]:
                px[x + xx, y + yy + 1] = (205, 196, 170, 255)   # 彫った文字の、下の縁（光を受ける）
    for yy in range(mask.height):
        for xx in range(mask.width):
            if mp[xx, yy]:
                px[x + xx, y + yy] = (52, 46, 38, 255)          # 文字（くぼみ）
    img.save(path)


if __name__ == "__main__":
    font, src, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    for n, num, name, sub, stone in STAGES:
        size = stage_title(font, num, name, sub, os.path.join(out, f"stage_title_{n}.png"))
        base = os.path.join(src, "stele_a.png" if len(stone) >= 3 else "stele_b.png")
        stele(font, base, stone, os.path.join(out, f"stele_{n}.png"))
        print(n, name, size)
