"""吹き出しの中のせりふを、1行の絵に書き出す（ゲームにフォントを入れずに出すため）。

使い方: python tools/make_talk_text.py フォント.ttf "せりふ" 出力.png
  - 暗い字だけを書く（吹き出しの白い枠は、ゲームの側で描く）。アンチエイリアスなし
  - ドットのフォントを、もとの大きさ（12ドット）で書いて、2倍にする（1ドットが、2ドット角になる。昔のゲームの、せりふの字）
  - 1文字を、幅24ドットのますに1つずつ置く（config.py の TALK_CELL と同じ幅）。ゲームでは、左から1ますずつ出す
使っているフォント: PixelMplus12 Bold（M+ FONT LICENSE）。assets/concept/fonts/PixelMplus12-Bold.ttf
  （その前は、M PLUS 1p Black。太くて読みやすいが、ドットの字ではなかった。DotGothic16 は、細くて読みにくかった）
"""
import sys

from PIL import Image, ImageDraw, ImageFont

INK = (24, 16, 32, 255)
SIZE = 12    # フォントの、もとのドットの大きさ
SCALE = 2    # 拡大（ますの幅は SIZE × SCALE = 24）
CELL = SIZE * SCALE


def main(font_path, line, out):
    font = ImageFont.truetype(font_path, SIZE)
    mask = Image.new("L", (SIZE * len(line), SIZE + 2), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = "1"
    for i, ch in enumerate(line):
        d.text((i * SIZE + (SIZE - int(font.getlength(ch))) // 2, 0), ch, font=font, fill=255)
    mask = mask.point(lambda v: 255 if v >= 128 else 0).resize((mask.width * SCALE, mask.height * SCALE), Image.NEAREST)
    img = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    img.paste(INK, (0, 0), mask)
    img.save(out)
    print("書き出し:", out, img.size)


if __name__ == "__main__":
    main(*sys.argv[1:4])
