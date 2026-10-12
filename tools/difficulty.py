"""面ごとの難易度と、面の出来（単調さ）を、表にして出す。

使い方: python tools/difficulty.py [面の番号 ...]
  面全体:
  - 敵の密度 = 面にいる敵の難易度の合計 ÷ 面の長さ（1000px あたり）。目標（config.STAGE_TARGET）との差が、許す幅を超えたら「注意」
  - 地形 = 穴・池の数と幅、足場の数 / ボス = 種類と難易度
  区画ごと（stage.py の zones。決めていない面は、config.MAP_CHECK["window"] ごとに区切る。ボスの間は、入れない）:
  - 強さ = 敵の難易度の合計 ＋ 跳ぶ難しさ を、500px あたりに直して、1〜5 の段にしたもの。zones に「ねらい」があれば、比べる
  - 跳ぶ難しさ = 穴を越えるジャンプ1回ごとに 1〜5（必要な距離 ÷ 届く距離。着地が狭ければ ＋1）。穴のふちの敵は、1体につき ＋1。
    敵が少なくても、落ちないように跳んで進む区画は、ここで強さが出る（役目は「渡る」）
  - 敵の種類、穴、段差（地面の高さが変わる回数）、足場、団子、回復（おにぎり・石灯籠の中身）
  単調さの注意（物差しは config.MAP_CHECK）:
  - 強さに、山と谷が無い / 同じ敵が続く / 違う敵と一緒に出る場面が少ない / 平らな道が長い / 何も起きない区間が長い
  - 敵が等間隔に並んでいる / 1体ずつ順番に出てくる / 見せ場（敵がまとまって出る所）が無い
数字で分かるのは「悪い所」まで。面白いかどうかは、遊んで決める。
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import config as C  # noqa: E402
from stage import STAGES  # noqa: E402

M = C.MAP_CHECK
BARS = " ▁▃▅▆█"


def difficulty_of(kind):
    """配置表の種類名から、敵の討伐難易度を引く。無ければ None"""
    return C.ENEMY_DIFFICULTY.get(kind) or C.ENEMY_DIFFICULTY.get(kind.split("_")[0])


def base(kind):
    return kind.split("_")[0]


def holes(stage):
    """穴・池の幅の一覧（地面と地面のあいだ）"""
    return [b2 - a1 for (_, a1, _), (b2, _, _) in zip(stage.ground, stage.ground[1:]) if b2 > a1]


def hole_spans(stage):
    return [(a1, b2) for (_, a1, _), (b2, _, _) in zip(stage.ground, stage.ground[1:]) if b2 > a1]


def _arc():
    """全速で跳んだときの軌道: (横に進んだ距離, 跳んだ所からの高さ, 落ちているか) の並び"""
    x = y = 0.0
    vy, pts = C.JUMP_SPEED, []
    while y < 300:
        vy = min(vy + C.GRAVITY * (C.FALL_GRAVITY if vy > 0 else 1.0), C.MAX_FALL)
        y += vy
        x += C.MAX_SPEED
        pts.append((x, -y, vy >= 0))
    return pts


ARC = _arc()


def reach(rise):
    """rise だけ高い（負なら、低い）所へ跳ぶとき、横に届く距離。高すぎて届かなければ 0"""
    return max((x for x, h, down in ARC if down and h >= rise), default=0.0)


def hop_cost(s1, s2):
    """s1 から、右の s2 へ、穴の上を跳ぶ難しさ（1〜5）と、余裕（px）。届かなければ None"""
    gap, r = max(0, s2[0] - s1[1]), reach(s1[2] - s2[2])
    if not r or gap > r:
        return None
    return 1 + sum(gap / r > t for t in M["jump"]) + (s2[1] - s2[0] < M["narrow"]), r - gap


def hole_jumps(stage):
    """穴ごとの、跳ぶ難しさ: (左端, 右端, 難しさの合計, 跳ぶ回数, いちばん少ない余裕)。
    左の地面 → 穴の上の足場 → 右の地面を、いちばん楽な順でたどる"""
    out = []
    for (g1, g2) in zip(stage.ground, stage.ground[1:]):
        if g2[0] <= g1[1]:
            continue
        nodes = [g1] + sorted(p for p in stage.footholds if g1[1] - 20 <= (p[0] + p[1]) / 2 <= g2[0] + 20) + [g2]
        best = {0: (0, 0, 999.0)}
        for j in range(1, len(nodes)):
            for i in range(j):
                hc = hop_cost(nodes[i], nodes[j]) if i in best else None
                if hc and (j not in best or best[i][0] + hc[0] < best[j][0]):
                    best[j] = (best[i][0] + hc[0], best[i][1] + 1, min(best[i][2], hc[1]))
        cost, hops, margin = best.get(len(nodes) - 1, (9, 1, 0.0))    # 届かない穴（テストが見つける）は、いちばん難しい扱い
        out.append((g1[1], g2[0], cost, hops, margin))
    return out


JUMP_MAX = max(h for _, h, _ in ARC)     # 跳べる高さ（これより高い段は、壁。足場を踏んで登る）


def climb_cost(s1, s2):
    """s1 から、上の s2 へ、跳んで登る難しさ（1〜5）と、余裕（px）。左右どちらへ跳んでもよい。届かなければ None"""
    gap, r = max(0, s2[0] - s1[1], s1[0] - s2[1]), reach(s1[2] - s2[2])
    if not r or gap > r:
        return None
    return 1 + sum(gap / r > t for t in M["jump"]) + (s2[1] - s2[0] < M["narrow"]), r - gap


def climb_jumps(stage):
    """壁（跳べない高さの段）ごとの、登る難しさ: (登り始めの x, 壁の x, 難しさの合計, 跳ぶ回数, いちばん少ない余裕)。
    下の地面 → 壁の手前の足場（低い順）→ 上の地面を、いちばん楽な順でたどる"""
    out = []
    for g1, g2 in zip(stage.ground, stage.ground[1:]):
        if g2[0] != g1[1] or g1[2] - g2[2] <= JUMP_MAX:
            continue
        mid = sorted((p for p in stage.footholds if g1[0] <= (p[0] + p[1]) / 2 < g2[0] and g2[2] < p[2] < g1[2]), key=lambda p: -p[2])
        nodes = [g1] + mid + [g2]
        best = {0: (0, 0, 999.0, g1[1])}
        for j in range(1, len(nodes)):
            for i in range(j):
                cc = climb_cost(nodes[i], nodes[j]) if i in best else None
                if cc and (j not in best or best[i][0] + cc[0] < best[j][0]):
                    best[j] = (best[i][0] + cc[0], best[i][1] + 1, min(best[i][2], cc[1]), min(best[i][3], nodes[j][0]))
        cost, hops, margin, left = best.get(len(nodes) - 1, (9, 1, 0.0, g1[1]))    # 登れない壁（テストが見つける）は、いちばん難しい扱い
        out.append((min(left, g1[1] - 1), g1[1], cost, hops, margin))
    return out


def play_end(stage):
    """道中の右端（最後のボスの間の手前）"""
    return stage.arena_x0


def sections(stage):
    """区画の一覧: (左端, 右端, 名前, 役目, ねらい)。zones が無ければ、同じ幅で区切る"""
    if stage.zones:
        return [tuple(z) for z in stage.zones]
    end, w = play_end(stage), M["window"]
    cuts = list(range(0, end, w)) + [end]
    if len(cuts) > 2 and cuts[-1] - cuts[-2] < w // 2:     # 端の半端は、前の区画に入れる
        del cuts[-2]
    return [(a, b, "", "", None) for a, b in zip(cuts, cuts[1:])]


def level_of(raw):
    return 1 + sum(raw > t for t in M["level"])


def measure(stage, x0, x1):
    """1つの区画の数字"""
    kinds = Counter(base(k) for k, x in stage.spawns if x0 <= x < x1)
    hs = [h for h in hole_jumps(stage) if x0 <= h[0] < x1]
    cs = [c for c in climb_jumps(stage) if x0 <= c[1] < x1]     # 壁を、足場づたいに登る所（穴と同じく、跳ぶ難しさに数える）
    jump = sum(h[2] for h in hs + cs) + sum(1 for k, x in stage.spawns if any(h[0] - M["edge"] <= x <= h[1] + M["edge"] for h in hs + cs))
    foes = sum(difficulty_of(k) * n for k, n in kinds.items())
    steps = sum(1 for (_, a1, t1), (b0, _, t2) in zip(stage.ground, stage.ground[1:]) if a1 == b0 and t1 != t2 and x0 <= b0 < x1)
    gates = [k for x, k in stage.gates if x0 <= x + C.BASE_W // 2 < x1]
    gim = sum(max(0, min(x1, w[1]) - max(x0, w[0])) for w in list(stage.winds) + list(stage.traps)) * M["gimmick"] / 500
    jump += sum(1 for b in stage.blinks if x0 <= b[0] < x1)     # 消える光の足場: 間合いを計るぶん、1つにつき ＋1
    raw = foes + jump + gim + sum(C.BOSS_DIFFICULTY.get(k, 6) * 4 for k in gates)
    raw = raw * 500 / max(1, x1 - x0)
    return dict(kinds=kinds, holes=len(hs), climbs=sum(c[3] for c in cs), steps=steps, jump=jump, foes=foes, gates=gates, raw=raw, level=level_of(raw),
                plats=sum(1 for p in stage.platforms if x0 <= p[0] < x1),
                dango=sum(1 for k, x, _ in stage.items if k == "dango" and x0 <= x < x1),
                heal=sum(1 for k, x, _ in stage.items if k == "onigiri" and x0 <= x < x1)
                + sum(1 for k, x in stage.lanterns if k == "onigiri" and x0 <= x < x1))


def same_run(stage):
    """同じ種類の敵が、いちばん長く続く所: (数, 種類, 左端, 右端)"""
    best, run = (0, "", 0, 0), []
    for k, x in sorted(stage.spawns, key=lambda s: s[1]):
        run = run + [(base(k), x)] if run and run[-1][0] == base(k) else [(base(k), x)]
        if len(run) > best[0]:
            best = (len(run), run[0][0], run[0][1], run[-1][1])
    return best


def combo_rate(stage):
    """違う種類の敵と、一緒に（near 以内に）出る敵の割合"""
    sp = [(base(k), x) for k, x in stage.spawns]
    if not sp:
        return 0.0
    return sum(any(k2 != k and abs(x2 - x) <= M["near"] for k2, x2 in sp) for k, x in sp) / len(sp)


def spacing(stage):
    """敵の間隔のばらつき（標準偏差 ÷ 平均）。0 に近いほど、等間隔に並んでいる（まんべんなく置いただけ）"""
    xs = sorted(x for _, x in stage.spawns)
    gaps = [b - a for a, b in zip(xs, xs[1:])]
    if len(gaps) < 2:
        return 0.0
    mean = sum(gaps) / len(gaps)
    return (sum((g - mean) ** 2 for g in gaps) / len(gaps)) ** 0.5 / mean if mean else 0.0


def group_rate(stage):
    """ほかの敵と、かたまって（group 以内に）出る敵の割合。低いと、1体ずつ順番に出てくるだけ"""
    xs = [x for _, x in stage.spawns]
    return sum(any(a is not b and abs(a - b) <= M["group"] for b in xs) for a in xs) / len(xs) if xs else 0.0


def crowd(stage):
    """1画面（幅 480）に入る敵の数の、いちばん多い所と、区画の強さとは別の「見せ場」の有無を見る: (数, 左端)"""
    xs = sorted(x for _, x in stage.spawns)
    return max(((sum(1 for b in xs if a <= b < a + C.BASE_W), a) for a in xs), default=(0, 0))


def shapes(secs):
    """区画の「型」（敵の種類の組・穴の有無）が、何通りあるか: (通り, 区画の数)"""
    sig = [(tuple(sorted(s["kinds"])), s["holes"] > 0) for s in secs if s["kinds"] or s["holes"]]
    return len(set(sig)), len(sig)


def longest_flat(stage):
    """平らな道が、いちばん長く続く所（道中だけ）: (長さ, 左端, 右端)"""
    end, best, cur = play_end(stage), (0, 0, 0), None
    for x0, x1, top in stage.ground:
        x1 = min(x1, end)
        if x0 >= x1:
            continue
        cur = (cur[0], x1, top) if cur and cur[1] == x0 and cur[2] == top else (x0, x1, top)
        if cur[1] - cur[0] > best[0]:
            best = (cur[1] - cur[0], cur[0], cur[1])
    return best


def longest_empty(stage):
    """敵も、穴も、物も、中ボスも無い区間で、いちばん長い所: (長さ, 左端, 右端)"""
    end = play_end(stage)
    xs = [x for _, x in stage.spawns] + [x for _, x, _ in stage.items] + [x for _, x in stage.lanterns]
    xs += [x for h in hole_spans(stage) for x in h] + [x + C.BASE_W // 2 for x, _ in stage.gates]
    xs = sorted({0, end} | {x for x in xs if 0 < x < end})
    return max(((b - a, a, b) for a, b in zip(xs, xs[1:])), default=(0, 0, 0))


def warnings(stage, secs):
    out = []
    levels = [s["level"] for s in secs]
    if levels and max(levels) - min(levels) <= 1:
        out.append("強さに、山と谷が無い（どの区画も %d〜%d）" % (min(levels), max(levels)))
    n, kind, a, b = same_run(stage)
    if n >= M["same_run"]:
        out.append("同じ敵が続く: %s が %d体（%d〜%d）" % (kind, n, a, b))
    rate = combo_rate(stage)
    if rate < M["combo"]:
        out.append("違う敵と一緒に出る場面が少ない: %d%%（目安 %d%% 以上）" % (rate * 100, M["combo"] * 100))
    cv = spacing(stage)
    if cv < M["spacing"]:
        out.append("敵が、ほぼ等間隔に並んでいる: ばらつき %.2f（目安 %.2f 以上）" % (cv, M["spacing"]))
    gr = group_rate(stage)
    if gr < M["grouped"]:
        out.append("敵が、1体ずつ順番に出てくる: かたまって出る敵 %d%%（目安 %d%% 以上）" % (gr * 100, M["grouped"] * 100))
    n, a = crowd(stage)
    if n < M["crowd"]:
        out.append("見せ場が無い: 1画面の敵は、多い所でも %d体（%d あたり。目安 %d体以上）" % (n, a, M["crowd"]))
    length, a, b = longest_flat(stage)
    if length > M["flat"]:
        out.append("平らな道が長い: %d（%d〜%d）" % (length, a, b))
    length, a, b = longest_empty(stage)
    if length > M["empty"]:
        out.append("何も起きない区間が長い: %d（%d〜%d）" % (length, a, b))
    for (x0, x1, name, role, aim), s in zip(sections(stage), secs):
        if aim and abs(s["level"] - aim) >= 2:
            out.append("区画「%s」の強さが、ねらいと離れている: ねらい %d、実際 %d" % (name, aim, s["level"]))
        if role == "教える" and len(s["kinds"]) > 2:
            out.append("区画「%s」は「教える」なのに、敵が %d種類いる" % (name, len(s["kinds"])))
        if role == "渡る" and s["foes"] > s["jump"]:
            out.append("区画「%s」は「渡る」なのに、跳ぶ難しさ（%d）より、敵（%d）のほうが強い" % (name, s["jump"], s["foes"]))
        if role == "休む" and s["level"] > 2:
            out.append("区画「%s」は「休む」なのに、強さが %d" % (name, s["level"]))
    return out


NAMES = {"blinks": "消える光の足場", "winds": "山おろし（風）", "traps": "光の柱の廊下", "pond": "池の飛び石", "benkei": "中ボス・弁慶", "climb": "崖登り（画面が上へ動く）",
         "boss": "影・泰衡", "boss2": "影・基衡", "boss3": "影・秀衡"}


def elements(stage):
    """その面に出てくる「もの」の一覧（敵の種類・仕掛け・途中のボス）。面ごとの、新しさを見るのに使う"""
    out = [base(k) for k, _ in sorted(stage.spawns, key=lambda s: s[1])]
    out += [NAMES[k] for _, k in stage.gates]
    out += [NAMES[n] for n in ("winds", "traps", "climb", "blinks") if getattr(stage, n)]
    if max(holes(stage), default=0) >= 130:
        out.append(NAMES["pond"])
    return list(dict.fromkeys(out))


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
    secs = [measure(stage, s[0], s[1]) for s in sections(stage)]
    heal = sum(s["heal"] for s in secs) + len(stage.gates)
    dango = sum(1 for k, _, _ in stage.items if k == "dango")
    print("  補給 回復 %d、団子 %d（手裏剣 %d回ぶん。最初の %d を含む）" % (heal, dango, C.AMMO["start"] + dango * C.AMMO["dango"], C.AMMO["start"]))
    n, a = crowd(stage)
    k, m = shapes(secs)
    print("  並び 間隔のばらつき %.2f、かたまって出る敵 %d%%、違う敵と一緒 %d%%、1画面の最大 %d体（%d）、区画の型 %d通り／%d"
          % (spacing(stage), group_rate(stage) * 100, combo_rate(stage) * 100, n, a, k, m))
    print("  強さの流れ  %s  %s" % ("".join(BARS[s["level"]] for s in secs), " ".join(str(s["level"]) for s in secs)))
    hj = hole_jumps(stage)
    hard = max(hj, key=lambda h: h[2], default=None)
    lead = sum(1 for s in secs if s["jump"] and s["jump"] >= s["foes"])
    print("  跳ぶ 難しさの合計 %d、いちばん難しい穴 %s、跳ぶのが主役の区画 %d／%d"
          % (sum(h[2] for h in hj), "%d〜%d（難しさ %d、%d回跳ぶ、余裕 %dpx）" % hard if hard else "なし", lead, len(secs)))
    print("  %-11s %-14s %-4s %2s %2s  %-26s %s" % ("区画", "名前・役目", "ねらい", "強さ", "", "敵", "跳ぶ 穴 段差 足場 団子 回復"))
    for (x0, x1, name, role, aim), s in zip(sections(stage), secs):
        kinds = " ".join("%s%d" % (k, n) for k, n in s["kinds"].most_common()) + "".join(" ★" + g for g in s["gates"])
        label = (name + ("・" + role if role else "")) or "-"
        print("  %5d-%-5d %-14s %-4s %2d %-2s  %-26s %3d %2d %3d %3d %3d %3d" % (
            x0, x1, label, aim or "-", s["level"], BARS[s["level"]], kinds or "（なし）", s["jump"], s["holes"], s["steps"], s["plats"], s["dango"], s["heal"]))
    ws = warnings(stage, secs)
    for w in ws:
        print("  注意: " + w)
    if not ws:
        print("  注意: なし")
    print()
    return ws


if __name__ == "__main__":
    want = {int(a) for a in sys.argv[1:]}
    seen = []
    for st in sorted(STAGES, key=lambda x: x.number):
        new = [e for e in elements(st) if e not in seen]
        seen += new
        if not want or st.number in want:
            report(st)
            # 冗長さ: その面で、初めて出るもの。少ない面は、前の面の繰り返しに感じる（長い面ほど、新しいものが要る）
            print("  新しさ この面で初めて出るもの %d: %s（面の長さ 1000px あたり %.1f）%s\n"
                  % (len(new), "・".join(new) or "なし", len(new) / (st.width / 1000), "" if len(new) >= 2 else "  ← 注意: 少ない"))
