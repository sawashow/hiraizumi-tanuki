"""夜のステージマップ（stage_map_gemini_night.jpg）から、
構図・座標を完全に一致させたまま「朝霧・夜明け前」のステージマップを作成する。

- 境界線の段差が出ないよう、滑らかなグラデーションマスクで夜空と山並みを朝露・朝霧トーンへ自然にブレンド
- 手前の平原・毛越寺も、朝の澄んだ光（少し青みがかった朝の緑と爽やかな明るさ）に統一
"""
import os
from PIL import Image, ImageEnhance

SRC = "assets/concept/source/stage_map_gemini_night.jpg"
DST = "assets/images/stage_map_morning.png"

im = Image.open(SRC).convert("RGB")
w, h = im.size

out = Image.new("RGB", (w, h))
px_in = im.load()
px_out = out.load()

for y in range(h):
    # 上から下へ滑らかに変化 (0.0=最上部, 1.0=最下部)
    t = y / h
    for x in range(w):
        r, g, b = px_in[x, y]
        lum = (r * 299 + g * 587 + b * 114) / 1000
        
        # 夜の黒〜濃紺を朝のペールブルー・朝霧（水色〜淡い青白）に持ち上げる係数
        sky_factor = max(0.0, 1.0 - t * 1.3)
        
        # 1. 空・奥の山（上半分）の夜空を夜明け前の白藍・朝霧へ
        # 暗い画素ほど朝の空気光（ペールブルー）を足す
        dark_lift = max(0, 150 - lum) * sky_factor
        nr = r + dark_lift * 0.72
        ng = g + dark_lift * 0.88
        nb = b + dark_lift * 1.05
        
        # 2. 地面全体（森・草地・田畑・道）を朝の瑞々しい光へシフト
        nr = nr * 1.08 + 10
        ng = ng * 1.25 + 16
        nb = nb * 1.15 + 18
        
        px_out[x, y] = (int(min(255, max(0, nr))),
                        int(min(255, max(0, ng))),
                        int(min(255, max(0, nb))))

# 爽やかな朝の空気感にトーン調整
out = ImageEnhance.Contrast(out).enhance(1.04)
out = ImageEnhance.Color(out).enhance(0.96)

res = out.resize((480, 270), Image.LANCZOS)
os.makedirs(os.path.dirname(DST), exist_ok=True)
res.save(DST, optimize=True)
print("Updated morning map:", DST, res.size)
