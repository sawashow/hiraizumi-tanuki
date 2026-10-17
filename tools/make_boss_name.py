"""ボスが出てくる場面の、二つ名と名前の絵を書き出す（ゲームにフォントを入れずに出すため）。

使い方: python tools/make_boss_name.py フォント.ttf "首無武者" "くびなしむしゃ" "泰衡" "やすひら" 出力の頭
出力: 出力の頭_title.png（二つ名。朱色）、出力の頭_name.png（名前）。どちらも、上に小さく、ふりがなを付ける
  - フォントは、ドット風の DotGothic16（大きさ16）。二つ名は2倍、名前は3倍、ふりがなは1倍
  - アンチエイリアスなし。まわりに暗い縁取りを付ける
使っているフォント: DotGothic16（SIL Open Font License 1.1）https://github.com/fontworks-fonts/DotGothic16
"""
import sys

from PIL import Image, ImageDraw, ImageFont

INK = (10, 8, 16, 255)
WHITE = (252, 252, 252, 255)
RED = (240, 96, 40, 255)      # 二つ名の色（朱）


def text(font, s, scale, color, spacing=0):
    """文字列を、scale 倍のドットで描く。縁取り（scale ドットぶん）つき"""
    boxes = [font.getbbox(ch) for ch in s]
    top, bottom = min(b[1] for b in boxes), max(b[3] for b in boxes)
    width = sum(b[2] - b[0] for b in boxes) + spacing * (len(s) - 1)
    mask = Image.new("L", (width, bottom - top), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = "1"
    x = 0
    for ch, b in zip(s, boxes):
        d.text((x - b[0], -top), ch, font=font, fill=255)
        x += b[2] - b[0] + spacing
    mask = mask.point(lambda v: 255 if v >= 128 else 0).resize((width * scale, (bottom - top) * scale), Image.NEAREST)
    out = Image.new("RGBA", (mask.width + 2 * scale, mask.height + 2 * scale), (0, 0, 0, 0))
    for dy in range(0, 2 * scale + 1):
        for dx in range(0, 2 * scale + 1):
            out.paste(INK, (dx, dy), mask)
    out.paste(color, (scale, scale), mask)
    return out


def with_reading(font, word, reading, scale, color, spacing):
    """大きい字の上に、小さく、ふりがなを付ける。ふりがなは、字の幅に合わせて、間を広げる"""
    big = text(font, word, scale, color, spacing=spacing)
    gap = (big.width - 6 - 16 * len(reading)) // max(1, len(reading) - 1)
    kana = text(font, reading, 1, WHITE, spacing=max(0, min(gap, 10)))
    w = max(big.width, kana.width)
    out = Image.new("RGBA", (w, kana.height - 2 + big.height), (0, 0, 0, 0))
    out.alpha_composite(big, ((w - big.width) // 2, kana.height - 2))
    out.alpha_composite(kana, ((w - kana.width) // 2, 0))
    return out


def main(font_path, title, title_reading, name, reading, out_head):
    font = ImageFont.truetype(font_path, 16)
    t = with_reading(font, title, title_reading, 2, RED, 1)
    t.save(out_head + "_title.png")
    n = with_reading(font, name, reading, 3, WHITE, 2)
    n.save(out_head + "_name.png")
    print("書き出し:", out_head + "_title.png", t.size, "/", out_head + "_name.png", n.size)


if __name__ == "__main__":
    main(*sys.argv[1:7])
