"""始まりの語り（下から上へ流す文章）を、縦に長い1枚の絵に書き出す（ゲームにフォントを入れずに出すため）。

使い方: python tools/make_story_text.py フォント.ttf assets/story_intro.txt 出力.png [行の間=26]
  - 文章は、テキストファイルに書く（1行が、画面の1行。空の行は、段落の間）
  - 各行を、左右の中央にそろえる。白い字に、暗い縁取り。アンチエイリアスなし
使っているフォント: DotGothic16（SIL Open Font License 1.1）https://github.com/fontworks-fonts/DotGothic16
"""
import sys

from PIL import Image, ImageDraw, ImageFont

INK = (10, 8, 16, 255)
WHITE = (252, 252, 252, 255)


def main(font_path, text_path, out, pitch=26):
    font = ImageFont.truetype(font_path, 16)
    lines = [ln.rstrip("\r\n") for ln in open(text_path, encoding="utf-8")]
    while lines and not lines[-1].strip():
        lines.pop()
    width = max(int(font.getlength(ln)) for ln in lines) + 4
    mask = Image.new("L", (width, pitch * len(lines)), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = "1"
    for i, ln in enumerate(lines):
        d.text(((width - int(font.getlength(ln))) // 2, i * pitch + 2), ln, font=font, fill=255)
    mask = mask.point(lambda v: 255 if v >= 128 else 0)
    img = Image.new("RGBA", (width + 2, mask.height + 2), (0, 0, 0, 0))
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            img.paste(INK, (dx, dy), mask)
    img.paste(WHITE, (1, 1), mask)
    img.save(out)
    print("書き出し:", out, img.size, "%d行" % len(lines))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 26)
