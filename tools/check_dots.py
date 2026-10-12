"""ゲームに入っている絵（assets/images）の、ドットの粗さと色数を測って、基準から外れているものを表にする。

使い方: python tools/check_dots.py [絵のファイル ...]
  - ファイルを書かなければ、assets/images の全部を測る（コマが連番の絵は、1枚目だけ）
  - 絵を作り直したら、置く前に、そのファイルを指定して測る

測るもの:
  - 2角: 絵を 2×2 ドットの升目に区切ったとき、1色になっていない升目の割合。0% に近ければ、2ドット角の粗さ
  - 細線: 横に見て、同じ色が1ドットしか続かない所の割合。高いほど、描き込みが細かい（主人公は、約50%）
  - 色: 使っている色の数（透明は除く）

判定（基準は assets/ドット絵基準.md）:
  - キャラ・小物: 細線 70% 以下、16色以下なら「○」。主人公（細線 約50%・9色）が見本。短い辺が 24 未満の小さい絵は、色数だけを見る
  - 背景・タイル・足場: 2角 15% 以下（2ドット角以上の粗さ）、32色以下なら「○」
  - 文字の絵（3色以下）と、光（光波）は、測るだけ（判定しない）
"""
import glob
import os
import re
import sys

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "images")
SHEETS = ("player_sheet.png", "shuriken_sheet.png", "boss4_sheet.png")    # 確認用のシート（ゲームは読まない）
STILLS = ("title.png", "ending.png", "stage_map.png")                     # 画面いっぱいの一枚絵
GLOW = ("wave", "slash")                                                   # 光（輪郭なし。ぼかしてよい）
CHAR_LINE, CHAR_COLORS = 0.70, 16
BG_BLOCK, BG_COLORS = 0.15, 32


def measure(path):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    if w > 900:                 # 横に長い背景は、左の 900 だけ測る（時間がかかるので）
        im, w = im.crop((0, 0, 900, h)), 900
    px = im.load()

    def at(x, y):
        p = px[x, y]
        return p if p[3] else None

    block = 1.0
    for ox in (0, 1):           # 升目の始まりを、ずらして試す（いちばん合う位置で測る）
        for oy in (0, 1):
            bad = total = 0
            for y in range(oy, h - 1, 2):
                for x in range(ox, w - 1, 2):
                    vals = {at(x, y), at(x + 1, y), at(x, y + 1), at(x + 1, y + 1)}
                    if vals == {None}:
                        continue
                    total += 1
                    bad += len(vals) > 1
            if total:
                block = min(block, bad / total)
    runs = single = 0
    for y in range(h):
        x = 0
        while x < w:
            c, n = at(x, y), 1
            while x + n < w and at(x + n, y) == c:
                n += 1
            if c is not None:
                runs += 1
                single += n == 1
            x += n
    colors = len({px[x, y] for y in range(h) for x in range(w) if px[x, y][3]})
    return (im.size if w < 900 else Image.open(path).size), block, single / max(1, runs), colors


def kind_of(rel):
    name = os.path.basename(rel)
    if name in STILLS:
        return "一枚絵"
    if re.match(r"(bg_|tile_|stone_|water_)", name):
        return "背景"
    if any(name.startswith(g) for g in GLOW):
        return "光"
    return "キャラ・小物"


def judge(kind, size, block, line, colors):
    if colors <= 3:
        return "文字"
    if kind == "光":
        return "−"
    if kind == "背景":
        why = [("粗さが細かい" if block > BG_BLOCK else ""), ("色が多い" if colors > BG_COLORS else "")]
    elif kind == "一枚絵":
        why = ["色が多い（ドット絵になっていない）" if colors > 64 else ""]
    else:
        fine = line > CHAR_LINE and min(size) >= 24      # 小さい絵は、どう描いても細線が多くなるので、色数だけを見る
        why = [("描き込みが細かい" if fine else ""), ("色が多い" if colors > CHAR_COLORS else "")]
    why = [t for t in why if t]
    return "× " + "・".join(why) if why else "○"


def main(args):
    if args:
        files = [(os.path.basename(f), f) for f in args]
    else:
        seen, files = set(), []
        for f in sorted(glob.glob(os.path.join(ROOT, "**", "*.png"), recursive=True)):
            rel = os.path.relpath(f, ROOT).replace(os.sep, "/")
            if os.path.basename(rel) in SHEETS:
                continue
            group = re.sub(r"_?\d+\.png$", "", rel)
            if group not in seen:
                seen.add(group)
                files.append((group, f))
    print("%-30s %-11s %-10s %5s %5s %5s  %s" % ("絵", "大きさ", "種類", "2角", "細線", "色", "判定"))
    bad = 0
    for label, f in files:
        size, block, line, colors = measure(f)
        kind = kind_of(f)
        verdict = judge(kind, size, block, line, colors)
        bad += verdict.startswith("×")
        print("%-30s %-11s %-10s %4.0f%% %4.0f%% %5d  %s" % (label[:30], "%dx%d" % size, kind, block * 100, line * 100, colors, verdict))
    print("基準から外れている絵: %d / %d" % (bad, len(files)))


if __name__ == "__main__":
    main(sys.argv[1:])
