"""スタート画面の題名を、昔のゲームのロゴ風の絵に書き出す（ゲームにフォントを入れずに出すため）。

使い方: python tools/make_title_logo.py 太いフォント.ttf ドット風フォント.ttf 出力.png
  - 上に小さく「平泉」（朱の札に白い字）、下に大きく「タヌキ侍」、その下に小さく英字
  - 大きい字は、斜めに傾けて、金から朱への色の段（真ん中に光の線）、黒い縁取り、右下に厚み（影）を付ける
  - アンチエイリアスなしで書き出す（ドットをそのまま出す）
使っているフォント: 太い字は M PLUS 1p Black、小さい字は DotGothic16（どちらも SIL Open Font License 1.1）
"""
import sys

from PIL import Image, ImageDraw, ImageFont

INK = (16, 10, 24, 255)        # 縁取り
DEPTH = (120, 16, 24, 255)     # 厚み（暗い朱）
PLATE = (200, 40, 32, 255)     # 札の朱
WHITE = (252, 252, 252, 255)
# 大きい字の色の段（上から）: 白っぽい金 → 金 → 光の線 → 橙 → 朱
BANDS = ((0.00, (255, 248, 176)), (0.30, (252, 208, 40)), (0.50, (255, 255, 224)),
         (0.56, (240, 136, 24)), (1.00, (200, 40, 32)))


def text_mask(font, text, spacing=0):
    """文字の形（白黒）。アンチエイリアスなし"""
    widths = [font.getbbox(ch) for ch in text]
    top = min(b[1] for b in widths)
    bottom = max(b[3] for b in widths)
    total = sum(b[2] - b[0] for b in widths) + spacing * (len(text) - 1)
    img = Image.new("L", (total, bottom - top), 0)
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    x = 0
    for ch, b in zip(text, widths):
        d.text((x - b[0], -top), ch, font=font, fill=255)
        x += b[2] - b[0] + spacing
    return img.point(lambda v: 255 if v >= 128 else 0)


def shear(mask, slant):
    """右に傾ける（上ほど右へ）"""
    w, h = mask.size
    extra = int(round(h * slant))
    return mask.transform((w + extra, h), Image.AFFINE, (1, slant, -extra, 0, 1, 0), Image.NEAREST)


def grow(mask, n):
    """形を、まわりに n ドット太らせる"""
    w, h = mask.size
    out = Image.new("L", (w + 2 * n, h + 2 * n), 0)
    for dy in range(-n, n + 1):
        for dx in range(-n, n + 1):
            out.paste(255, (n + dx, n + dy), mask)
    return out


def band_color(t):
    for (t0, c0), (t1, c1) in zip(BANDS, BANDS[1:]):
        if t <= t1:
            k = (t - t0) / (t1 - t0) if t1 > t0 else 0
            k = round(k * 3) / 3    # 色の段を、はっきり分ける（なめらかにしない）
            return tuple(round(a + (b - a) * k) for a, b in zip(c0, c1)) + (255,)
    return BANDS[-1][1] + (255,)


def big_word(font, text, slant=0.18, outline=2, depth=3):
    face = shear(text_mask(font, text, spacing=1), slant)
    w, h = face.size
    edge = grow(face, outline)
    out = Image.new("RGBA", (edge.width + depth, edge.height + depth), (0, 0, 0, 0))
    for i in range(depth, 0, -1):   # 厚み: 右下へずらして重ねる（外側ほど暗い縁）
        out.paste(INK if i == depth else DEPTH, (i, i), edge)
    out.paste(INK, (0, 0), edge)
    fill = Image.new("RGBA", (w, h))
    px = fill.load()
    for y in range(h):
        c = band_color(y / max(1, h - 1))
        for x in range(w):
            px[x, y] = c
    out.paste(fill, (outline, outline), face)
    return out


def plate(font, text, pad=3):
    m = text_mask(font, text, spacing=2)
    w, h = m.width + pad * 2 + 2, m.height + pad * 2 + 2
    out = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    d.rectangle((2, 2, w + 1, h + 1), fill=INK)                 # 影
    d.rectangle((0, 0, w - 1, h - 1), fill=INK)
    d.rectangle((1, 1, w - 2, h - 2), fill=PLATE)
    d.rectangle((2, 2, w - 3, 2), fill=(240, 136, 24, 255))     # 上の縁の光
    out.paste(WHITE, (pad + 1, pad + 1), m)
    return out


def small_text(font, text):
    m = text_mask(font, text)
    edge = grow(m, 1)
    out = Image.new("RGBA", edge.size, (0, 0, 0, 0))
    out.paste(INK, (0, 0), edge)
    out.paste(WHITE, (1, 1), m)
    return out


def main(bold_path, dot_path, out_path):
    big = big_word(ImageFont.truetype(bold_path, 46), "タヌキ侍")
    top = plate(ImageFont.truetype(bold_path, 20), "平泉")
    sub = small_text(ImageFont.truetype(dot_path, 16), "HIRAIZUMI TANUKI SAMURAI")
    w = max(big.width, sub.width, top.width + 10)
    out = Image.new("RGBA", (w, top.height - 4 + big.height + 3 + sub.height), (0, 0, 0, 0))
    bx = (w - big.width) // 2
    out.alpha_composite(big, (bx, top.height - 4))
    out.alpha_composite(top, (bx + 4, 0))       # 札は、大きい字の左上に、少し重ねる
    out.alpha_composite(sub, ((w - sub.width) // 2, top.height - 4 + big.height + 3))
    out.save(out_path)
    print("書き出し:", out_path, out.size)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
