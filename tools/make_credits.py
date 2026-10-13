"""エンドロールの文字を、縦に長い1枚の絵にする（ゲームにフォントを入れずに、日本語を出すため）。

使い方: python tools/make_credits.py [フォント.ttf] [出力.png]
  既定のフォントは assets/concept/fonts/PixelMplus12-Bold.ttf（M+ FONT LICENSE）、出力は assets/images/credits.png。
  ドットのフォントを、もとの大きさ（12ドット）で、アンチエイリアスなしで書く。どの行も、中央ぞろえ。黒い縁取りを付ける（明るい空の上でも読めるように）。
  中身を変えるときは、下の LINES を直して、作り直す。("見出し", 文) は金色の小見出し、("題", 文) は2倍の大きさ、("", 文) はふつうの行、None は、すき間
  ("絵", "") は、ボスの絵（動く）を、ゲームが重ねて描くための、空き場所（高さ SLOT_H。config.py の ROLL の slot_h と同じにする）。
  空き場所の上端の、左端の画素に、目印（色 255,0,255・不透明度 3。見えない）を打つ。ゲームは、これを探して、絵を重ねる（出てくる順が、config.py の ROLL_BOSSES の順）
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(__file__), "..")
W = 232      # 画面の右半分（幅 240）に収める
GOLD, WHITE, EDGE = (255, 226, 120, 255), (250, 250, 250, 255), (16, 10, 24, 255)
LINES = (
    ("題", "平泉タヌキ侍"),
    None, None,
    ("見出し", "ぶたい"),
    ("", "岩手県 平泉"),
    ("", "毛越寺・高館・月見坂・金色堂"),
    None,
    ("見出し", "しゅつえん"),
    None,
    ("絵", ""),
    ("見出し", "四代  藤原泰衡"),
    ("", "1155 - 1189"),
    ("", "頼朝に攻められ、"),
    ("", "家臣に裏切られて滅んだ"),
    None,
    ("絵", ""),
    ("見出し", "三代  藤原秀衡"),
    ("", "1122 - 1187"),
    ("", "奥州の最盛期を築き、"),
    ("", "義経をかくまった"),
    None,
    ("絵", ""),
    ("見出し", "二代  藤原基衡"),
    ("", "生年不明 - 1157"),
    ("", "毛越寺を造り、"),
    ("", "浄土の庭を残した"),
    None,
    ("絵", ""),
    ("見出し", "初代  藤原清衡"),
    ("", "1056 - 1128"),
    ("", "戦のない世を願い、"),
    ("", "中尊寺と金色堂を建てた"),
    None,
    ("見出し", "え"),
    ("", "Gemini"),
    ("", "ChatGPT"),
    None,
    ("見出し", "おんがく"),
    ("", "Gemini"),
    ("", "Evening at the Border Post"),
    ("", "Clash of the Iron Fan"),
    ("", "Crimson Temple Breach"),
    ("", "Seven Blades High"),
    ("", "Steps Into the Morning Sun"),
    None,
    ("見出し", "プログラム"),
    ("", "Claude"),
    ("", "Python・pygame"),
    None,
    ("見出し", "もじ"),
    ("", "PixelMplus"),
    ("", "DotGothic16"),
    None, None,
    ("見出し", "こうつうあんぜん"),
    ("", "道をわたるときは"),
    ("", "止まって、右を見て、左を見て"),
    ("", "もういちど、右を見る"),
    None, None, None,
    ("題", "おしまい"),
    None,
    ("", "あそんでくれて、ありがとう"),
)
ROW, GAP = 17, 12
SLOT_H = 118        # ボスの絵の空き場所の高さ（いちばん高い絵 115 + 余白）
MARK = (255, 0, 255, 3)


def line_image(font, s, color, scale):
    mask = Image.new("L", (int(font.getlength(s)) + 2, 15), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = "1"
    d.text((0, 0), s, font=font, fill=255)
    mask = mask.point(lambda v: 255 if v >= 128 else 0)
    if scale > 1:
        mask = mask.resize((mask.width * scale, mask.height * scale), Image.NEAREST)
    out = Image.new("RGBA", (mask.width + 2, mask.height + 2), (0, 0, 0, 0))
    for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2), (0, 0), (2, 2), (0, 2), (2, 0)):     # 黒い縁取り
        out.paste(EDGE, (dx, dy), mask)
    out.paste(color, (1, 1), mask)
    return out


def main(font_path, out):
    font = ImageFont.truetype(font_path, 12)
    rows, y, slots = [], 0, []
    for item in LINES:
        if item is None:
            y += GAP
            continue
        kind, s = item
        if kind == "絵":
            slots.append(y)
            y += SLOT_H + 4
            continue
        img = line_image(font, s, GOLD if kind else WHITE, 2 if kind == "題" else 1)
        rows.append((img, y))
        y += img.height + (ROW - 14)
    sheet = Image.new("RGBA", (W, y), (0, 0, 0, 0))
    for img, yy in rows:
        sheet.alpha_composite(img, ((W - img.width) // 2, yy))
    for sy in slots:
        sheet.putpixel((0, sy), MARK)       # 空き場所の目印（ゲームが探す）
    sheet.save(out)
    print("書き出し:", out, sheet.size)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets", "concept", "fonts", "PixelMplus12-Bold.ttf"),
         sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "assets", "images", "credits.png"))
