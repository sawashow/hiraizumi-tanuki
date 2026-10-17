"""スタート画面のメニューから開く「名所」の説明の絵を作る（面ごとに1枚。ゲームにフォントを入れずに、日本語を出すため）。

使い方: python tools/make_meisho.py [フォント.ttf]
  既定のフォントは assets/concept/fonts/PixelMplus12-Bold.ttf（M+ FONT LICENSE）、出力は assets/images/meisho_1.png 〜 meisho_4.png。
  見た目は、操作説明（tools/make_howto.py）にそろえる。中身を変えるときは、下の PLACES を直して、作り直す
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(__file__), "..")
W, H = 420, 252
BG, EDGE, GOLD, WHITE, GREY = (16, 14, 34, 236), (214, 168, 72, 255), (255, 236, 150, 255), (244, 244, 244, 255), (176, 180, 196, 255)
LEFT = 22

# 面の順（毛越寺→高館→月見坂→金色堂）: (名前, 読み, 説明の行, ゲームでは)
PLACES = (
    ("毛越寺", "もうつうじ", (
        "二代 基衡が造りはじめ、三代 秀衡が仕上げた寺。",
        "極楽浄土を地上に写した庭と、大泉が池が今も残る。",
        "池へ水を引く遣水では、今も曲水の宴が開かれる。",
    ), "一の面。四代 泰衡が待つ。"),
    ("高館", "たかだち", (
        "北上川を見下ろす丘。源義経が最期を迎えた地とされる。",
        "芭蕉はここで「夏草や 兵どもが 夢の跡」と詠んだ。",
        "丘の上には、義経をまつる義経堂が建つ。",
    ), "二の面。三代 秀衡が待つ。"),
    ("月見坂", "つきみざか", (
        "中尊寺の表参道。杉の並木が続く、長い上り坂。",
        "杉は江戸時代に伊達藩が植えたもので、樹齢は300年をこえる。",
        "坂の途中から、北上川と束稲山が見わたせる。",
    ), "三の面。二代 基衡が待つ。"),
    ("金色堂", "こんじきどう", (
        "初代 清衡が1124年に建てた、金箔におおわれたお堂。",
        "須弥壇の中に、藤原四代が今も眠る。",
        "2011年、平泉は世界遺産になった。",
    ), "四の面。影の三人と、初代 清衡が待つ。"),
)


def big(font, s, scale):
    """ドットのフォントを、整数倍に大きくした文字の型（にじまない）"""
    mask = Image.new("L", (12 * len(s), 14), 0)
    md = ImageDraw.Draw(mask)
    md.fontmode = "1"
    md.text((0, 0), s, font=font, fill=255)
    mask = mask.crop(mask.getbbox())
    return mask.resize((mask.width * scale, mask.height * scale), Image.NEAREST)


def make(font, place, out):
    name, kana, lines, game = place
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    d.rectangle((0, 0, W - 1, H - 1), outline=(0, 0, 0, 255))
    d.rectangle((1, 1, W - 2, H - 2), outline=EDGE)
    d.rectangle((3, 3, W - 4, H - 4), outline=EDGE[:3] + (110,))
    # 名前（3倍）と、読み
    mask = big(font, name, 3)
    img.paste(GOLD, (LEFT, 18), mask)
    d.text((LEFT + mask.width + 12, 18 + mask.height - 13), kana, font=font, fill=GREY)
    y = 18 + mask.height + 10
    d.line((LEFT, y, W - LEFT, y), fill=EDGE[:3] + (150,))
    y += 14
    for s in lines:
        assert font.getlength("・" + s) <= W - 2 * LEFT, s      # 1行に収まる
        d.text((LEFT, y), "・" + s, font=font, fill=WHITE)
        y += 22
    y += 10
    d.text((LEFT, y), "ゲームでは", font=font, fill=GOLD)
    d.text((LEFT + 72, y), game, font=font, fill=WHITE)
    back = "決定のキーで、もどる"
    d.text(((W - int(font.getlength(back))) // 2, H - 22), back, font=font, fill=GOLD)
    img.save(out)
    print("書き出し:", os.path.normpath(out), img.size, "文字の下端", y + 12)


def main(font_path):
    font = ImageFont.truetype(font_path, 12)
    for i, place in enumerate(PLACES, 1):
        make(font, place, os.path.join(ROOT, "assets", "images", "meisho_%d.png" % i))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets", "concept", "fonts", "PixelMplus12-Bold.ttf"))
