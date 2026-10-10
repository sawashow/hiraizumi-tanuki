"""吹き出しの中のせりふを、1行の絵に書き出す（ゲームにフォントを入れずに出すため）。

使い方: python tools/make_talk_text.py フォント.ttf "せりふ" 出力.png
  - 暗い字だけを書く（吹き出しの白い枠は、ゲームの側で描く）。アンチエイリアスなし
  - 1文字を、幅18ドットのますに1つずつ置く（config.py の TALK_CELL と同じ幅）。ゲームでは、左から1ますずつ出す
使っているフォント: M PLUS 1p Black（SIL Open Font License 1.1）。太くて、小さくても字の形がつぶれない
  （DotGothic16 を重ねて太らせると、「ひ」などが読みにくかった）
"""
import sys

from PIL import Image, ImageDraw, ImageFont

INK = (24, 16, 32, 255)
CELL = 18    # 1文字のますの幅


def main(font_path, line, out):
    font = ImageFont.truetype(font_path, 16)
    mask = Image.new("L", (CELL * len(line), 20), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = "1"
    for i, ch in enumerate(line):
        d.text((i * CELL + (CELL - int(font.getlength(ch))) // 2, 0), ch, font=font, fill=255)
    mask = mask.point(lambda v: 255 if v >= 128 else 0)
    img = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    img.paste(INK, (0, 0), mask)
    img.save(out)
    print("書き出し:", out, img.size)


if __name__ == "__main__":
    main(*sys.argv[1:4])
