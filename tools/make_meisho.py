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
        "両側の杉の多くは、樹齢300年をこえる。",
        "坂を上った先に、本堂と金色堂がある。",
    ), "三の面。二代 基衡が待つ。"),
    ("金色堂", "こんじきどう", (
        "初代 清衡が1124年に建てた、金箔におおわれたお堂。",
        "須弥壇の中に、藤原四代が今も眠る。",
        "2011年、平泉は世界遺産になった。",
    ), "四の面。影の三人と、初代 清衡が待つ。"),
)


# 人物（遊ぶ順。泰衡→秀衡→基衡→清衡）: (名前, 読み, 説明の行, ゲームでは)。出力は jinbutsu_1.png 〜 jinbutsu_4.png
PEOPLE = (
    ("藤原泰衡", "ふじわらのやすひら", (
        "四代。1155-1189。秀衡の子。",
        "頼朝に迫られ、父がかくまった義経を高館に攻めた。",
        "それでも頼朝の大軍に攻められ、平泉を焼いて北へ逃げた。",
        "逃げる途中、家臣に討たれ、首は頼朝のもとへ送られた。",
        "その首は、のちに金色堂に納められた。",
    ), "一の面のボス。首を失った「首無武者」。"),
    ("藤原秀衡", "ふじわらのひでひら", (
        "三代。1122-1187。基衡の子。",
        "鎮守府将軍となり、奥州藤原氏の最盛期を築いた。",
        "毛越寺を仕上げ、宇治の平等院をまねた無量光院を建てた。",
        "頼朝に追われた源義経を、平泉にかくまった。",
        "死の間際、義経を立てて国を守れと言い残した。",
    ), "二の面のボス。薙刀の光波と、踏み込み突き。"),
    ("藤原基衡", "ふじわらのもとひら", (
        "二代。生年不明-1157。清衡の子。",
        "父の死後、兄弟と争って、跡を継いだ。",
        "京から仏師や職人を招き、毛越寺を造りはじめた。",
        "極楽浄土を写した庭は、今も毛越寺に残る。",
        "妻は、毛越寺のとなりに観自在王院を建てた。",
    ), "三の面のボス。扇で風を起こす。"),
    ("藤原清衡", "ふじわらのきよひら", (
        "初代。1056-1128。",
        "前九年・後三年の戦で、父も妻子も失った。",
        "戦の世を終わらせ、平泉に中尊寺を建てた。",
        "敵も味方も、戦で死んだすべての命を弔うと願った。",
        "1124年に金色堂を建て、今もそこに眠る。",
    ), "最後のボス。金色の光をまとい、浮かぶ。"),
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
    step = 22 if len(lines) <= 3 else 19      # 行が多い（人物）ときは、少し詰める
    for s in lines:
        assert font.getlength("・" + s) <= W - 2 * LEFT, s      # 1行に収まる
        d.text((LEFT, y), "・" + s, font=font, fill=WHITE)
        y += step
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
    for i, person in enumerate(PEOPLE, 1):
        make(font, person, os.path.join(ROOT, "assets", "images", "jinbutsu_%d.png" % i))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets", "concept", "fonts", "PixelMplus12-Bold.ttf"))
