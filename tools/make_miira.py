"""ミイラのシート（白背景）を、ゲーム用のコマにする。

使い方: python tools/make_miira.py シート.jpg 出力フォルダ
  元絵は、明るい布に、暗い巻き目の線が細かく入っている。そのまま縮めると、線と布が混ざって、全体が暗くつぶれる。青い目も、小さくて消える。
  そこで、縮める前に、(1) 布の色を明るくし、(2) 目の青を、まわりへ広げて太らせる。そのあと、make_poses.py で、姿を番号で選んで、コマにする。
出力: 出力フォルダ/miira_walk_0〜3.png、miira_death_0〜2.png、確認用の miira_sheet.png
"""
import os
import subprocess
import sys

from PIL import Image, ImageFilter

LIFT = 1.45         # 布の明るさの倍率（輪郭の暗い色は、変えない）
EYE = (150, 220, 244)
GROW = 9            # 目を太らせる大きさ（元絵のピクセル。縮尺は、7ピクセルが1ドット）


def main():
    src, out = sys.argv[1], sys.argv[2]
    img = Image.open(src).convert("RGB")
    px = img.load()
    eyes = Image.new("L", img.size, 0)
    ep = eyes.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = px[x, y]
            if b > r + 40 and b > 150:              # 目の青
                ep[x, y] = 255
            elif max(r, g, b) < 235 and max(r, g, b) > 90:      # 布（白い背景と、暗い輪郭は、変えない）
                px[x, y] = tuple(min(255, round(c * LIFT)) for c in (r, g, b))
    eyes = eyes.filter(ImageFilter.MaxFilter(GROW))
    img.paste(EYE, mask=eyes)
    os.makedirs(out, exist_ok=True)
    tmp = os.path.join(out, "_miira_bright.png")
    img.save(tmp)
    subprocess.check_call([sys.executable, "-X", "utf8", os.path.join(os.path.dirname(__file__), "make_poses.py"), tmp, out, "miira",
                           "--anim", "walk=0,1,2,3", "--anim", "death=4,5,6+7+8+9+10+11", "--height", "40", "--colors", "14",
                           "--keep-colors", "%d,%d,%d" % EYE])
    os.remove(tmp)


if __name__ == "__main__":
    main()
