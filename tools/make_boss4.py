"""4面ボス（清衡）のシート（白背景・3行: 浮いて座る / 数珠を飛ばす / 光になって消える）を、ゲーム用のコマにする。

使い方: python tools/make_boss4.py シート.jpg 出力フォルダ
  tools/make_enemy.py で、コマに切り出して（横の基準は絵の中心、縦も中心）、共通の少数色に寄せる。
  そのあと、光輪の内側に残った白（背景の白が、輪に囲まれて残ったもの）を、透明にする。
  出力: boss4_idle_0〜2.png / boss4_cast_0〜2.png / boss4_death_0〜2.png と、確認用の boss4_sheet.png
"""
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(__file__)
WHITE = 242      # 全チャンネルがこれ以上の画素は、背景の白（光輪の内側に残ったもの）


def main(src, out):
    subprocess.run([sys.executable, os.path.join(HERE, "make_enemy.py"), src, out, "boss4",
                    "--names", "idle,cast,death", "--rows", "0,1,2", "--gaps", "40,40,40",
                    "--anchors", "bbox,bbox,bbox", "--target-h", "60", "--valign", "center", "--colors", "24"], check=True)
    n = 0
    for anim in ("idle", "cast", "death"):
        for i in range(3):
            path = os.path.join(out, "boss4_%s_%d.png" % (anim, i))
            im = Image.open(path).convert("RGBA")
            px = im.load()
            for y in range(im.height):
                for x in range(im.width):
                    r, g, b, a = px[x, y]
                    if a and min(r, g, b) >= WHITE:
                        px[x, y] = (0, 0, 0, 0)
                        n += 1
            im.save(path)
    print("光輪の内側の白を消した画素:", n)


if __name__ == "__main__":
    main(*sys.argv[1:3])
