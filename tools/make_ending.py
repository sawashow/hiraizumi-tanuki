"""エンディングの絵（夜明けの金色堂の前で、タヌキ侍が手を合わせる。「交通安全 終」の文字入り）を、画面に合わせる。

使い方: python tools/make_ending.py 元絵.jpg 出力.png
  480×270 に縮める（色は、そのまま。文字の金色を残すため、色数は絞らない）
元絵は assets/concept/source/ending_koutsu_anzen.jpg（Gemini）
"""
import sys

from PIL import Image

if __name__ == "__main__":
    Image.open(sys.argv[1]).convert("RGB").resize((480, 270), Image.LANCZOS).save(sys.argv[2], optimize=True)
    print("ok")
