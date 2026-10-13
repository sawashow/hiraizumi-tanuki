"""スタート画面のメニューから開く「操作説明」の絵を作る（ゲームにフォントを入れずに、日本語を出すため）。

使い方: python tools/make_howto.py [フォント.ttf] [出力.png]
  既定のフォントは assets/concept/fonts/PixelMplus12-Bold.ttf（M+ FONT LICENSE）、出力は assets/images/howto.png。
  ドットのフォントを、もとの大きさ（12ドット）で、アンチエイリアスなしで書く。題名だけ、2倍にする。
  中身を変えるときは、下の ROWS・NOTES を直して、作り直す
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(__file__), "..")
W, H = 420, 252
BG, EDGE, GOLD, WHITE, GREY = (16, 14, 34, 236), (214, 168, 72, 255), (255, 236, 150, 255), (244, 244, 244, 255), (176, 180, 196, 255)
COLS = (18, 132, 276)       # 動き / キーボード / コントローラ の、左端
ROWS = (
    ("移動", "← →", "十字キー・スティック"),
    ("ジャンプ", "Space・↑", "A（長く押すと高く）"),
    ("しゃがむ", "↓", "下"),
    ("刀", "Z", "X"),
    ("手裏剣", "X", "B・Y"),
    ("ポーズ", "P", "START"),
)
NOTES = (
    "・手裏剣は、団子の数だけ投げられる",
    "・おにぎりを取ると、体力が回復する",
    "・火のともった灯籠は、壊すと物が出る",
)


def main(font_path, out):
    font = ImageFont.truetype(font_path, 12)
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    d.rectangle((0, 0, W - 1, H - 1), outline=(0, 0, 0, 255))
    d.rectangle((1, 1, W - 2, H - 2), outline=EDGE)
    d.rectangle((3, 3, W - 4, H - 4), outline=EDGE[:3] + (110,))
    # 題名（2倍）
    title = "操作説明"
    mask = Image.new("L", (12 * len(title), 14), 0)
    md = ImageDraw.Draw(mask)
    md.fontmode = "1"
    md.text((0, 0), title, font=font, fill=255)
    mask = mask.point(lambda v: 255 if v >= 128 else 0).resize((mask.width * 2, mask.height * 2), Image.NEAREST)
    img.paste(GOLD, ((W - mask.width) // 2, 10), mask)
    y = 46
    for x, s in zip(COLS[1:], ("キーボード", "コントローラ")):
        d.text((x, y), s, font=font, fill=GOLD)
    d.line((COLS[0], y + 15, W - COLS[0], y + 15), fill=EDGE[:3] + (150,))
    y += 20
    for row in ROWS:
        for x, s, color in zip(COLS, row, (GOLD, WHITE, WHITE)):
            d.text((x, y), s, font=font, fill=color)
        y += 17
    y += 6
    for s in NOTES:
        d.text((COLS[0], y), s, font=font, fill=GREY)
        y += 15
    back = "決定のキーで、もどる"
    d.text(((W - int(font.getlength(back))) // 2, H - 22), back, font=font, fill=GOLD)
    img.save(out)
    print("書き出し:", out, img.size, "文字の下端", y)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets", "concept", "fonts", "PixelMplus12-Bold.ttf"),
         sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "assets", "images", "howto.png"))
