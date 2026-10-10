"""敵の光波の絵（白背景・横一列の3コマ）を、ゲーム用のドット絵に変換する。
使い方: python tools/make_wave.py シート.jpg 出力フォルダ [--height 32] [--violet]
  - 白い背景を外から塗りつぶして透過にし、1コマずつ切り出す
  - 高さを --height ドットにそろえて縮小し、半透明の画素は、はっきりした色（不透明）にする
  - --violet: 水色を、白〜薄い紫に寄せる（主人公の水色の斬撃と、見分けるため）
出力: 出力フォルダ/wave_0.png ...
"""
import argparse
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from slice_sheet import components, remove_white_bg  # noqa: E402


def main(src, out_dir, height, violet):
    img = remove_white_bg(Image.open(src), erode=False)
    comps = sorted((c for c in components(img) if len(c["pts"]) > 800), key=lambda c: c["box"][0])
    os.makedirs(out_dir, exist_ok=True)
    print("コマ数:", len(comps))
    scale = height / max(c["box"][3] - c["box"][1] for c in comps)
    for i, c in enumerate(comps):
        x0, y0, x1, y1 = c["box"]
        crop = img.crop((x0, y0, x1, y1))
        small = crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))), Image.BOX)
        px = small.load()
        for y in range(small.height):
            for x in range(small.width):
                r, g, b, a = px[x, y]
                if a < 110:
                    px[x, y] = (0, 0, 0, 0)
                    continue
                if violet:
                    r, g, b = (r + b) // 2 + 10, int(g * 0.8) + 25, b
                px[x, y] = (min(r, 255), min(g, 255), min(b, 255), 255)
        small.save(os.path.join(out_dir, f"wave_{i}.png"))
        print(i, small.size)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out_dir")
    ap.add_argument("--height", type=int, default=32)
    ap.add_argument("--violet", action="store_true")
    a = ap.parse_args()
    main(a.src, a.out_dir, a.height, a.violet)
