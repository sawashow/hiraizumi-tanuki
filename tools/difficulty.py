"""面ごとの難易度を、表にして出す。敵の討伐難易度（config.ENEMY_DIFFICULTY）から、面の敵の密度を測り、目標（config.STAGE_TARGET）と比べる。

使い方: python tools/difficulty.py
  - 敵の密度 = 面にいる敵の難易度の合計 ÷ 面の長さ（1000px あたり）
  - 地形 = 穴・池の数と、いちばん広い幅。足場の数
  - ボス = ボスの種類と、難易度
  - 目標との差が、許す幅（±25%）を超えたら「注意」と出す
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import config as C  # noqa: E402
from stage import STAGES  # noqa: E402


def difficulty_of(kind):
    """配置表の種類名から、敵の討伐難易度を引く。無ければ None"""
    return C.ENEMY_DIFFICULTY.get(kind) or C.ENEMY_DIFFICULTY.get(kind.split("_")[0])


def holes(stage):
    """穴・池の幅の一覧（地面と地面のあいだ）"""
    return [b2 - a1 for (_, a1, _), (b2, _, _) in zip(stage.ground, stage.ground[1:]) if b2 > a1]


def report(stage):
    counts = Counter(k for k, _ in stage.spawns)
    unknown = [k for k in counts if difficulty_of(k) is None]
    total = sum(difficulty_of(k) * n for k, n in counts.items() if difficulty_of(k))
    density = total / (stage.width / 1000)
    hs = holes(stage)
    target = C.STAGE_TARGET.get(stage.number)
    mark = ""
    if target:
        low, high = target[0] * (1 - C.DENSITY_TOLERANCE), target[0] * (1 + C.DENSITY_TOLERANCE)
        mark = "OK" if low <= density <= high else "注意（目標 %g、許す幅 %.1f〜%.1f）" % (target[0], low, high)
    boss = C.BOSS_DIFFICULTY.get(stage.boss_kind)
    boss_mark = ""
    if target and boss is not None and boss != target[1]:
        boss_mark = "（目標 %d。仮のボス）" % target[1]
    print("第%d面 %s（長さ %d）" % (stage.number, stage.name, stage.width))
    print("  敵   %d体 %s" % (sum(counts.values()), dict(counts)))
    print("  密度 %.1f  %s" % (density, mark))
    print("  地形 穴・池 %d個 %s、最大幅 %s、足場 %d" % (len(hs), hs, max(hs) if hs else 0, len(stage.platforms)))
    print("  ボス %s 難易度 %s %s" % (stage.boss_kind, boss, boss_mark))
    if unknown:
        print("  ※ 難易度が決まっていない敵: %s" % unknown)
    print()


if __name__ == "__main__":
    for st in sorted(STAGES, key=lambda x: x.number):
        report(st)
