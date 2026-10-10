"""高精細なドット絵風画像を、ファミコン風の粗いドット絵に変換する。

使い方: python tools/pixelize.py 入力.jpg 出力.png [高さ] [色数]
  - 緑の背景（クロマキー）を透過にする
  - キャラの外接矩形で切り出し、指定の高さに縮小
  - 色数を減らし、黒の輪郭を付ける
"""
import sys

from PIL import Image, ImageFilter

BLACK = (0, 0, 0, 255)

# 色の取り違え（赤が茶色になる等）を防ぐため、自動の減色はせず固定パレットに寄せる
PALETTE = [
    (24, 16, 16),     # 黒に近い暗色
    (200, 40, 32),    # 赤
    (120, 16, 24),    # 暗い赤
    (168, 104, 48),   # 茶
    (84, 44, 24),     # 暗い茶
    (236, 188, 140),  # 肌色
    (252, 252, 252),  # 白
    (150, 150, 160),  # 灰（刀）
]


def remove_green(img):
    img = img.convert("RGBA")
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, _ = px[x, y]
            if g > 140 and g > r + 50 and g > b + 50:
                px[x, y] = (0, 0, 0, 0)
    img = drop_baseline(img)
    # 縁のにじみ（緑が混ざった画素）を削る
    alpha = img.getchannel("A").filter(ImageFilter.MinFilter(3))
    img.putalpha(alpha)
    return img


def drop_baseline(img):
    """足元に引かれた細い地面線を、本体と分かれていれば消す"""
    a = img.getchannel("A")
    w, h = a.size
    counts = [sum(1 for x in range(w) if a.getpixel((x, y))) for y in range(h)]
    y = h - 1
    while y >= 0 and counts[y] == 0:
        y -= 1
    line_bottom = y
    while y >= 0 and counts[y] > 0:
        y -= 1
    # y は本体との隙間の行。線が細い（本体が上にある）ときだけ切る
    if y >= 0 and line_bottom - y < h * 0.05:
        px = img.load()
        for yy in range(y + 1, h):
            for x in range(w):
                px[x, yy] = (0, 0, 0, 0)
    return img


def nearest(c):
    return min(PALETTE, key=lambda p: sum((a - b) ** 2 for a, b in zip(c, p)))


CANVAS = 32


def majority(img):
    """3x3 の多数決で、孤立した色のノイズを減らす（透明画素は触らない）"""
    px = img.load()
    out = img.copy()
    op = out.load()
    for y in range(img.height):
        for x in range(img.width):
            if px[x, y][3] == 0:
                continue
            around = []
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < img.width and 0 <= ny < img.height and px[nx, ny][3]:
                        around.append(px[nx, ny])
            best = max(set(around), key=around.count)
            # 自分が少数派のときだけ置き換える（輪郭や細部を消しすぎない）
            if around.count(px[x, y]) <= 2 and around.count(best) >= 4:
                op[x, y] = best
    return out


def fit_canvas(img):
    """32×32 の枠の下端・左右中央に配置する"""
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(img, ((CANVAS - img.width) // 2, CANVAS - img.height), img)
    return canvas


def pixelize(src, height=None, colors=None):
    """元絵を 32×32 の枠に収まる粗いドット絵にする（輪郭 1px 込み）"""
    img = remove_green(Image.open(src))
    img = img.crop(img.getchannel("A").getbbox())
    inner = CANVAS - 2
    scale = min(inner / img.width, inner / img.height)
    w, height = max(1, round(img.width * scale)), max(1, round(img.height * scale))
    # 縮小は面積平均（BOX）で色を混ぜ、あとで減色する
    small = img.resize((w, height), Image.BOX)
    alpha = small.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
    out = small.convert("RGB")
    op = out.load()
    for y in range(out.height):
        for x in range(out.width):
            op[x, y] = nearest(op[x, y])
    out = out.convert("RGBA")
    out.putalpha(alpha)
    return fit_canvas(add_outline(majority(out)))


def add_outline(img):
    """透明な画素のうち、不透明画素に隣接するものを黒にする"""
    w, h = img.size
    out = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    out.paste(img, (1, 1))
    src = out.copy()
    sp, op = src.load(), out.load()
    for y in range(out.height):
        for x in range(out.width):
            if sp[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < out.width and 0 <= ny < out.height and sp[nx, ny][3]:
                    op[x, y] = BLACK
                    break
    return out


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    height = int(sys.argv[3]) if len(sys.argv) > 3 else 32
    colors = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    pixelize(src, height, colors).save(dst)
