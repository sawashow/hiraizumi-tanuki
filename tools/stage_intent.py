"""配置の意図の一覧を作る。面ごと・区画ごとに、足場・動く足場・消える足場・敵の、位置と意図を並べる。
意図は stage.py の各行の最後の文字列（StageDef の *_notes）。「要見直し」で始まるものは、見直す候補として、最後にまとめる。

使い方: python tools/stage_intent.py   → design/配置の意図.md を書き出す（画面にも、面ごとの数を出す）
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config as C  # noqa: E402
from stage import STAGES  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "design", "配置の意図.md")

# 敵の特徴（動き・体力）。意図を読むときの手がかり
ENEMY = {
    "ochimusha": "落ち武者（歩いて近づき、構えて斬る。体力%d）" % C.OCHI["hp"],
    "miira": "ミイラ（ゆっくり歩くだけ。触れると痛い。段差で折り返す。体力%d）" % C.MIIRA["hp"],
    "kitsunebi_low": "狐火・低（揺れながら、主人公のほうへ進む。跳び越える高さ。体力1）",
    "kitsunebi_high": "狐火・高（同じ動きで、高い所を飛ぶ。くぐる高さ。体力1）",
    "karasu": "烏（空中で待ち、羽ばたいて予告し、主人公のいた所へ急降下。体力1）",
    "tengu": "天狗（かがんで予告し、跳びかかる。穴・段差の手前では跳ばない。体力%d）" % C.TENGU["hp"],
    "yumihei": "弓兵（動かない。弓を引いて予告し、矢を撃つ。矢は斬れる。体力%d）" % C.YUMI["hp"],
    "tachiojo": "立ち往生（正面の攻撃を弾く。うしろから斬ると倒せる）",
}
ITEM = {"dango": "団子", "onigiri": "おにぎり", "leaf": "強化（葉）", "triple": "強化（三方）"}
REVIEW = "要見直し"


def rows(stage):
    """面の、意図を持つ物の一覧: (x, 種類, 中身, 意図)"""
    tr = stage.terrain()
    out = []
    for (x0, x1, top), note in zip(stage.platforms, stage.platform_notes):
        g = tr.height_at((x0 + x1) // 2)
        where = "穴の上" if g is None else "地面から %d" % (g - top)
        on = [ITEM.get(k, k) for k, x, y in stage.items if x0 - 6 <= x <= x1 + 6 and 0 < top - y <= 60]
        out.append((x0, "足場 %d〜%d" % (x0, x1), where + ("・上に " + "・".join(on) if on else ""), note))
    for m, note in zip(stage.movers, stage.mover_notes):
        way = "横" if m[1] == m[3] else "上下" if m[0] == m[2] else "斜め"
        out.append((min(m[0], m[2]), "動く足場（%s）" % way, "%d〜%d" % (min(m[0], m[2]), max(m[0], m[2]) + m[4]), note))
    for b, note in zip(stage.blinks, stage.blink_notes):
        out.append((b[0], "消える足場 %d〜%d" % (b[0], b[1]), "", note))
    for (k, x), note in zip(stage.spawns, stage.spawn_notes):
        out.append((x, "敵 x=%d" % x, ENEMY.get(k, k), note))
    return sorted(out)


def stage_md(stage):
    lines = ["## %d面 %s" % (stage.number, stage.name), ""]
    rs = rows(stage)
    zones = list(zip(stage.zones, stage.zone_notes)) or [((0, stage.width, "", "", None), "")]
    for (x0, x1, name, role, aim), note in zones:
        lines += ["### %s（%d〜%d・%s・ねらい %s）" % (name, x0, x1, role, aim), "",
                  "してほしい動き: " + (note or "（未記入）"), ""]
        inside = [r for r in rs if x0 <= r[0] < x1]
        if inside:
            lines += ["| 物 | 中身 | 意図 |", "|---|---|---|"]
            lines += ["| %s | %s | %s |" % (kind, what, note or "（未記入）") for _, kind, what, note in inside]
            lines.append("")
    return lines


def counts(stage):
    notes = stage.platform_notes + stage.mover_notes + stage.blink_notes + stage.spawn_notes + stage.zone_notes
    return sum(1 for n in notes if not n), sum(1 for n in notes if n.startswith(REVIEW)), len(notes)


def main():
    lines = ["# 配置の意図", "",
             "tools/stage_intent.py が stage.py から作る一覧（手で直さない）。意図は、stage.py の各行の最後に書く。", "",
             "| 面 | 未記入 | 要見直し | 全部 |", "|---|---|---|---|"]
    for st in STAGES:
        empty, review, n = counts(st)
        lines.append("| %s | %d | %d | %d |" % (st.name, empty, review, n))
        print("%s: 未記入 %d / 要見直し %d / 全部 %d" % (st.name, empty, review, n))
    lines.append("")
    for st in STAGES:
        lines += stage_md(st)
    lines += ["## 要見直しの一覧", ""]
    for st in STAGES:
        for _, kind, _, note in rows(st):
            if note.startswith(REVIEW):
                lines.append("- %s %s: %s" % (st.name, kind, note[len(REVIEW):].lstrip(": ")))
        for (x0, x1, name, *_), note in zip(st.zones, st.zone_notes):
            if note.startswith(REVIEW):
                lines.append("- %s 区画「%s」: %s" % (st.name, name, note[len(REVIEW):].lstrip(": ")))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("書き出し:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
