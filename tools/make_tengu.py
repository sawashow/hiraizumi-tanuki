"""天狗のシート（白背景）を、ゲーム用のコマにする。

使い方: python tools/make_tengu.py シート.jpg 出力フォルダ
  元絵の装束は、暗い藍色（56,48,80 ほど）で、そのまま縮めると、黒や灰色につぶれる。
  縮める前に、(1) 藍色の装束を、明るく・青く持ち上げ、(2) 胸の白い房を、まわりへ広げて太らせる。そのあと、make_poses.py で、姿を番号で選んで、コマにする。
  姿の番号: 0 待つ / 1 空中 / 2 かがむ / 3 着地 / 4 のけぞる / 5 崩れる。消える羽根（最後のコマ）は、黒くて細いので、範囲を指定して、そのまま切り出す。
出力: 出力フォルダ/tengu_walk_0〜3.png、tengu_death_0〜2.png、確認用の tengu_sheet.png
"""
import os
import subprocess
import sys

from PIL import Image, ImageFilter

NAVY_LIFT = (1.5, 1.5, 1.9)      # 藍色の装束の、色ごとの倍率（青を強く）
POM = (250, 250, 250)            # 胸の白い房
GROW = 7                         # 房を太らせる大きさ（元絵のピクセル。縮尺は、6ピクセルが1ドット）
FEATHERS = "985,455,1235,705"    # 消える羽根の範囲（元絵）


def main():
    src, out = sys.argv[1], sys.argv[2]
    img = Image.open(src).convert("RGB")
    px = img.load()
    pom = Image.new("L", img.size, 0)
    pp = pom.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = px[x, y]
            if min(r, g, b) > 235:                       # 白（背景も含む。背景は、あとで消える）
                continue
            if b >= r - 4 and b >= g and 24 < max(r, g, b) < 130 and r < 110:    # 藍色の装束・黒い羽根の青み
                px[x, y] = tuple(min(255, round(c * k)) for c, k in zip((r, g, b), NAVY_LIFT))
    pom = pom.filter(ImageFilter.MaxFilter(GROW))
    img.paste(POM, mask=pom)
    os.makedirs(out, exist_ok=True)
    tmp = os.path.join(out, "_tengu_bright.png")
    img.save(tmp)
    subprocess.check_call([sys.executable, "-X", "utf8", os.path.join(os.path.dirname(__file__), "make_poses.py"), tmp, out, "tengu",
                           "--anim", "walk=0,1,2,3", "--anim", "death=4,5", "--height", "40", "--ref", "walk", "--colors", "16",
                           "--keep-colors", "250,250,250;230,200,40", "--raw", "tengu_death_2=" + FEATHERS])
    os.remove(tmp)


if __name__ == "__main__":
    main()
