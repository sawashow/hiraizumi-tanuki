"""ステージ選択の地図（平泉のワールドマップ）を、ゲーム用に変換する。
使い方: python tools/make_stage_map.py 元絵.jpg フォント.ttf 出力フォルダ
  - stage_map.png: 480×270 に縮め、夜の絵を少し持ち上げる（暗いと、道や広場が沈む）
  - map_label_N.png: 着いた場所に出す「第N面 地名」（ドット風フォント）
元絵は assets/concept/source/stage_map_*.jpg（Gemini）。場所の座標は config.py の MAP_PADS・MAP_ROUTE
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import make_text_image  # noqa: E402

GAMMA = 0.7      # 1より小さいほど、暗い所が持ち上がる（夜の雰囲気は残る）
# 色数は絞らない（絞ると、金色堂の金と、狐火の青が、灰色に沈む）
LABELS = ((1, "第一面　毛越寺"), (2, "第二面　高館"), (3, "第三面　月見坂"), (4, "第四面　金色堂"))


def convert(src, out):
    im = Image.open(src).convert("RGB").resize((480, 270), Image.LANCZOS)
    lut = [round(255 * (i / 255) ** GAMMA) for i in range(256)]
    im = im.point(lut * 3)
    im.save(out, optimize=True)


if __name__ == "__main__":
    src, font, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    convert(src, os.path.join(out, "stage_map.png"))
    for n, text in LABELS:
        make_text_image.main(font, text, os.path.join(out, f"map_label_{n}.png"), 16, 1)
    print("ok")
