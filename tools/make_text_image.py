"""日本語の短い文字列を、ドット風フォントで、透過PNGに書き出す（ゲームにフォントを入れずに、日本語を出すため）。

使い方: python tools/make_text_image.py フォント.ttf "無念…" 出力.png [フォントの大きさ=16] [拡大=3]
  - フォントの大きさは、そのフォントのドットの大きさ（DotGothic16 は 16）に合わせる
  - 文字は白、まわりに暗い縁取りを1ドット付ける
使っているフォント: DotGothic16（SIL Open Font License 1.1）https://github.com/fontworks-fonts/DotGothic16
"""
import sys

from PIL import Image, ImageDraw, ImageFont


def main(font_path, text, out, size=16, scale=3):
    font = ImageFont.truetype(font_path, size)
    # 大きさは、実際に書いた字から測る（getbbox は、アンチエイリアスなしで書いたときより狭いことがあり、最後の字が切れる）
    img = Image.new("L", (size * (len(text) + 2), size * 3), 0)
    d = ImageDraw.Draw(img)
    d.fontmode = "1"   # アンチエイリアスなし（ドットをそのまま出す）
    d.text((size, size), text, font=font, fill=255)
    l, t, r, b = img.getbbox()
    img = img.crop((l - 2, t - 2, r + 2, b + 2))
    mask = img.point(lambda v: 255 if v >= 128 else 0)
    w, h = mask.size
    big = mask.resize((w * scale, h * scale), Image.NEAREST)
    # 縁取り（拡大後の1ドット = scale px 分）
    pad = scale
    outline = Image.new("L", (w * scale + pad * 2, h * scale + pad * 2), 0)
    ob, bp = outline.load(), big.load()
    for y in range(big.height):
        for x in range(big.width):
            if bp[x, y]:
                for dy in range(-pad, pad + 1):
                    for dx in range(-pad, pad + 1):
                        ob[x + pad + dx, y + pad + dy] = 255
    out_img = Image.new("RGBA", outline.size, (0, 0, 0, 0))
    op = out_img.load()
    for y in range(outline.height):
        for x in range(outline.width):
            if ob[x, y]:
                op[x, y] = (10, 8, 16, 255)
    out_img.paste(Image.new("RGBA", big.size, (252, 252, 252, 255)), (pad, pad), big)
    out_img.save(out)
    print("書き出し:", out, out_img.size)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3],
         int(sys.argv[4]) if len(sys.argv) > 4 else 16, int(sys.argv[5]) if len(sys.argv) > 5 else 3)
