"""始まりの語り（眠るタヌキ侍の画面）の背景（夜の平泉）を、ゲーム用（480×270）にする。

使い方: python tools/make_story_bg.py 元絵.jpg 出力.png
  元絵: assets/concept/source/story_bg.jpg（Gemini）。出力: assets/images/story_bg.png
  縮めて平均するとぼやけるので、480×270 の格子に合わせて、ますの真ん中の近くの色を拾い、少数色にまとめる。
  元絵の地面の線は、下から約 24%（高さ 205 ほど）。語りの地面（config.py の STORY_TANUKI の ground）に合わせて、下へずらす
  （上にできた隙間は、いちばん上の行をのばす）。文字が読めるよう、全体を DIM の倍率で暗くする（満月が、文字の邪魔にならないように）
"""
import sys

from PIL import Image

W, H, COLORS = 480, 270, 20
GROUND_SRC, GROUND = 205, 236
DIM = 0.7


def main(src, out):
    img = Image.open(src).convert("RGB")
    px, py = img.width / W, img.height / H
    sp = img.load()
    dots = Image.new("RGB", (W, H))
    shift = GROUND - GROUND_SRC
    for j in range(H):
        sj = max(j - shift, 0)
        for i in range(W):
            cx, cy = (i + 0.5) * px, (sj + 0.5) * py
            pts = [sp[min(int(cx) + dx, img.width - 1), min(int(cy) + dy, img.height - 1)] for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
            dots.putpixel((i, j), tuple(int(sum(p[k] for p in pts) / len(pts) * DIM) for k in range(3)))
    dots.quantize(colors=COLORS, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB").save(out)
    print("書き出し:", out, (W, H))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
