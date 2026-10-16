"""ヘッドレスで操作を再生して、動きの結果を確認し、場面ごとのスクリーンショットを保存する。

使い方: python tools/smoke_test.py
出力: assets/concept/smoke_sheet.png（場面の一覧）
"""
import math
import re
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame  # noqa: E402

import config as C  # noqa: E402
from main import ENEMY_SPAWNS, Game, drop_kind  # noqa: E402
from sprites import Item, Karasu, Kitsunebi, Ochimusha, Shuriken, Wave  # noqa: E402
import copy  # noqa: E402

from stage import GROUND, ITEMS, PLATFORMS, S4, STAGE1_LEGACY, STAGE2, STAGES, Terrain  # noqa: E402

# 本番の面の順は、毛越寺 → 月見坂（ボスは遊ぶ順で決まる）。ただし、以下の動きのテスト（地形・敵・ボス）は、
# 「月見坂＝1面（泰衡）、毛越寺＝2面（基衡）」で書かれているので、写しを作って、その形にそろえて動かす。
# 本番の順そのものは、最後の「面の順」の節で確かめる
PROD_STAGES = list(STAGES)
_L1 = copy.copy(STAGE1_LEGACY)
_L1.number, _L1.boss_kind = 1, "boss"
_L1.boss_title, _L1.boss_name, _L1.boss_pattern = C.BOSS_TITLE, C.BOSS_NAME, C.BOSS_PATTERN
_L1.talk_boss, _L1.talk_tanuki = C.TALK_BOSS, C.TALK_TANUKI
_L2 = copy.copy(STAGE2)
_L2.number, _L2.boss_kind, _L2.boss_pattern = 2, "boss2", C.BOSS2_PATTERN
_L2.boss_title, _L2.boss_name = "enemies/boss2_title.png", "enemies/boss2_name.png"
_L2.talk_boss, _L2.talk_tanuki = "talk_boss2.png", "talk_tanuki2.png"
STAGES[:] = [_L1, _L2]

# 古い（平らな）地形。穴と足場の動きのテスト用
_T = C.FLOOR_Y
OLD_GROUND = ((0, 700, _T), (780, 1250, _T), (1380, 1700, _T), (1830, C.STAGE_W, _T))
OLD_PLATFORMS = ((980, 1044, _T - 62), (1290, 1340, _T - 50), (1740, 1790, _T - 56))

DROPS = C.DROPS
C.DROPS = ()   # ふだんは、敵が物を落とさないようにしておく（結果が毎回同じになるように）。落とし物のテストで戻す

pygame.init()
pygame.display.set_mode((C.BASE_W, C.BASE_H))
font = pygame.font.Font(None, 20)
screen = pygame.Surface((C.BASE_W, C.BASE_H))
shots = []
fails = []


def snap(g, label):
    g.draw(screen, font)
    shots.append((label, screen.copy()))


def check(name, cond, detail=""):
    print(("OK  " if cond else "NG  ") + name + (" " + detail if detail else ""))
    if not cond:
        fails.append(name)


def run(g, n, held=(), pressed_first=()):
    for i in range(n):
        g.step(set(held), set(pressed_first) if i == 0 else set())


def fresh(enemies=(), px=300.0):
    """敵を指定したものだけにした、新しいゲーム"""
    g = Game(Terrain(OLD_GROUND, OLD_PLATFORMS))
    g.lives = 1   # 1回やられたら、ゲームオーバーになる設定（残機のテストは別）
    g.enemies = list(enemies)
    for e in g.enemies:
        e.a = g.a   # テストで作った敵にも、絵を持たせる
    g.player.px = float(px)
    return g


# ---------------------------------------------------------------- 1. 移動・ジャンプ
g = fresh(px=60)
snap(g, "start")
x0 = g.player.px
run(g, 40, {"right"})
check("右に歩ける", g.player.px > x0 + 50, "x=%.0f" % g.player.px)
snap(g, "walk")
run(g, 1, (), {"jump"})
peak = 99999
for _ in range(60):
    run(g, 1)
    peak = min(peak, g.player.py)
check("ジャンプで上がる", C.FLOOR_Y - peak > 50, "高さ=%.0f" % (C.FLOOR_Y - peak))
check("ジャンプ後に着地する", g.player.on_ground)

# ---------------------------------------------------------------- 2. 敵3種類の違い
oc, ki, ka = Ochimusha(0), Kitsunebi(0, "low"), Karasu(0)
sizes = {(e.w, e.h) for e in (oc, ki, ka)}
check("3種類の当たり判定の大きさが、すべて違う", len(sizes) == 3, str(sorted(sizes)))
check("体力: 落ち武者2・狐火1・烏1（飛ぶ敵は、もろい）", (oc.max_hp, ki.max_hp, ka.max_hp) == (2, 1, 1))
check("刀は手裏剣より強い", C.SWORD_DAMAGE > C.SHURIKEN_DAMAGE, "刀%d / 手裏剣%d" % (C.SWORD_DAMAGE, C.SHURIKEN_DAMAGE))
check("刀の回数: 落ち武者1回・狐火1回・烏1回",
      tuple(-(-e.max_hp // C.SWORD_DAMAGE) for e in (oc, ki, ka)) == (1, 1, 1))
check("手裏剣の発数: 落ち武者2発・狐火1発・烏1発",
      tuple(-(-e.max_hp // C.SHURIKEN_DAMAGE) for e in (oc, ki, ka)) == (2, 1, 1))
check("落ち武者が一番大きい", oc.w * oc.h > max(ki.w * ki.h, ka.w * ka.h))
check("烏は横長・狐火は小さい", ka.w > ka.h * 1.5 and ki.w * ki.h < ka.w * ka.h)
kinds = [k for k, _ in ENEMY_SPAWNS]
check("1面の配置が、落ち武者11・狐火6・烏7（敵が多い面）", (kinds.count("ochimusha"), sum(k.startswith("kitsunebi") for k in kinds),
                                      kinds.count("karasu")) == (11, 6, 7))
check("2面は、1面より敵が少ない（飛ぶ敵が中心）", len(STAGES[1].spawns) < len(STAGES[0].spawns) * 0.7
      and sum(k != "ochimusha" for k, _ in STAGES[1].spawns) > sum(k == "ochimusha" for k, _ in STAGES[1].spawns))
check("序盤は落ち武者だけ（x<1000）", all(k == "ochimusha" for k, x in ENEMY_SPAWNS if x < 1000))
check("烏は後半（x>=1800）にだけ出る", all(x >= 1800 for k, x in ENEMY_SPAWNS if k == "karasu"))

# ---------------------------------------------------------------- 3. 落ち武者
g = fresh([Ochimusha(640)], px=400)
e = g.enemies[0]
d0 = abs(e.cx - g.player.rect.centerx)
run(g, 60)
check("落ち武者は、近づくと主人公に向かって歩く", abs(e.cx - g.player.rect.centerx) < d0 - 20,
      "距離 %.0f→%.0f" % (d0, abs(e.cx - g.player.rect.centerx)))
check("落ち武者の歩きは遅い（1フレーム0.6）", abs((d0 - abs(e.cx - g.player.rect.centerx)) / 60 - C.OCHI["speed"]) < 0.05)
g = fresh([Ochimusha(900)], px=100)
x_before = g.enemies[0].cx
run(g, 60)
check("遠い落ち武者は、その場の近くをうろうろするだけ", abs(g.enemies[0].cx - x_before) < C.OCHI["patrol"] + 5)
# 近づくと、一度止まって構える
g = fresh([Ochimusha(400 + 8 + 70)], px=400)
e = g.enemies[0]
run(g, 100)
stopped = 0
for _ in range(200):
    run(g, 1)
    if e.ready_t > 0:
        break
prev = e.cx
for _ in range(60):
    run(g, 1)
    if abs(e.cx - prev) < 1e-9:
        stopped += 1
    prev = e.cx
check("落ち武者は、近づくと止まって構え、刀を振る（約1秒動かない）", stopped >= 50, "停止 %d フレーム" % stopped)

# 光波: 構えのあと、刀を振ると前方に飛ぶ
def wave_game(px=400):
    gg = fresh([Ochimusha(px + 100)], px=px)
    for _ in range(300):
        run(gg, 1)
        if gg.waves:
            break
    return gg


g = wave_game()
check("落ち武者が刀を振ると、光波が出る", len(g.waves) == 1)
w = g.waves[0]
check("光波は、主人公のいる側（左）へ飛ぶ", w.dir == -1)
x_w = w.px
run(g, 10)
check("光波は、まっすぐ進む（1フレーム %.1f）" % C.WAVE["speed"], abs((x_w - w.px) / 10 - C.WAVE["speed"]) < 0.05)
check("光波の高さは、足元すれすれ（ジャンプでよけられる高さ）", w.rect.bottom <= C.FLOOR_Y and w.rect.top > C.FLOOR_Y - 30)
snap(g, "wave")
hp0 = g.player.hp
for _ in range(120):
    run(g, 1)
    if not w.alive:
        break
check("立っていると、光波に当たってダメージ1", g.player.hp == hp0 - C.WAVE["damage"] and not w.alive, "HP %d → %d" % (hp0, g.player.hp))

g = wave_game()
hp0 = g.player.hp
w = g.waves[0]
for _ in range(120):
    if w.px - g.player.rect.centerx < 24 and g.player.on_ground and w.px > g.player.rect.centerx:
        run(g, 1, (), {"jump"})
    else:
        run(g, 1)
    if w.px < g.player.rect.centerx - 30:
        break
check("ジャンプでよけられる（ダメージなし）", g.player.hp == hp0, "HP %d → %d" % (hp0, g.player.hp))

g = wave_game()
hp0 = g.player.hp
w = g.waves[0]
g.player.facing = 1
for _ in range(120):
    if w.alive and w.px - g.player.rect.centerx < 34 and not g.player.attack_t:
        run(g, 1, (), {"attack"})
    else:
        run(g, 1)
    if not w.alive:
        break
check("刀で斬ると光波が消える（ダメージなし）", not w.alive and g.player.hp == hp0, "HP %d → %d" % (hp0, g.player.hp))

g = fresh(px=100)
g.waves = [Wave(300, C.FLOOR_Y - 18, -1, g.a)]
g.shurikens = [Shuriken(310, C.FLOOR_Y - 18, -1, g.a)]
run(g, 3)
check("手裏剣は、光波を消せない（通り抜ける）", g.waves and g.waves[0].alive)
g = fresh(px=100)
g.waves = [Wave(110, C.FLOOR_Y - 18, -1, g.a)]
g.player.invincible = 30
run(g, 5)
check("無敵のあいだは、光波に当たらない", g.player.hp == C.PLAYER_HP)
g = fresh(px=100)
g.waves = [Wave(110, C.FLOOR_Y - 18, -1, g.a)]
g.waves[0].travel = C.WAVE["range"] - 0.1
run(g, 2)
check("光波は、一定の距離で消える", not g.waves)

# ---------------------------------------------------------------- 4. 刀
g = fresh([Ochimusha(300 + 8 + 34)], px=300)
e = g.enemies[0]
g.player.facing = 1
run(g, 1, (), {"attack"})
sword_seen = False
for _ in range(30):
    run(g, 1)
    if g.player.sword_rect() is not None and not sword_seen:
        sword_seen = True
        snap(g, "sword active")
check("刀の判定が出る", sword_seen)
check("刀で落ち武者を、1振りで倒す（2→0）", e.hp <= 0, "HP=%d" % e.hp)
e2 = Ochimusha(0)
e2.hit(C.SWORD_DAMAGE)
check("被弾すると光って、少し止まる", e2.flash == C.HIT_FLASH and e2.stun == C.HIT_STUN)

# ---------------------------------------------------------------- 5. 手裏剣
g = fresh([Ochimusha(480)], px=300)
e = g.enemies[0]
g.player.facing = 1
hits = []
effect_seen = False
released = False
for k in range(3):
    run(g, 1, (), {"throw"})
    for _ in range(60):
        run(g, 1)
        if g.shurikens and not released:
            released = True
            snap(g, "shuriken thrown")
        if g.effects and not effect_seen:
            effect_seen = True
            snap(g, "shuriken hit")
    hits.append(max(e.hp, 0))
check("手裏剣が発射される", released)
check("落ち武者は手裏剣2発で倒れる（2→1→倒れる）", hits == [1, 0, 0], str(hits))
check("命中の破片が出る", effect_seen)

# ---------------------------------------------------------------- 6. 狐火
g = fresh([Kitsunebi(600, "low")], px=300)
e = g.enemies[0]
ys, xs = [], []
far = Kitsunebi(900, "low")
g.enemies.append(far)
for _ in range(240):
    run(g, 1)
    ys.append(e.cy)
    xs.append(e.cx)
check("狐火は、近づくまで動かない（遠い狐火は、そのまま）", far.dir == 0 and far.cx == 900)
check("狐火は、上下に揺れる（振れ幅が約±12）", abs((max(ys) - min(ys)) / 2 - C.KITSUNEBI["bob"]) < 2.5,
      "振れ幅 %.1f" % ((max(ys) - min(ys)) / 2))
check("狐火は、主人公のいる側へ、まっすぐ進む", xs[-1] < xs[0] - 100, "x %.0f→%.0f" % (xs[0], xs[-1]))
g = fresh([Kitsunebi(600, "high")], px=100)
e = g.enemies[0]
run(g, 5)
check("遠い狐火は、動かない", e.cx == 600)
check("狐火（高め）は、地上の刀では届かない高さ", e.rect.bottom < C.FLOOR_Y - C.PLAYER_H - C.SWORD_H + 2 + 2 or
      e.rect.bottom < C.FLOOR_Y - 70)
g = fresh([Kitsunebi(500, "low")], px=300)
g.enemies[0].hit(C.SWORD_DAMAGE)
check("狐火は、刀1回で倒れる（やられの動きに入る）", not g.enemies[0].active and g.enemies[0].dying)
run(g, 6 * 4 + 2)
check("やられの動きが終わると、敵が消える", not g.enemies)
g = fresh([Kitsunebi(500, "low")], px=300)
g.enemies[0].hit(C.SHURIKEN_DAMAGE)
check("狐火は、手裏剣1発で倒れる", g.enemies[0].dying)

# ---------------------------------------------------------------- 7. 烏
g = fresh([Karasu(520)], px=300)
e = g.enemies[0]
x_start = e.cx
target = None
dive_start = None
for i in range(200):
    run(g, 1)
    if e.state == "dive" and dive_start is None:
        dive_start = i
        target = (g.player.rect.centerx, g.player.rect.centery)
        speed = math.hypot(e.vx, e.vy)
    if i == 25:
        telegraph_moved = abs(e.cx - x_start)
check("烏は、近づくまで待つ（予告の間は動かない）", telegraph_moved < 1, "予告中の移動 %.1f" % telegraph_moved)
check("予告は約0.5秒（30フレーム）", dive_start is not None and 28 <= dive_start <= 32, "急降下の開始 %s" % dive_start)
check("急降下の速さは3.5", dive_start is not None and abs(speed - C.KARASU["speed"]) < 0.01, "速さ %.2f" % speed)
vs = []
for py in (C.FLOOR_Y, C.FLOOR_Y - 60):      # 主人公が、地面にいるときと、高い所にいるとき
    g = fresh([Karasu(520)], px=300)
    g.player.py = float(py)
    e = g.enemies[0]
    e.t = C.KARASU["telegraph"]
    e.state = "telegraph"
    e.think(pygame.Rect(290, py - 30, 20, 30), C.STAGE_W)
    vs.append((round(e.vx, 3), round(e.vy, 3)))
check("烏の急降下の向きは、主人公の高さに関係なく、同じ", vs[0] == vs[1] and vs[0][1] > 0, str(vs))
g = fresh([Karasu(320)], px=300)
e = g.enemies[0]
e.t = C.KARASU["telegraph"]
e.state = "telegraph"
e.think(g.player.rect, C.STAGE_W)
check("主人公が真下にいても、まっすぐ落ちない（横へ進む）", abs(e.vx) > 1.5, "%.2f" % e.vx)
for _ in range(120):
    e.think(g.player.rect, C.STAGE_W)
check("烏は、地面を滑らず、すり抜けて飛び去る（画面の下で消える）", not e.alive and e.cy > C.FLOOR_Y)
g = fresh([Karasu(520)], px=300)
e = g.enemies[0]
nearest = 9999
for _ in range(400):
    run(g, 1)
    if e.state == "dive":
        nearest = min(nearest, math.hypot(e.cx - target[0], e.cy - target[1]))
    if not g.enemies:
        break
check("烏は、予告のときの主人公の位置へ向かう", nearest < 14, "最接近 %.0f" % nearest)
check("烏は、通り過ぎたら画面の外で消える", not g.enemies or not e.alive or e.cx < -50)

# ---------------------------------------------------------------- 7b. 絵（コマの切り替え）
g = fresh([Ochimusha(520)], px=100)
e = g.enemies[0]
imgs = set()
for _ in range(60):
    run(g, 1)
    imgs.add(id(e.image()))
check("落ち武者は、歩くと絵が切り替わる（4コマ）", len(imgs) == 4, "%d コマ" % len(imgs))
e2 = Ochimusha(0, g.a)
e2.ready_t = 30
a0 = id(e2.image())
e2.ready_t = 1
check("構えのコマに変わる（歩きとは別の絵）", a0 != id(Ochimusha(0, g.a).image()))
e3 = Ochimusha(0, g.a)
w0 = id(e3.image())
e3.hit(C.SWORD_DAMAGE); e3.hit(C.SWORD_DAMAGE)
check("やられのコマに変わる", id(e3.image()) != w0 and e3.dying)
art = {k: C.ENEMY_ART[k] for k in C.ENEMY_FRAMES}
sizes_ok = all(g.a.enemy[k][an][True][0].get_size() == (art[k]["w"], art[k]["h"])
               for k in C.ENEMY_FRAMES for an in C.ENEMY_FRAMES[k])
check("敵の絵の大きさが、設定（枠）と合っている", sizes_ok)

# ---------------------------------------------------------------- 8. 接触ダメージ・ゲームオーバー
for name, mk in (("落ち武者", lambda: Ochimusha(300)), ("狐火", lambda: Kitsunebi(300, "low")),
                 ("烏", lambda: Karasu(300))):
    g = fresh([mk()], px=300)
    e = g.enemies[0]
    e.cy = g.player.rect.centery
    hp = g.player.hp
    run(g, 1)
    check("%sに触れるとダメージ" % name, g.player.hp == hp - 1, "HP %d→%d" % (hp, g.player.hp))
snap(g, "hurt")
run(g, 2)
check("無敵中は連続ダメージを受けない", g.player.hp == C.PLAYER_HP - 1)
g.player.invincible = 0
g.player.hp = 1
g.enemies[0].cy = g.player.rect.centery
run(g, 1)
check("HP0でゲームオーバー", g.player.hp == 0)
snap(g, "game over")
g.step(set(), {"restart"})
check("暗転の途中は、Enterを押しても再開しない", g.player.hp == 0)


def bright(surface):
    return sum(sum(surface.get_at((x, y))[:3]) for x in range(0, C.BASE_W, 24) for y in range(0, C.BASE_H, 24))


surf = pygame.Surface((C.BASE_W, C.BASE_H))
g.draw(surf, font)
b_early = bright(surf)
run(g, C.GAMEOVER_START + C.GAMEOVER_FADE)
g.draw(surf, font)
b_late = bright(surf)
check("ゲームオーバー後、画面が暗くなる", b_late < b_early * 0.45, "明るさ %d → %d" % (b_early, b_late))
check("真っ黒にはならず、背景が見える", b_late > 0)
check("倒れた後は、倒れたままの絵", g.player.frame_index() == C.DEFEAT_END)
snap(g, "game over (dark)")
run(g, C.GAMEOVER_WAIT)
g.step(set(), {"restart"})
check("Enterで再開", g.player.hp == C.PLAYER_HP and g.player.px == 60 and len(g.enemies) == len(ENEMY_SPAWNS))

# ---------------------------------------------------------------- 9. 面の配置（実際の面）
g = Game()
snap(g, "stage start")
g.player.px = 1900.0
run(g, 1)
snap(g, "stage mid")
g.player.px = float(C.STAGE_W - 40)
run(g, 2)
check("カメラが面の端で止まる", g.cam_x == C.STAGE_W - C.BASE_W, "cam=%d" % g.cam_x)
snap(g, "stage end")


# ---------------------------------------------------------------- 11. 穴と足場
T = Terrain(OLD_GROUND, OLD_PLATFORMS)
pit1, pit2, pit3 = [(OLD_GROUND[i][1], OLD_GROUND[i + 1][0]) for i in range(3)]
check("穴が3つある（幅80・130・130）", [b - a for a, b in (pit1, pit2, pit3)] == [80, 130, 130])
check("落ち武者の配置が、すべて地面の上", all(T.ground_at(x - 8, x + 8) for k, x in ENEMY_SPAWNS if k == "ochimusha"))
check("足場が、ジャンプの高さ（約72）以下で、届く", all(C.FLOOR_Y - top <= 66 for _, _, top in OLD_PLATFORMS))


def run_until(gg, cond, held, limit=400):
    for _ in range(limit):
        gg.step(set(held))
        if cond(gg):
            return True
    return False


# 穴に落ちる → ダメージ2で、穴の手前に戻る
g = fresh(px=600)
run_until(g, lambda gg: gg.player.hp < C.PLAYER_HP, {"right"})
hp_after = g.player.hp
g.step(set())
check("穴に落ちるとダメージ2", hp_after == C.PLAYER_HP - C.FALL_DAMAGE, "HP %d→%d" % (C.PLAYER_HP, hp_after))
check("穴の手前の地面に戻る（縁から離れた所）", g.player.px < pit1[0] and g.player.py == C.FLOOR_Y and g.player.on_ground,
      "x=%.0f" % g.player.px)
check("戻った直後は無敵（点滅）", g.player.invincible > 0)
snap(g, "fell and respawned")

# 全力ジャンプで、幅80の穴を越えられる
g = fresh(px=560)
run(g, 30, {"right"})
run_until(g, lambda gg: gg.player.px >= pit1[0] - 1, {"right"})
g.step({"right"}, {"jump"})
run_until(g, lambda gg: gg.player.on_ground, {"right"})
check("幅80の穴は、ジャンプで越えられる（落ちない）", g.player.hp == C.PLAYER_HP and g.player.px > pit1[1], "x=%.0f" % g.player.px)


def at_edge_jump(gg, edge, held_right=True):
    run_until(gg, lambda g2: g2.player.px >= edge - 1, {"right"})   # 縁を踏み出す前に跳ぶ
    gg.step({"right"}, {"jump"})


# 幅130の穴は、足場なしでは越えられない
g = fresh(px=pit2[0] - 150)
g.terrain = Terrain(OLD_GROUND, ())     # 足場を外した地形
run(g, 40, {"right"})
at_edge_jump(g, pit2[0])
run_until(g, lambda gg: gg.player.hp < C.PLAYER_HP or (gg.player.on_ground and gg.player.px > pit2[1]), {"right"})
check("幅130の穴は、足場がないと越えられない（落ちる）", g.player.hp < C.PLAYER_HP)

# 足場を使うと越えられる（縁から足場へ、足場から向こう岸へ）
g = fresh(px=pit2[0] - 150)
run(g, 40, {"right"})
at_edge_jump(g, pit2[0])
plat = OLD_PLATFORMS[1]
landed = run_until(g, lambda gg: gg.player.on_ground, {"right"})
check("縁から、浮き足場に跳び乗れる", landed and g.player.py == plat[2] and plat[0] <= g.player.px <= plat[1],
      "x=%.0f 高さ=%.0f" % (g.player.px, g.player.py))
run_until(g, lambda gg: gg.player.px >= plat[1] - 8, {"right"})
g.step({"right"}, {"jump"})
run_until(g, lambda gg: gg.player.on_ground, {"right"})
check("足場から向こう岸へ渡れる（落ちない）", g.player.hp == C.PLAYER_HP and g.player.px > pit2[1] - 6 and g.player.py == C.FLOOR_Y,
      "x=%.0f HP=%d" % (g.player.px, g.player.hp))
snap(g, "on platform")

# 一方通行: 下から突き抜けて、上に乗れる
p0 = OLD_PLATFORMS[0]
g = fresh(px=(p0[0] + p0[1]) / 2)
g.step(set(), {"jump"})
peak_y = 99999
for _ in range(80):
    g.step(set())
    peak_y = min(peak_y, g.player.py)
    if g.player.on_ground and g.player.py != C.FLOOR_Y:
        break
check("下からのジャンプで、足場を突き抜けて、上に乗れる", g.player.py == p0[2] and peak_y < p0[2], "頭が止まらず、乗った高さ=%.0f" % g.player.py)
g.step(set())
check("足場の上に立っていられる", g.player.on_ground and g.player.py == p0[2])
# 足場の端から歩いて降りる
run_until(g, lambda gg: gg.player.py == C.FLOOR_Y and gg.player.on_ground, {"right"})
check("足場の端から歩くと、落ちて地面に降りる", g.player.py == C.FLOOR_Y)
# 早く離す小ジャンプでは、足場に届かない
g = fresh(px=(p0[0] + p0[1]) / 2)
g.step(set(), {"jump"})
g.step(set(), {"jump_release"})
run(g, 70)
check("小ジャンプでは、高い足場に乗れない", g.player.py == C.FLOOR_Y)

# 落ち武者は、穴の縁で止まる（落ちない）
g = fresh([Ochimusha(pit1[0] - 20)], px=pit1[1] + 40)
run(g, 300)
check("落ち武者は、穴の縁で止まる", g.enemies[0].cx <= pit1[0] + 4 and g.enemies[0].alive, "x=%.0f" % g.enemies[0].cx)

# 穴に落ちて体力が尽きたら、ゲームオーバー
g = fresh(px=600)
g.player.hp = 2
run_until(g, lambda gg: gg.player.hp <= 0, {"right"})
check("体力が尽きる落下は、ゲームオーバー", g.player.hp == 0)
snap(g, "game over by fall")

# ---------------------------------------------------------------- 10. 慣性
def vx_after(frames, held):
    gg = fresh(px=800)
    for _ in range(frames):
        gg.step(set(held))
    return gg


gg = fresh(px=800)
gg.step({"right"})
check("押した直後はまだ遅い（加速する）", 0 < gg.player.vx < 0.5, "vx=%.2f" % gg.player.vx)
gg = vx_after(25, {"right"})
check("しばらく押すと最高速に届く", abs(gg.player.vx - C.MAX_SPEED) < 0.01, "vx=%.2f" % gg.player.vx)
x_release = gg.player.px
gg.step(set())
check("離した直後はまだ動いている（滑る）", gg.player.vx > 1.5, "vx=%.2f" % gg.player.vx)
n = 0
while abs(gg.player.vx) > 0 and n < 60:
    gg.step(set())
    n += 1
check("離すと十数フレームで止まる", 8 <= n <= 20, "止まるまで %d フレーム" % n)
check("滑った距離が0より大きい", gg.player.px - x_release > 10, "滑走 %.0f px" % (gg.player.px - x_release))
gg = vx_after(25, {"right"})
gg.step({"left"})
check("切り返すと、すぐ左を向く（体は、まだ少し右へすべっている）", gg.player.facing == -1 and gg.player.vx > 0)
gg.step({"left"}, {"attack"})
check("切り返してすぐ刀を振ると、押している向きに出る", gg.player.attack_t > 0 and gg.player.facing == -1)
gg = vx_after(25, {"right"})
gg.step({"left"}, {"attack"})
check("右へ走りながら、左を押して刀を振ると、振り向いて出る", gg.player.attack_t > 0 and gg.player.facing == -1)
gg = vx_after(5, {"right"})
gg.step(set(), {"attack"})
total = sum(n for _, n in C.SWORD_SEQ)
swing = total - C.SWORD_SEQ[-1][1]      # 振り終わるまで（このあとが、隙）
from sprites import seq_frame
for _ in range(swing - 7):
    gg.step(set())
gg.step(set(), {"throw"})
check("刀を振っている途中で手裏剣を押しても、まだ出ない（覚えておく）", gg.player.attack_t > 0 and not gg.player.throw_t and gg.player.queued == "throw")
for _ in range(7):
    gg.step(set())
check("刀を振り終わったら、隙を待たずに、すぐ手裏剣が出る（押し直さなくていい）", gg.player.throw_t > 0 and not gg.player.attack_t and gg.player.queued is None)
gg = vx_after(5, {"right"})
gg.step(set(), {"attack"})
for _ in range(swing + 1):
    gg.step(set())
check("振り終わったあとは、隙（まだ、刀の動きの途中）", gg.player.attack_t > 0 and gg.player.recovering and gg.player.sword_rect() is None)
gg.step({"left"})
check("隙は、歩く・向きを変えるで打ち切れる", not gg.player.attack_t and gg.player.facing == -1)
gg = vx_after(5, {"right"})
gg.step(set(), {"attack"})
for _ in range(swing + 1):
    gg.step(set())
gg.step(set(), {"jump"})
check("隙は、ジャンプで打ち切れる", not gg.player.attack_t and not gg.player.on_ground)
gg = vx_after(5, {"right"})
gg.step(set(), {"attack"})
for _ in range(swing + 1):
    gg.step(set())
n0 = gg.player.swing_id
gg.step(set(), {"attack"})
check("刀の隙は、次の刀では打ち切れない（連打しても、速くならない）", gg.player.swing_id == n0 and gg.player.recovering)
waited = 0
for _ in range(C.SWORD_SEQ[-1][1] + C.SWORD_COOLDOWN + 4):
    if gg.player.swing_id != n0:
        break
    gg.step(set())
    waited += 1
check("刀は、振り終わってから少し間をおいて、次が出る（連打しても、速くならない。押し直さなくていい）",
      gg.player.swing_id == n0 + 1 and waited >= C.SWORD_SEQ[-1][1] + C.SWORD_COOLDOWN - 3, "待ち %d" % waited)
gg = vx_after(5, {"right"})
starts, last = [], gg.player.swing_id
for f in range(160):
    gg.step(set(), {"attack"})      # 連打する
    if gg.player.swing_id != last:
        starts.append(f)
        last = gg.player.swing_id
per = (starts[-1] - starts[0]) / max(1, len(starts) - 1)
check("刀を連打したときの間隔は、1振り＋間（約0.6秒）", total + C.SWORD_COOLDOWN - 2 <= per <= total + C.SWORD_COOLDOWN + 4, "%.1f フレームに1回" % per)
gg = vx_after(5, {"right"})
gg.step(set(), {"attack"})
for _ in range(swing + 1):
    gg.step(set())
gg.step({"right"})
check("刀の間のあいだも、歩く・手裏剣は、すぐできる", not gg.player.attack_t and gg.player.sword_cool > 0 and gg.player.vx > 0)
gg.step(set(), {"throw"})
check("（手裏剣）", gg.player.throw_t > 0)
gg = vx_after(5, {"right"})
gg.step(set(), {"attack"})
for _ in range(swing + 1):
    gg.step(set())
gg.step(set(), {"throw"})
check("刀の隙は、手裏剣で打ち切れる", gg.player.throw_t > 0 and not gg.player.attack_t)
gg = vx_after(25, {"right"})
gg.step({"right"}, {"attack"})
for _ in range(swing - 1):
    gg.step({"right"})
check("右を押したまま刀を振ると、止まらずに、少し遅く進み続ける",
      gg.player.attack_t > 0 and abs(gg.player.vx - C.MAX_SPEED * C.ATTACK_MOVE) < 0.01, "vx=%.2f" % gg.player.vx)
gg.step({"right"})
gg.step({"right"})
check("振り終わると、そのまま走りに戻る（止まらない）", not gg.player.attack_t and gg.player.vx > C.MAX_SPEED * C.ATTACK_MOVE)
gg = fresh()
run(gg, 5)
gg.step({"right"}, {"jump"})
check("立ったまま、右を押しながら跳ぶと、すぐ斜めに跳ぶ（横の速さを、最初から持つ）",
      not gg.player.on_ground and abs(gg.player.vx - C.MAX_SPEED * C.JUMP_START) < 0.2, "vx=%.2f" % gg.player.vx)
gg = fresh()
run(gg, 5)
gg.step(set(), {"jump"})
check("何も押さずに跳ぶと、真上に跳ぶ", not gg.player.on_ground and gg.player.vx == 0)
while gg.player.vy < 0 or gg.player.py < C.FLOOR_Y - 30:
    gg.step(set())
gg.step({"left"}, {"jump"})
check("着地の少し前にジャンプを押しても、まだ跳ばない（覚えておく）", gg.player.vy > 0 and gg.player.jump_q > 0)
landed = False
for _ in range(C.JUMP_BUFFER):
    gg.step({"left"})
    landed = landed or gg.player.vy < 0
check("着地したら、すぐ跳ぶ（押し直さなくていい。押している向きへ、斜めに）", landed and not gg.player.on_ground and gg.player.vx < -1.5, "vx=%.2f" % gg.player.vx)
gg = fresh()
run(gg, 5)
gg.player.on_ground, gg.player.py = False, C.FLOOR_Y - 60.0     # 足場の縁から出た直後（跳んではいない）
run(gg, 3)
gg.step(set(), {"jump"})
check("足場の縁から出てしまった直後でも、跳べる", gg.player.vy < 0 and gg.player.jumped)
gg.step(set(), {"jump"})
run(gg, C.JUMP_BUFFER)
check("空中では、もう一度は跳べない", gg.player.vy > C.JUMP_SPEED + 1)
gg = fresh()
run(gg, 5)
gg.player.on_ground, gg.player.py = False, C.FLOOR_Y - 60.0
run(gg, C.COYOTE + 2)
gg.step(set(), {"jump"})
check("縁から出て、時間がたつと、跳べない", gg.player.vy > 0)
gg = vx_after(5, {"right"})
gg.step(set(), {"attack"})
for _ in range(4):
    gg.step({"left"}, {"jump"})
check("振っている途中は、打ち切れない", gg.player.attack_t > 0 and gg.player.on_ground and gg.player.facing == 1)
gg = vx_after(5, {"right"})
gg.step(set(), {"attack"})
gg.step(set(), {"throw"})
for _ in range(total + 2):
    gg.step(set())
check("早すぎる入力は、忘れる（勝手に出ない）", not gg.player.throw_t and not gg.player.attack_t and gg.player.queued is None)
gg = vx_after(25, {"right"})
gg.step({"left"})
for _ in range(30):
    gg.step({"left"})
check("そのまま押すと左向きに変わって左へ進む", gg.player.facing == -1 and gg.player.vx < 0)
gg = vx_after(25, {"right"})
gg.step({"right"}, {"jump"})
vx_jump = gg.player.vx
for _ in range(10):
    gg.step(set())
check("ジャンプ中に手を離しても勢いが残る", gg.player.vx > vx_jump - 0.3 and not gg.player.on_ground)
gg = vx_after(25, {"right"})
gg.step({"right"}, {"jump"})
n = 0
while gg.player.vx > -1.0 and n < 120 and not gg.player.on_ground:
    gg.step({"left"})
    n += 1
check("空中で逆向きに押すと約0.3秒で反転方向に動く", n <= 30 and gg.player.vx <= -1.0, "%d フレーム" % n)
check("空中で向きを変えられる", gg.player.facing == -1)
gg = fresh(px=800)
gg.step(set(), {"jump"})
for _ in range(5):
    gg.step(set())
gg.step(set(), {"attack"})
gg.step({"left"})
check("空中で刀を振っていても向きを変えられる", gg.player.facing == -1)
gg = vx_after(25, {"right"})
gg.step({"right"}, {"attack"})
for _ in range(10):
    gg.step({"left"})
check("地上の攻撃中は入力を受けず、向きも変わらない", gg.player.attack_t > 0 and gg.player.facing == 1)
for _ in range(5):
    gg.step({"left"})
check("振っている間は、滑って止まっていく（入力は無視されたまま。振り終わると、打ち切れる）",
      gg.player.attack_t > 0 and abs(gg.player.vx) < 0.01 and gg.player.facing == 1)


def jump_height(release_after):
    gg = fresh(px=800)
    gg.step(set(), {"jump"})
    top = gg.player.py
    for i in range(1, 80):
        gg.step(set(), {"jump_release"} if i == release_after else set())
        top = min(top, gg.player.py)
    return C.FLOOR_Y - top


h_long, h_short = jump_height(None), jump_height(2)
check("ボタンを長く押すと高く、早く離すと低い", h_short < h_long * 0.7, "長押し %.0f / 早離し %.0f" % (h_long, h_short))
check("早く離しても跳ぶ", h_short > 15)


def air():
    gg = fresh(px=800)
    gg.step(set(), {"jump"})
    up = down = 0
    peaked = False
    for _ in range(200):
        gg.step(set())
        if gg.player.on_ground:
            break
        if not peaked and gg.player.vy > 0:
            peaked = True
        if peaked:
            down += 1
        else:
            up += 1
    return up, down


up, down = air()
check("下降は上昇より速い（ふわっとしない）", down < up, "上昇 %d / 下降 %d" % (up, down))

# ---------------------------------------------------------------- 12. 起伏（段差・高台・谷）
R = Terrain()   # 本物の1面
Tn = C.FLOOR_Y
check("地面に高低差がある（4段階以上）", len({top for _, _, top in GROUND}) >= 4)
steps = [abs(a[2] - b[2]) for a, b in zip(GROUND, GROUND[1:]) if a[1] == b[0]]
check("つながった地面の段差は32以下（高い塔の壁は、足場を使って登る。2か所まで）", sum(1 for s in steps if s > 40) <= 2 and sum(1 for s in steps if 32 < s <= 40) == 0,
      "最大 %d" % max(steps))
check("落ち武者の配置が、すべて地面の上", all(R.height_at(x) is not None for k, x in ENEMY_SPAWNS if k == "ochimusha"))


def real(px, py=None):
    gg = Game()
    gg.lives = 1
    gg.enemies = []
    gg.player.px = float(px)
    if py is not None:
        gg.player.py = float(py)
    return gg


# 段差の角をかすめて降りたあと、壁に入り込まない（入り込むと、地面の下へ落ちる）
g = real(380, Tn - 16)
for _ in range(120):
    run(g, 1, {"left"})
    if g.player.on_ground and g.player.py == Tn:
        break
x_drop = g.player.px
run(g, 150, {"right"})
check("段差から降りて、すぐ引き返しても、壁に入り込まない（落ちない）",
      g.player.hp == C.PLAYER_HP and g.player.py == Tn and g.player.px <= 360 - C.PLAYER_W / 2 + 0.01,
      "降りた所 x=%.1f → x=%.1f y=%.0f HP %d" % (x_drop, g.player.px, g.player.py, g.player.hp))
ok = True
for start in range(300, 352, 3):   # いろいろな間合いで、段差に向かって跳ぶ（届かない跳び方も含む）
    for hold in (2, 6, 12, 30):
        g = real(start)
        run(g, 1, {"right"}, {"jump"})
        run(g, hold, {"right"})
        run(g, 1, {"right"}, {"jump_release"})
        run(g, 200, {"right"})
        if g.player.hp < C.PLAYER_HP or (g.player.py == Tn and g.player.px > 360 - C.PLAYER_W / 2 + 0.01):
            ok = False
            bad = (start, hold, g.player.px, g.player.py, g.player.hp)
check("段差に向かって、どんな間合いで跳んでも、壁に入り込まない（落ちない）", ok, "" if ok else "x=%d 長さ%d → x=%.1f y=%.0f HP %d" % bad)
# 段差にぶつかると止まる
g = real(300)
run(g, 90, {"right"})
check("段差の壁にぶつかって止まる（乗り越えない）", abs(g.player.px - (360 - C.PLAYER_W / 2)) < 1 and g.player.py == Tn,
      "x=%.1f y=%.0f" % (g.player.px, g.player.py))
# ジャンプで段差に登る
g = real(330)
run(g, 1, {"right"}, {"jump"})
run_until(g, lambda gg: gg.player.on_ground and gg.player.px > 365, {"right"})
check("ジャンプで段差（+16）に登れる", g.player.py == Tn - 16 and g.player.px > 365, "y=%.0f" % g.player.py)
# 高台から飛び降りる
g = real(600, Tn - 32)
run_until(g, lambda gg: gg.player.px > 660, {"right"})
run(g, 30, {"right"})
check("高台から歩いて降りられる（ダメージなし）", g.player.hp == C.PLAYER_HP and g.player.py in (Tn - 16, Tn), "y=%.0f" % g.player.py)
# 谷の塔を、足場づたいに登る（谷底 → 足場 → 足場 → 塔のてっぺん）
def hop(px, py, held, hold_jump=True):
    gg = real(px, py)
    run(gg, 1, held, {"jump"})
    run_until(gg, lambda g2: g2.player.on_ground, held)
    return gg.player.px, gg.player.py


px, py = hop(1428, Tn, {})
check("谷底から、1つ目の足場（高さ56）に乗れる", py == Tn - 56, "y=%.0f x=%.0f" % (py, px))
px, py = hop(1440, Tn - 56, {"right"})
check("1つ目から、2つ目の足場（高さ108）に乗れる", py == Tn - 108, "y=%.0f x=%.0f" % (py, px))
px, py = hop(1485, Tn - 108, {"right"})
check("2つ目から、塔のてっぺん（高さ150）に乗れる", py == Tn - 150 and px > 1500, "y=%.0f x=%.0f" % (py, px))
gg = real(1570, Tn - 150)
run_until(gg, lambda g2: g2.player.on_ground and g2.player.py != Tn - 150, {"right"})
check("塔のてっぺんから、歩いて降りられる（ダメージなし）", gg.player.hp == C.PLAYER_HP and gg.player.py == Tn - 32, "y=%.0f" % gg.player.py)
gg = real(1470, Tn)
run(gg, 60, {"right"})
check("塔の壁には、下からは登れない", gg.player.py == Tn and gg.player.px <= 1500 - C.PLAYER_W / 2 + 1)
# 穴に落ちたら、落ちる前に立っていた高さの地面へ戻る
g = real(1630, Tn - 32)
g.player.safe_x, g.player.safe_y = 1580.0, float(Tn - 32)
run_until(g, lambda gg: gg.player.hp < C.PLAYER_HP, {"right"})
check("穴に落ちると、元の高さの地面に戻る", g.player.hp == C.PLAYER_HP - C.FALL_DAMAGE and g.player.py == Tn - 32 and g.player.px < 1650,
      "x=%.0f y=%.0f" % (g.player.px, g.player.py))
# 落ち武者は、高台の上で、段差から落ちずにうろうろする
g = real(100)
g.enemies = [Ochimusha(520, g.a, R.height_at(520))]
e = g.enemies[0]
xs = []
for _ in range(600):
    run(g, 1)
    xs.append(e.cx)
check("落ち武者は、高台の上に立つ", e.rect.bottom == Tn - 32, "足元 %d" % e.rect.bottom)
check("落ち武者は、高台から落ちない", 470 <= min(xs) and max(xs) <= 640)
snap(real(430, Tn - 16), "steps")

# 落ち武者は、端（穴）まで行ったら、折り返す
g = fresh([Ochimusha(640)], px=800)
e = g.enemies[0]
xs = []
for _ in range(500):
    run(g, 1)
    xs.append(e.cx)
check("落ち武者は、穴の縁まで行って止まる（落ちない）", max(xs) < 700 and max(xs) > 690, "最大 %.0f" % max(xs))
check("落ち武者は、端で折り返して戻る（行ったり来たりする）", min(xs[200:]) < 650, "後半の最小 %.0f" % min(xs[200:]))

# ---------------------------------------------------------------- 13. 足場の配置・アイテム
# 地面と足場を「面」として、ジャンプで渡れるか（横のすき間90以下・上り66以下）を、すべての面で調べる
from stage import STAGES  # noqa: E402
for st in STAGES:
    surf = [(a, b, top) for a, b, top in st.ground] + [(a, b, top) for a, b, top in st.platforms]
    surf += [s2 for m in st.movers for s2 in ((m[0], m[0] + m[4], m[1]), (m[2], m[2] + m[4], m[3]))]    # 動く足場は、両端の位置を、足場として数える
    ng = len(st.ground)
    reach = {0}
    frontier = [0]
    while frontier:
        i = frontier.pop()
        for j, (a2, b2, t2) in enumerate(surf):
            if j in reach:
                continue
            a1, b1, t1 = surf[i]
            gap = max(a2 - b1, a1 - b2, 0)
            if gap <= 90 and (t1 - t2) <= 66 and not (j < ng and i < ng and (t1 - t2) > 40 and gap == 0):
                reach.add(j)
                frontier.append(j)
    check("[%s] すべての地面と足場に、ジャンプで行ける" % st.name, len(reach) == len(surf),
          "行けない: %s" % [surf[k] for k in range(len(surf)) if k not in reach])
    sp = Terrain(st.ground, st.platforms)
    check("[%s] 落ち武者の配置が、すべて地面の上" % st.name, all(sp.height_at(x) is not None for k, x in st.spawns if k == "ochimusha"))
    check("[%s] アイテムが、地面の中に埋まっていない" % st.name,
          all((sp.height_at(x) is None) or (y + C.ITEM_SIZE / 2 <= sp.height_at(x) + 1) for _, x, y in st.items))
    check("[%s] 団子がある・敵がいる・中間地点が地面の上" % st.name,
          st.dango_total > 0 and len(st.spawns) > 0 and sp.height_at(st.checkpoint[0]) == st.checkpoint[1])
check("アイテムが、地面の中に埋まっていない", all((R.height_at(x) is None) or (y + C.ITEM_SIZE / 2 <= R.height_at(x) + 1) for _, x, y in ITEMS))
check("アイテムは、団子・おにぎり・金の葉の3種類", {k for k, _, _ in ITEMS} == {"dango", "onigiri", "leaf"})


def item_game(kind):
    gg = real(300)
    gg.items = [Item(kind, 300, C.FLOOR_Y - 18, gg.a)]
    return gg


g = item_game("dango")
run(g, 2)
check("団子を取るとスコア +%d" % C.SCORE_DANGO, g.score == C.SCORE_DANGO and not g.items)
g = item_game("onigiri")
g.player.hp = 3
run(g, 2)
check("おにぎりで体力が回復する", g.player.hp == 3 + C.HEAL_ONIGIRI and not g.items)
g = item_game("onigiri")
run(g, 2)
check("体力満タンでは、おにぎりは、スコアになる（体力は増えすぎない）", g.player.hp == C.PLAYER_HP and g.score == C.SCORE_FULL_HP)
g = item_game("leaf")
run(g, 2)
check("金の葉で強化される", g.player.power)
g = real(300)
g.player.power = True
g.enemies = [Ochimusha(480, g.a, C.FLOOR_Y)]
g.player.facing = 1
run(g, 1, (), {"attack"})
run(g, 30)
check("強化中に刀を振ると、光波が出る", g.slashes or g.enemies[0].hp < 4, "光波 %d" % len(g.slashes))
hp_e = g.enemies[0].hp
g = real(300)
g.player.power = True
g.enemies = [Ochimusha(520, g.a, C.FLOOR_Y)]
g.player.facing = 1
e = g.enemies[0]
run(g, 1, (), {"attack"})
run_until(g, lambda gg: gg.player.hp < C.PLAYER_HP or e.hp < e.max_hp or e.dying, {})
check("光波は、離れた敵にも、ダメージを与える", e.hp < e.max_hp or e.dying, "敵HP %d" % e.hp)
g = real(300)
g.player.power = True
g.player.take_damage(400, 1)
check("ダメージを受けると、強化が消える", not g.player.power)
g = real(300)
g.player.attack()
run(g, 30)
check("強化していないと、光波は出ない", not g.slashes)
g = real(300)
g.player.power = True
g.score = 500
g.reset()
check("やり直すと、スコアと強化がもとに戻る", g.score == 0 and not g.player.power and len(g.items) == len(ITEMS))
snap(item_game("dango"), "items")

# ---------------------------------------------------------------- 14. 残機・中間地点・団子の数
DANGO_TOTAL = STAGE1_LEGACY.dango_total   # 古い短い版の月見坂の団子の数
from stage import CHECKPOINT  # noqa: E402


def kill(gg):
    gg.player.hp = 1
    gg.player.take_damage(gg.player.px + 5, 1)
    gg.step(set())


g = Game()
check("残機は%d" % C.LIVES, g.lives == C.LIVES)
check("団子は、全部で%d個" % DANGO_TOTAL, DANGO_TOTAL == sum(1 for k, _, _ in ITEMS if k == "dango") and DANGO_TOTAL > 0)
g.enemies = []
kill(g)
check("やられると、残機が1減る", g.lives == C.LIVES - 1 and g.player.hp == 0)
run(g, C.RESPAWN_AT - 5)
check("残機があるうちは、「無念」にならず、少しして自動で再開する", g.player.hp == 0)
snap(g, "lives left")
run(g, 10)
check("再開すると、体力が満タンで、最初から", g.player.hp == C.PLAYER_HP and g.player.px == 60 and g.lives == C.LIVES - 1)
check("再開すると、敵が元の配置に戻る", len(g.enemies) == len(ENEMY_SPAWNS))
# 中間地点
g = Game()
g.enemies = []
g.player.px, g.player.py = float(CHECKPOINT[0]), float(CHECKPOINT[1])
g.score, g.dango = 700, 7
run(g, 2)
check("中間地点（鳥居）を通ると、有効になる", g.checkpoint.active and g.cp_state is not None)
g.score, g.dango = 900, 9
kill(g)
run(g, C.RESPAWN_AT + 5)
check("やられると、中間地点から再開する", abs(g.player.px - CHECKPOINT[0]) < 1 and g.player.py == CHECKPOINT[1] and g.player.hp == C.PLAYER_HP,
      "x=%.0f y=%.0f" % (g.player.px, g.player.py))
check("再開すると、スコアと団子の数が、中間地点のときに戻る", g.score == 700 and g.dango == 7, "%d / %d" % (g.score, g.dango))
check("中間地点より前に取ったアイテムは、戻らない", all(it.idx >= 0 for it in g.items))
near = [e for e in g.enemies if abs(e.cx - CHECKPOINT[0]) <= C.RESPAWN_CLEAR]
check("再開した場所の近くには、敵がいない", not near and 0 < len(g.enemies) < len(ENEMY_SPAWNS), "%d / %d" % (len(near), len(g.enemies)))
check("再開してすぐは、無敵", g.player.invincible > 0)
run(g, C.INVINCIBLE_FRAMES + 30)
check("再開して、動かずにいても、すぐにはやられない", g.player.hp == C.PLAYER_HP, "HP %d" % g.player.hp)
# 残機0 → ゲームオーバー
g = Game()
g.enemies = []
g.lives = 1
kill(g)
check("最後の残機でやられると、ゲームオーバー（自動で再開しない）", g.lives == 0)
run(g, C.RESPAWN_AT + 20)
check("ゲームオーバーでは、再開しない", g.player.hp == 0)
run(g, 1, (), {"restart"})
check("Enterで、最初から（残機も初期値に戻る）", g.player.hp == C.PLAYER_HP and g.lives == C.LIVES and g.score == 0)
# 団子 = 手裏剣を投げられる数（悪魔城ドラキュラのサブウェポンと同じ扱い）
A = C.AMMO
g = fresh(px=300)
check("面の始まりは、団子を %d 持っている（持てるのは %d まで）" % (A["start"], A["max"]), g.player.ammo == A["start"] < A["max"])
run(g, 1, (), {"throw"})
run_until(g, lambda gg: gg.shurikens, (), 40)
check("手裏剣を投げると、団子が1つ減る", g.player.ammo == A["start"] - A["cost"] and len(g.shurikens) == 1)
run(g, 60)
g.player.triple = True
n0 = g.player.ammo
run(g, 1, (), {"throw"})
run_until(g, lambda gg: gg.shurikens, (), 40)
check("三方手裏剣は、3つ出ても、団子は1つしか減らない", len(g.shurikens) == 3 and g.player.ammo == n0 - A["cost"])
g = fresh(px=300)
g.player.ammo = 0
run(g, 1, (), {"throw"})
run(g, 20)
check("団子が無いと、手裏剣は投げられない（ゲージが、赤く点滅する）", not g.shurikens and not g.player.throw_t and g.player.empty_t > 0)
snap(g, "ammo empty")
run(g, 1, (), {"attack"})
check("団子が無くても、刀は振れる", g.player.attack_t > 0)
g = fresh(px=300)
g.player.ammo = 3
g.items = [Item("dango", g.player.px, g.player.py - 8, g.a, 0)]
run(g, 2)
check("団子を拾うと、投げられる数が %d 増える（スコアも入る）" % A["dango"], g.player.ammo == 3 + A["dango"] and g.score == C.SCORE_DANGO)
g.player.ammo = A["max"] - 1
g.items = [Item("dango", g.player.px, g.player.py - 8, g.a, 1)]
run(g, 2)
check("団子は、持てる数までしか増えない", g.player.ammo == A["max"])
g.lives = 3
g.player.ammo = 1
g.player.hp = 0
for _ in range(C.RESPAWN_AT + 5):
    g.step(set())
check("やられて再開すると、団子は、始まりの数に戻る（無いまま再開しない）", g.player.hp > 0 and g.player.ammo == A["start"])
check("団子を全部取っても、残機は増えない（団子は、集める物ではなく、使う物になった）", g.lives == 2)
few = [(st.name, st.dango_total) for st in PROD_STAGES]
check("本番の面の団子は、足場の上にだけ、1つずつ（地面には置かない）。1面に 26個まで",
      all(n <= 26 for _, n in few) and all(sum(p[0] <= x <= p[1] and 0 < p[2] - y <= 60 for p in st.platforms) == 1
                                            for st in PROD_STAGES for k, x, y in st.items if k == "dango"), str(few))


def _purpose(st, p):
    """足場の役目: 穴を渡る / 上に物がある / ボスの間（ボスを跳び越える）/ 崖登りの足場。どれも無ければ、意味の無い足場"""
    cx = (p[0] + p[1]) / 2
    holes = [(a1, b0) for (_, a1, _), (b0, _, _) in zip(st.ground, st.ground[1:]) if b0 > a1]
    return (any(h0 - 10 <= cx <= h1 + 10 for h0, h1 in holes) or any(p[0] - 6 <= x <= p[1] + 6 and 0 < p[2] - y <= 60 for _, x, y in st.items)
            or any(a["x0"] <= cx <= a["x1"] for a in st.arenas) or bool(st.climb and st.climb[0] <= cx < st.climb[1]))


idle = [(st.name, p[0], p[1]) for st in PROD_STAGES for p in st.platforms if not _purpose(st, p)]
check("[本番] 意味の無い足場が無い（どの足場も、穴を渡るか、上に物があるか、ボスの間にある）", not idle, str(idle))

# ---------------------------------------------------------------- 15. ボスの場所
def boss_game():
    """ボスの場所に入った直後のゲーム（主人公は、当たっても体力が減らないようにしておく）"""
    gg = Game()
    gg.lives = 1
    gg.score, gg.dango = 1500, 9
    gg.player.px, gg.player.py = float(C.ARENA_X0 + C.BASE_W // 2 - 1), float(C.FLOOR_Y)
    run(gg, 30, {"right"})
    return gg


def boss_until(gg, cond, limit=1200):
    for _ in range(limit):
        gg.player.invincible = 5
        gg.step(set())
        if cond(gg):
            return True
    return False


g = Game()
g.player.px, g.player.py = float(C.ARENA_X0 + 100), float(C.FLOOR_Y)
run(g, 3)
check("ボスの場所の手前では、ボスは出ない（曲は、面の曲）", not g.boss_on and g.boss is None and g.bgm == C.BGM_STAGE1)
g = boss_game()
b = g.boss
check("最後の1画面に入りきると、ボスが出て、画面が止まる", g.boss_on and b is not None and g.cam_x == C.ARENA_X0)
gg = Game()
gg.player.px, gg.player.py = float(C.ARENA_X0 + C.BOSS_TRIGGER - 20), float(C.FLOOR_Y)
for _ in range(60):
    if gg.boss_on:
        break
    gg.step({"right"})
cam0 = gg.cam_x
check("ボスの場所に少し入ると、もうボスが出る（画面は、まだ右端に着いていない）", gg.boss_on and gg.boss is not None and cam0 < C.ARENA_X0, "cam=%d" % cam0)
for _ in range(60):
    if gg.cam_x == C.ARENA_X0:
        break
    gg.step(set())
check("画面は、右端まで流れて止まる（ボスと、離れて向き合う。ボスは、まだ降ってきていない）",
      gg.cam_x == C.ARENA_X0 and gg.boss.state == "wait" and C.BOSS_X - gg.player.px > 200, "間 %.0f" % (C.BOSS_X - gg.player.px))
check("ボスが出ると、ザコ敵が消えて、まず静かになる（曲が止まる）", not g.enemies and g.bgm is None and b.state == "wait" and b.rect.bottom < 0)
x0 = g.player.px
run(g, 20, {"right"}, {"jump"})
check("ボスが出てくる場面の間は、主人公を動かせない", g.boss_intro and g.player.on_ground and abs(g.player.px - x0) < 30, "%.0f → %.0f" % (x0, g.player.px))
boss_until(g, lambda gg: gg.boss.state == "drop")
check("少し待ってから、画面の上から降ってくる", b.st <= 1 and b.rect.top < 0 and g.bar_t == C.BOSS_INTRO["bar_frames"], "帯 %d" % g.bar_t)
hp0 = b.hp
boss_until(g, lambda gg: gg.boss.state == "land")
check("ボスが降ってくると、タヌキ侍が驚く（ボスのほうを向く）", g.player.startle_t > 0 and g.player.facing == 1)
snap(g, "boss startle")
check("着地すると、画面が揺れて、ボスの曲が始まる", g.shake_t > 0 and g.bgm == C.BGM_BOSS, "揺れ %d" % g.shake_t)
check("ボスは、地面に着地している", b.state != "drop" and b.rect.bottom == round(C.FLOOR_Y), "%s 下端 %d" % (b.state, b.rect.bottom))
boss_until(g, lambda gg: gg.boss.state == "pose" and gg.boss.st == gg.boss.intro["pose"] // 2)
b.hit(2)
check("着地のあと、立って止まる（名前が出る）。出てくる場面の間は、攻撃を受けない", b.hp == hp0 and g.boss_intro)
snap(g, "boss")
t0 = g.frames
boss_until(g, lambda gg: not gg.boss_intro)
check("名前が消えると、戦いが始まる（動かせるようになる）", b.state == "walk" and g.frames - t0 >= b.intro["pose"] // 2 - 1)
boss_until(g, lambda gg: gg.bar_t == 0, 100)
check("上下の黒い帯は、戦いが始まると消える", g.bar_t == 0)
b.hit(2)
check("攻撃を受けても、ひるまない（体力は減る）", b.hp == hp0 - 2 and b.stun == 0 and b.flash > 0)
ok = boss_until(g, lambda gg: gg.boss.state == "ready")
check("歩いたあと、構える（光波の予告）", ok)
ok = boss_until(g, lambda gg: gg.waves)
w = g.waves[0] if g.waves else None
check("構えのあと、主人公のいる側へ光波を出す", ok and w.dir == b.facing == -1)
check("最初の光波は、低い。足元を速く飛ぶ（ジャンプか刀で対処）", w is not None and not w.tall and w.speed > C.WAVE["speed"] and w.rect.bottom <= C.FLOOR_Y and w.rect.top > C.FLOOR_Y - 30)
snap(g, "boss wave")
ok = boss_until(g, lambda gg: gg.boss.state == "recover")
check("攻撃のあとに、隙がある", ok)
ok = boss_until(g, lambda gg: gg.boss.state == "crouch")
check("3回に1回は、かがむ（跳びかかりの予告）", ok and b.count == 3, "回数 %d" % b.count)
target = g.player.rect.centerx
ok = boss_until(g, lambda gg: gg.boss.state == "leap")
top = C.FLOOR_Y
while b.state == "leap":
    g.player.invincible = 5
    g.step(set())
    top = min(top, b.rect.bottom)
check("跳びかかりは、下をくぐれる高さまで上がる", C.FLOOR_Y - top > C.PLAYER_H + 20, "高さ %d" % (C.FLOOR_Y - top))
check("跳びかかりは、かがんだときの主人公の位置に着地する", abs(b.cx - max(b.x_min, target)) < 2, "x=%.0f / 目標 %d" % (b.cx, target))
check("着地しても、光波は出ない", not g.waves and b.state == "recover", "%r" % [w.dir for w in g.waves])
snap(g, "boss landed")
# 高い光波と、しゃがみ
def high_wave_game():
    """ボスが高い光波を出した直後のゲーム（主人公は、ボスから離れた所に立っている）"""
    gg = boss_game()
    gg.player.px = float(C.ARENA_X0 + 150)
    boss_until(gg, lambda x: x.boss.state == "recover")
    gg.boss.shots = C.BOSS_PATTERN.index("H")
    boss_until(gg, lambda x: x.boss.state == "ready")
    gg.waves = []   # 前の光波は消しておく
    high_pose = gg.boss.image() in (gg.boss._opt("high") or [gg.boss._frames("swing")[0]])
    boss_until(gg, lambda x: x.waves)
    gg.player.invincible = 0
    return gg, high_pose


def wave_passes(gg, held=(), jump_at=None):
    """光波が、主人公を通り過ぎる（か、当たって消える）まで進める。ボスには当たらないようにしておく"""
    w = gg.waves[0]
    for _ in range(400):
        gg.boss.cx = gg.boss.x_max
        gg.boss.state, gg.boss.st = "recover", 0
        near = jump_at is not None and abs(w.px - gg.player.px) < jump_at and gg.player.on_ground
        gg.step(set(held), {"jump"} if near else set())
        if not w.alive or w.px < gg.player.px - 30:
            break


check("光波の順番に、高い・低いの両方がある", set(C.BOSS_PATTERN) == {"L", "H"})
g, high_pose = high_wave_game()
w = g.waves[0]
check("高い光波の構えは、低い光波の構えと絵が違う（刀を振り上げる）", high_pose)
check("高い光波は、しゃがんだ頭より上・立った頭より下から始まる（大きさは、絵と同じ）",
      w.tall and C.CROUCH_H <= C.FLOOR_Y - w.rect.bottom < C.PLAYER_H and w.rect.height == max(f.get_height() for f in g.a.wave[True]),
      "地面から %d〜%d" % (C.FLOOR_Y - w.rect.bottom, C.FLOOR_Y - w.rect.top))
snap(g, "boss high wave")
hp0 = g.player.hp
wave_passes(g)
check("高い光波は、立っていると当たる", g.player.hp == hp0 - C.WAVE["damage"], "HP %d → %d" % (hp0, g.player.hp))
res = {}
for d in range(10, 90, 4):
    g, _ = high_wave_game()
    wave_passes(g, jump_at=d)
    res[d] = g.player.hp == hp0
safe = [d for d, ok in res.items() if ok]
check("高い光波は、跳んでよけるのは難しい（よけられる間合いが、狭い）", len(safe) <= 3, "よけられた間合い %r" % safe)
g, _ = high_wave_game()
wave_passes(g, {"down"})
check("高い光波は、しゃがむと頭の上を通り過ぎる", g.player.hp == hp0 and g.player.crouch, "HP %d → %d" % (hp0, g.player.hp))
snap(g, "crouch")
check("しゃがんでいる間は、当たり判定が低い", g.player.rect.height == C.CROUCH_H and g.player.rect.bottom == round(g.player.py))
g.boss, g.waves = None, []   # ここからは、しゃがみの動きだけを見る
x0 = g.player.px
g.player.facing = 1
run(g, 20, {"down", "left"})
check("しゃがんでいる間は、歩けない（向きは変わる）", g.player.px == x0 and g.player.facing == -1, "%.1f → %.1f" % (x0, g.player.px))
check("コマの長さは、しゃがみと立ちで同じ", [d for _, d in C.CROUCH_SWORD_SEQ] == [d for _, d in C.SWORD_SEQ]
      and [d for _, d in C.CROUCH_THROW_SEQ] == [d for _, d in C.THROW_SEQ])
run(g, 1, {"down"}, {"attack"})
check("しゃがんだまま、刀を振れる", g.player.attack_t > 0 and g.player.crouch and g.player.rect.height == C.CROUCH_H
      and g.player.frame_index() == C.CROUCH_SWORD_SEQ[0][0])
low = None
for _ in range(30):
    run(g, 1)   # 下を離しても、振り終わるまでしゃがんだまま
    if g.player.sword_rect():
        low = g.player.sword_rect()
        snap(g, "crouch sword")
        break
check("しゃがみ斬りは、低い所を斬る（足元の光波に届き、高い光波には届かない）",
      low is not None and g.player.crouch and low.bottom >= C.FLOOR_Y and C.FLOOR_Y - low.top <= C.BOSS["high_bottom"],
      "地面から %d〜%d" % ((C.FLOOR_Y - low.bottom, C.FLOOR_Y - low.top) if low else (0, 0)))
run(g, 60)
check("振り終わって、下を離していれば、立つ", not g.player.crouch and not g.player.attack_t)
run(g, 2, {"down"})
run(g, 1, {"down"}, {"throw"})
for _ in range(30):
    run(g, 1, {"down"})
    if g.shurikens:
        break
check("しゃがんだまま、手裏剣を投げられる（低く飛ぶ）", g.player.crouch and g.shurikens and C.FLOOR_Y - g.shurikens[0].rect.centery < C.CROUCH_H,
      "高さ %d" % (C.FLOOR_Y - g.shurikens[0].rect.centery if g.shurikens else -1))
snap(g, "crouch throw")
run(g, 60)
run(g, 1, (), {"attack"})
run(g, 3, {"down"})
check("立って振り始めた刀は、下を押しても、立ったまま", g.player.attack_t > 0 and not g.player.crouch)
run(g, 60)
run(g, 1, {"down"}, {"jump"})
run(g, 3, {"down"})
check("しゃがみからでも跳べる（空中では、しゃがまない）", not g.player.on_ground and not g.player.crouch)
# 低い光波は、しゃがんでも当たる
g = boss_game()
g.player.px = float(C.ARENA_X0 + 150)
boss_until(g, lambda x: x.waves)
g.player.invincible = 0
wave_passes(g, {"down"})
check("低い光波は、しゃがんでも当たる（跳んでよける）", g.player.hp == hp0 - C.WAVE["damage"], "HP %d → %d" % (hp0, g.player.hp))
# 壁ぎわ
g = boss_game()
g.boss.cx = g.boss.x_max
for _ in range(200):
    g.player.invincible = 5
    g.boss.state, g.boss.st = "recover", 0
    g.step({"left"})
check("ボスと戦っている間は、左へ戻れない（画面も動かない）", g.player.px == C.ARENA_X0 + C.PLAYER_W / 2 and g.cam_x == C.ARENA_X0,
      "x=%.1f" % g.player.px)
g = boss_game()
g.player.px = float(C.ARENA_X0 + 20)
boss_until(g, lambda x: x.boss.state in ("ready", "crouch"))
check("主人公が壁ぎわにいると、最初から跳びかかりを選ぶ（下をくぐって逃げられる）", g.boss.state == "crouch" and g.boss.count == 1)
# 体力が半分になっても、光波は1発ずつ
g = boss_game()
b = g.boss
boss_until(g, lambda gg: gg.boss.state == "recover")
b.hp = b.max_hp // 2
check("体力が半分になると、怒る", b.rage)
boss_until(g, lambda gg: gg.boss.state == "swing")
n = 0
while b.state == "swing":
    g.player.invincible = 5
    before = len(b.spawned)
    b.think(g.player.rect, C.STAGE_W)
    n += len(b.spawned) - before
check("怒っても、光波は1発ずつ（歩く時間と隙が短くなるだけ）", n == 1 and C.BOSS["rage_recover_frames"] < C.BOSS["recover_frames"], "%d発" % n)
# やられたら、ボスの場所の入口から
g = boss_game()
g.lives = 2
kill(g)
run(g, C.RESPAWN_AT + 5)
check("ボスにやられると、ボスの場所の入口から再開する（ボスは、入り直すと出る）",
      g.player.px == C.ARENA_X0 + 100 and g.player.hp == C.PLAYER_HP and not g.boss_on and g.boss is None and not g.enemies,
      "x=%.0f" % g.player.px)
check("再開すると、スコアと団子の数が、ボスの場所に入ったときに戻る", g.score == 1500 and g.dango == 9, "%d / %d" % (g.score, g.dango))
run(g, 120, {"right"})
check("入り直すと、体力が満タンのボスが出る（出てくる場面は、短くなる）", g.boss_on and g.boss is not None and g.boss.hp == g.boss.max_hp
      and g.boss.intro["pose"] == C.BOSS_INTRO_QUICK["pose"] < C.BOSS_INTRO["pose"])
# 倒すとクリア
g = boss_game()
b = g.boss
boss_until(g, lambda gg: gg.boss.state == "recover")
b.hit(b.hp)
check("体力がなくなると、やられの動きになる（まだクリアではない）", b.dying and not g.cleared)
run(g, 1)
check("倒すと、すぐ寸劇が始まる（まだクリアではない。スコアが入り、曲が止まる）",
      g.ending and not g.end_ready and not g.cleared and g.boss is b and g.score == 1500 + C.SCORE_BOSS and g.bgm is None, "スコア %d" % g.score)
run(g, 12, {"left"}, {"jump"})
check("ボスは、弧を描いて吹っ飛ぶ", b.cy < b.floor - b.h / 2 - 20 and not b.down_t, "cy=%.0f" % b.cy)
snap(g, "ending blow")
t0 = g.frames
for _ in range(700):
    if g.end_ready:
        break
    g.step({"left"}, {"jump"})
check("ボスは決まった場所に倒れ、タヌキ侍は決まった場所まで歩いて、ボスのほうを向く（動かせない。時間も止まる）",
      g.end_ready and b.cx == C.END_BOSS_X and b.down_t and g.player.px == C.END_TANUKI_X and g.player.on_ground
      and g.player.facing == 1 and g.frames == t0, "ボス %.0f タヌキ %.0f" % (b.cx, g.player.px))
E = C.ENDING
run(g, E["wait"] + E["skip"] - 2, {"left"}, {"jump"})
check("話している間も、動かせない", g.player.px == C.END_TANUKI_X and g.frames == t0)
check("間のあと、ボスがひとこと言う（出てすぐは、キーで送れない）", g._end_phase()[0] == "boss", str(g._end_phase()))
snap(g, "ending boss")
run(g, 3)
n0 = g._end_phase()[1] // E["type"]
run(g, 1, (), {"attack"})
check("字は、1文字ずつ出る（出るたびに、音が鳴る）。途中でキーを押すと、全部出る（まだ送らない）",
      n0 < g.a.talk_boss.get_width() // C.TALK_CELL - 1 and C.SFX_TALK_LOW in g.sfx and g._end_phase()[0] == "boss"
      and g._end_phase()[1] >= (g.a.talk_boss.get_width() // C.TALK_CELL) * E["type"] - 1, str(g._end_phase()))
run(g, 1, (), {"attack"})
check("せりふは、キーで送れる（ボスが、光になって消えていく）", g._end_phase() == ("fade", 0) and g.boss is b and C.SFX_CHECKPOINT in g.sfx, str(g._end_phase()))
run(g, E["fade"] // 2)
snap(g, "ending fade")
run(g, E["fade"])
check("ボスが消えて、タヌキ侍が返す", g._end_phase()[0] == "reply" and g.boss is None, str(g._end_phase()))
snap(g, "ending reply")
at, wait = C.TALK_PAUSE["reply"]
t1 = at * E["type"] + wait - 1
check("タヌキ侍のせりふは、「・・・」のあと、間をおいてから続きが出る",
      g._talk_shown("reply", at * E["type"] - 1) == at == g._talk_shown("reply", t1) and g._talk_shown("reply", t1 + 1) == at + 1
      and g._talk_shown("reply", 999) == g._talk_cells("reply") == 5)
boss_until(g, lambda gg: gg._end_phase()[0] == "run", 300)
check("送らなくても、時間で進む（右へ走り出す）", g._end_phase()[0] == "run" and not g.cleared)
run(g, 20)
snap(g, "ending run")
ok = boss_until(g, lambda gg: gg.cleared, 400)
check("画面の右へ駆け抜けると、クリア（落ちない）", ok and g.player.px > C.STAGE_W and g.player.on_ground and g.player.hp > 0
      and g.score == 1500 + C.SCORE_BOSS and g.bgm is None, "x=%.0f" % g.player.px)
t0 = g.frames
run(g, 10, {"right"}, {"restart"})
check("クリアのあとは、動かない（時間も止まる。すぐには、Enterを受け付けない）", g.cleared and g.frames == t0)
run(g, C.CLEAR_WAIT)
snap(g, "clear")
_lives0 = g.lives
run(g, 1, (), {"restart"})
check("クリアのあと、Enterで、次の面へ進む（スコアは引き継ぎ、体力は満タン、団子・時間は数え直す）",
      not g.cleared and g.stage_i == 1 and g.stage.name == "毛越寺" and g.player.px == 60 and g.player.hp == C.PLAYER_HP
      and g.score == 1500 + C.SCORE_BOSS and g.dango == 0 and g.frames <= 1 and g.boss_state is None and g.cp_state is None
      and g.lives == _lives0 and not g.boss_on and len(g.enemies) > 0,
      "stage %d px %.0f hp %d score %d dango %d frames %d lives %d enemies %d" % (g.stage_i, g.player.px, g.player.hp, g.score, g.dango, g.frames, g.lives, len(g.enemies)))
check("次の面の地形に切り替わっている", g.terrain.ground == [tuple(x) for x in g.stage.ground] and g.stage.width != C.STAGE_W)
g.lives = 3
g.player.hp = 1
g.player.take_damage(g.player.px + 5, 1)
run(g, C.RESPAWN_AT + 5)
check("次の面で、やられても、その面の最初から再開する", g.stage_i == 1 and g.player.hp == C.PLAYER_HP and g.player.px == 60)
g.lives = 1
g.player.invincible = 0
g.player.hp = 1
g.player.take_damage(g.player.px + 5, 1)
run(g, C.GAMEOVER_WAIT + 5)
run(g, 1, (), {"restart"})
check("スタート画面が無ければ、ゲームオーバーのあと、最初の面から（残機は戻る）", g.stage_i == 0 and g.lives == C.LIVES and g.player.hp == C.PLAYER_HP and g.score == 0)
gt = Game(title=True)
gt.title = False
gt.lives, gt.player.hp = 1, 1
gt.player.take_damage(gt.player.px + 5, 1)
run(gt, C.GAMEOVER_WAIT + 5)
run(gt, 1, (), {"restart"})
check("スタート画面がある遊びでは、ゲームオーバーのあと、スタート画面へ戻る", gt.title and gt.lives == C.LIVES and gt.player.hp == C.PLAYER_HP)

# ---------------------------------------------------------------- 16. スタート画面
g = Game()
check("何も指定しなければ、スタート画面は出ない（すぐ遊べる）", not g.title)
g = Game(title=True)
x0 = g.player.px
run(g, 60, {"right"}, {"throw"})
check("スタート画面の間は、止まっている（曲も鳴らさない）", g.title and g.player.px == x0 and g.frames == 0 and g.bgm is None and not g.shurikens)
snap(g, "title")
g.sfx.clear()
run(g, C.TITLE_THUNDER[0] - 60)
check("放っておくと、稲光が走る", g.flash_t == C.TITLE_FLASH and not g.sfx, "光 %d" % g.flash_t)
run(g, 3)
snap(g, "title flash")
run(g, C.THUNDER_DELAY - 3)
check("少し遅れて、雷鳴が鳴る", g.sfx == [C.SFX_THUNDER], "%r" % g.sfx)
g.sfx.clear()
run(g, C.TITLE_THUNDER[1] - C.THUNDER_DELAY - 1)
check("雷は、間をおいて、くり返す", g.sfx == [] and g.flash_t == 0)
run(g, 1 + C.THUNDER_DELAY)
check("2回目の雷鳴", g.sfx == [C.SFX_THUNDER] and g.thunder_n == 2)
g.sfx.clear()
run(g, 1, (), {"restart"})
check("Enterで、メニューが開く（まだ始まらない。決める音が鳴る）",
      g.menu_on and g.menu_page == "main" and g.menu_i == 0 and g.title and not g.start_t and g.sfx == [C.SFX["decide"]])
check("メニューは、STORY / OPTION / DISCOGRAPHY / HOW TO PLAY", C.MENU["pages"]["main"] == ("story", "option", "disco", "howto"))
snap(g, "title menu")


def tap(held=(), pressed=()):
    """1回だけ押して、離す"""
    run(g, 1, held, pressed)
    run(g, 1, ())


def cur():
    return C.MENU["pages"][g.menu_page][g.menu_i]


g.sfx.clear()
tap({"down"})
check("下で、次の項目（OPTION）へ移る。選ぶ音が鳴る", cur() == "option" and g.sfx == [C.SFX["cursor"]])
g.sfx.clear()
tap({"up"}, {"jump"})
check("上キー（ジャンプと同じキー）は、決定にならない。上の項目（STORY）へ戻って、選ぶ音が鳴る",
      cur() == "story" and not g.start_t and g.sfx == [C.SFX["cursor"]])
tap({"up"}, {"jump"})
check("いちばん上で、上を押すと、いちばん下（HOW TO PLAY）へ回る", cur() == "howto")
tap((), {"restart"})
check("HOW TO PLAY で決定すると、操作説明が出る（絵がある）", g.howto and g.a.howto is not None and g.title and not g.start_t)
snap(g, "howto")
tap({"down"})
check("操作説明の間は、項目は動かない", g.howto and cur() == "howto")
tap((), {"attack"})
check("もう一度決定すると、メニューに戻る（始まらない）", not g.howto and g.menu_on and not g.start_t and cur() == "howto")
tap({"up"})
tap({"up"})
tap((), {"restart"})
check("OPTION で決定すると、設定の画面へ移る（LEVEL / MUSIC / SOUND / BACK）",
      g.menu_page == "option" and cur() == "level" and C.MENU["pages"]["option"] == ("level", "music", "sound", "back"))
snap(g, "title option")
tap({"right"})
check("LEVEL で右を押すと、難しさが上がる（残機も、その難しさの数になる）", g.level == "hard" and g.lives == C.LEVELS["hard"]["lives"])
tap({"right"})
check("右の端では、止まる", g.level == "hard")
tap({"left"})
check("左で、戻る", g.level == "normal")
tap((), {"restart"})
tap((), {"restart"})
check("LEVEL は、決定でも送れる（端まで行ったら、最初へ回る）", g.level == "easy" and g.menu_page == "option")
tap((), {"restart"})
check("もう一度で、もとの難しさ", g.level == "normal")
tap({"down"})
tap({"left"})
check("MUSIC で左を押すと、曲の音量が1段下がる（効果音は、そのまま）", g.vol_bgm == C.MENU["steps"] - 1 and g.vol_sfx == C.MENU["steps"])
tap({"right"})
tap({"right"})
check("音量は、いちばん上の段より、上がらない", g.vol_bgm == C.MENU["steps"])
tap({"down"})
for _ in range(C.MENU["steps"] + 2):
    tap({"left"})
check("SOUND で左を押し続けると、効果音が消える（0 より下がらない）", g.vol_sfx == 0 and g.vol_bgm == C.MENU["steps"])
snap(g, "title menu sound")
g.vol_sfx = C.MENU["steps"]
tap({"down"})
tap((), {"restart"})
check("BACK で決定すると、最初のメニューへ戻る（OPTION を選んだまま。始まらない）", g.menu_page == "main" and cur() == "option" and not g.start_t)
tap({"down"})
tap((), {"restart"})
check("DISCOGRAPHY で決定すると、曲の一覧が出る（曲＋BACK）", g.menu_page == "disco" and cur() == "t0" and len(C.MENU["pages"]["disco"]) == len(C.DISCO) + 1)
tap({"down"})
tap((), {"restart"})
check("曲で決定すると、その曲が鳴る", g.bgm == C.DISCO[1][0])
snap(g, "disco")
tap((), {"restart"})
check("もう一度決定すると、止まる", g.bgm is None)
tap({"up"})
tap({"up"})
tap((), {"restart"})
check("DISCOGRAPHY の BACK で、最初のメニューへ戻る（曲は止まる）", g.menu_page == "main" and cur() == "disco" and g.bgm is None and g.disco_song is None)
tap({"up"})
tap({"up"})
g.sfx.clear()
run(g, 1, (), {"restart"})
check("STORY で決定すると、刀の音が鳴る（すぐには始まらず、少し間がある）", g.sfx == [C.SFX_SWORD] and g.title and g.start_t == C.TITLE_START)
run(g, 5, (), {"restart"})
check("間のあいだに押しても、刀の音は1回だけ", g.sfx == [C.SFX_SWORD])
run(g, C.TITLE_START)
check("間のあと、始まりの語りが流れる（語りの曲があれば鳴る。無ければ無音）", not g.title and g.story and g.bgm == (C.BGM_STORY if g.story_bgm else None))
run(g, 120, {"right"})
snap(g, "story")
check("語りの間は、ゲームは止まっている", g.story and g.player.px == x0 and g.frames == 0)
T_ = C.STORY_TANUKI
check("語りの始めは、タヌキ侍は立って起きている", not g.story_asleep)
run(g, T_["sleep_at"] - T_["sit"] - T_["drowsy"] - 30 - g.story_t)
snap(g, "story yawn")
run(g, T_["sleep_at"] - g.story_t)
check("しばらくすると、座って眠ってしまう", g.story_asleep and not g.story_dreaming, "語り %d" % g.story_t)
run(g, 70)
snap(g, "story sleep")
run(g, T_["dream_at"] - g.story_t + 40)
check("眠ったあと、おにぎりの夢を見る", g.story_dreaming)
snap(g, "story dream")
total = int((C.STORY_WINDOW + g.a.story.get_height()) / C.STORY_SPEED) + 2
run(g, max(0, total - g.story_t) + 120)
check("文章が流れきっても、ゲームは始まらない（文章は、くり返さない。%d秒で流れきる）" % (total // C.FPS),
      g.story and g.story_run == 0 and g.frames == 0 and C.STORY_WINDOW - g.story_t * C.STORY_SPEED < -g.a.story.get_height())
run(g, 1, (), {"restart"})
check("Enterで、タヌキ侍が気づく（眠っていたので、飛び起きる。まだ走らない）", g.story and g.story_run > 0 and g.story_woke and not g.story_asleep
      and g.story_wake == T_["wake"])
x1 = g.story_x
run(g, T_["wake"] // 2)
snap(g, "story wake")
check("飛び起きる間は、その場にいる", g.story_x == x1)
run(g, T_["wake"] // 2 + 12)
snap(g, "story run")
check("起きたら、右へ素早く駆けていく", g.story and g.story_x > x1 + 60, "%.0f → %.0f" % (x1, g.story_x))
for _ in range(400):
    if not g.story:
        break
    run(g, 1)
check("画面の右へ駆け抜けると、地図が出る（歩かず、1面の場所に立つ）", not g.story and not g.title and g.map_on and g.map_len == 0
      and g.map_to == g.stage.number and g.bgm != C.BGM_STAGE1)
run(g, 5, (), {"restart"})
check("地図は、出してすぐはキーを受け付けない", g.map_on)
run(g, 30, {"right"})
check("地図の間は、ゲームは進まない（動かない・時間も数えない）", g.map_on and g.player.px == x0 and g.frames == 0)
run(g, C.MAP_SKIP_WAIT)
run(g, 1, (), {"restart"})
check("Enterで地図を飛ばすと、ゲームが始まる", not g.map_on and not g.title and g.bgm == C.BGM_STAGE1)
run(g, 30, {"right"})
check("始まると、動かせる", g.player.px > x0)
g = Game(title=True)
run(g, 1, (), {"attack"})
run(g, 1, (), {"attack"})
run(g, C.TITLE_START)
check("刀のキーでも、メニューを開いて、語りへ進める", not g.title and g.story)
run(g, 5, (), {"restart"})
check("語りは、始まってすぐはキーを受け付けない", g.story and g.story_run == 0)
run(g, C.STORY_SKIP_WAIT)
run(g, 1, (), {"attack"})
check("起きているときに押すと、すぐ気づいて走り出す（飛び起きない）", g.story_run > 0 and not g.story_woke and g.story_wake == T_["notice"] < T_["wake"])
run(g, 150)
check("語りからも、刀のキーで始められる", not g.story and not g.title)
while g.map_on:
    run(g, 1, (), {"restart"} if g.map_t >= C.MAP_SKIP_WAIT else ())
g.player.px, g.player.py = float(C.ARENA_X0 + C.BASE_W // 2 - 1), float(C.FLOOR_Y)
run(g, 30, {"right"})
boss_until(g, lambda gg: gg.boss.state == "recover")
g.boss.hit(g.boss.hp)
boss_until(g, lambda gg: gg.cleared, 1500)
run(g, C.CLEAR_WAIT)
_saved = list(STAGES)
STAGES[:] = [STAGES[0]]   # 最後の面をクリアしたときの動き（1面だけの設定にする）
run(g, 1, (), {"restart"})
STAGES[:] = _saved
check("最後の面のクリアのあと、Enterで、姫を助ける場面（THANK YOU TANUKI!）が出る", g.thanks and not g.ending_screen and not g.title)
run(g, g._thanks_at("arrive") - 4)
snap(g, "thanks walk")
check("タヌキ侍が歩いてくる間は、まだ文は出ない", g._thanks_shown() == 0 and g.thanks)
run(g, g._thanks_at("type") - g.thanks_t + 3 * C.THANKS["type"])
check("姫が喜んだあと、礼の文が、1文字ずつ出る", 0 < g._thanks_shown() < len(C.THANKS["lines"][0]))
run(g, 1, (), {"restart"})
check("途中で押すと、文が全部出る（まだ、先へは進まない）", g.thanks and g._thanks_shown() == sum(len(x) for x in C.THANKS["lines"]))
run(g, C.THANKS["wait"] + 1)
snap(g, "thanks")
run(g, 1, (), {"restart"})
RL = C.ROLL
check("もう一度押すと、エンドロールが始まる（エンディングの絵は、まだ）", g.roll and not g.thanks and not g.ending_screen and g.roll_state == "walk")
check("エンドロールの文字の絵がある", g.a.credits is not None)
run(g, 5, (), {"restart"})
check("エンドロールは、始まってすぐは、飛ばせない", g.roll)
x_r = g.roll_x
run(g, 30)
check("二人は、右へ歩いていく（景色が流れる）", g.roll_x > x_r and g.roll_state == "walk" and g.roll_side == 0)
snap(g, "roll walk")
run_until(g, lambda q: q.roll_state == "stop", (), 2000)
x_stop = g.roll_x
check("横断歩道に来ると、止まる", g.roll_state == "stop" and g.roll_car is None)
run(g, RL["car_wait"] + 12)
check("止まっている間に、車が来る（二人は、動かない）", g.roll_car is not None and g.roll_x == x_stop and g.roll_state == "stop")
snap(g, "roll car")
run_until(g, lambda q: q.roll_state == "look", (), 600)
check("車が通りすぎてから、右・左を見る（まだ渡らない）", g.roll_car is None and g.roll_x == x_stop)
run(g, RL["look"] + 3)
snap(g, "roll look")
run_until(g, lambda q: q.roll_state == "cross", (), 600)
check("3回見てから、渡りはじめる", g.roll_st <= 1 and g.roll_x == x_stop)
run(g, RL["cross"] // 2)
check("渡っている間は、車が来ない", g.roll_car is None and g.roll_state == "cross")
snap(g, "roll cross")
run_until(g, lambda q: q.roll_state == "walk", (), 600)
check("渡りきると、向こうの歩道を、また歩く", g.roll_side == 1 and g.roll_n == 1)
run_until(g, lambda q: q.roll_n == 2 and q.roll_state == "walk", (), 3000)
check("次の横断歩道で、もとの歩道へ渡る（くり返す）。車は、1回ごとに、反対から来る", g.roll_side == 0)
n_cross = 0
for _ in range(20000):
    g.step(set())
    if not g.roll:
        break
check("文字が流れきると、エンディングの絵に替わる（渡っている途中では、替わらない）",
      not g.roll and g.ending_screen and g.roll_state == "walk" and g._roll_done(), "渡った回数 %d" % g.roll_n)
gr = Game(title=True)
gr.title = False
gr._start_roll()
run(gr, RL["skip"] + 1)
run(gr, 1, (), {"restart"})
check("エンドロールは、決定のキーで飛ばせる（エンディングの絵へ）", not gr.roll and gr.ending_screen and gr.a.ending_image is not None)
run(g, 5, (), {"restart"})
check("エンディングは、しばらくはEnterを受け付けない", g.ending_screen)
snap(g, "ending screen")
run(g, C.ENDING_SCREEN["wait"])
run(g, 1, (), {"restart"})
check("エンディングのあと、Enterで、スタート画面へ戻る（雷も、最初から数え直す）", g.title and not g.story and not g.cleared and not g.ending_screen
      and g.player.px == 60 and g.score == 0 and g.title_t == 0 and g.thunder_n == 0)

# ---------------------------------------------------------------- 17. 回復・落とし物・強化3種類・中間地点の演出
class FixedRng:
    """くじを、決まった値にする"""
    def __init__(self, v):
        self.v = v

    def random(self):
        return self.v


C.DROPS = DROPS
total = sum(c for _, c in DROPS)
check("落とし物は、おにぎり・強化2種類・団子（スーパータヌキは出ない）。何も落とさないことのほうが多い", {k for k, _ in DROPS} == {"onigiri", "leaf", "triple", "dango"} and total < 0.5,
      "落とす確率 %.2f" % total)
check("くじの値で、落とす物が決まる", drop_kind(0.0) == DROPS[0][0] and drop_kind(total - 0.001) == DROPS[-1][0] and drop_kind(total + 0.001) is None
      and drop_kind(0.999) is None)
check("おにぎりの回復は2。面には5個置いてある", C.HEAL_ONIGIRI == 2 and sum(1 for k, _, _ in ITEMS if k == "onigiri") == 5)


def roll_for(kind):
    acc = 0.0
    for k, c in DROPS:
        if k == kind:
            return acc + c / 2
        acc += c
    return 0.999


def drops(gg):
    return [it for it in gg.items if it.drop]


def kill_enemy(gg):
    e = gg.enemies[0]
    e.hit(99)
    run(gg, 1)
    return e


# 落とす・落ちる・消える
g = fresh([Karasu(360)], px=100)
g.rng = FixedRng(0.999)
kill_enemy(g)
check("くじが外れなら、何も落とさない", not drops(g))
g = fresh([Karasu(360)], px=100)
g.rng = FixedRng(roll_for("leaf"))
e = kill_enemy(g)
it = drops(g)[0] if drops(g) else None
check("倒した敵が、物を落とす（空中の敵なら、その場所に出る）", it is not None and it.kind == "leaf" and it.drop and abs(it.cx - e.rect.centerx) < 2
      and it.cy < C.FLOOR_Y - 60, "高さ %d" % (C.FLOOR_Y - it.cy if it else -1))
run(g, 4)
snap(g, "drop")
run(g, 120)
check("落とし物は、地面まで落ちて止まる（1つだけ）", len(drops(g)) == 1 and it.resting and 0 < C.FLOOR_Y - it.rect.bottom <= 4, "下端 %d" % (C.FLOOR_Y - it.rect.bottom))
run(g, C.DROP_LIFE)
check("落とし物は、しばらくすると消える", not drops(g))
g = fresh([Ochimusha(130)], px=100)
g.rng = FixedRng(roll_for("onigiri"))
g.player.hp = 3
kill_enemy(g)
run(g, 40)
run(g, 40, {"right"})
check("落としたおにぎりを拾うと、体力が2回復する", g.player.hp == 5 and not drops(g), "HP %d" % g.player.hp)
g = boss_game()
g.rng = FixedRng(0.0)
boss_until(g, lambda gg: gg.boss.state == "recover")
g.boss.hit(g.boss.hp)
boss_until(g, lambda gg: gg.cleared, 1500)
check("ボスは、物を落とさない", not any(it.drop for it in g.items))
C.DROPS = ()

# 三方手裏剣
g = fresh(px=100)
g.items = [Item("triple", 100, C.FLOOR_Y - 14, g.a)]
run(g, 2)
check("三方手裏剣を拾う", g.player.triple)
run(g, 1, (), {"throw"})
run_until(g, lambda gg: gg.shurikens, (), 40)
vys = sorted(s_.vy for s_ in g.shurikens)
check("手裏剣が、3方向に出る（前・斜め上・斜め下）", len(vys) == 3 and vys[0] < 0 and vys[1] == 0 and vys[2] > 0, "%r" % vys)
run(g, 12)
snap(g, "triple")
ys = sorted(s_.py for s_ in g.shurikens)
check("3つの手裏剣は、上下に広がっていく", len(ys) == 3 and ys[2] - ys[0] > 30, "%r" % [round(y) for y in ys])
gt = fresh([Ochimusha(130)], px=100)
gt.player.triple = True
et = gt.enemies[0]
run(gt, 1, (), {"throw"})
for _ in range(40):
    et.cx, et.stun = 130.0, 5      # 目の前に立たせておく（3つとも、当たる近さ）
    gt.player.invincible = 5
    gt.step(set())
check("三方手裏剣が3つとも当たっても、1投げで減る体力は1つぶんだけ（残りは、消える）",
      et.hp == et.max_hp - C.SHURIKEN_DAMAGE and not gt.shurikens, "体力 %d/%d 残り %d" % (et.hp, et.max_hp, len(gt.shurikens)))
run(gt, 1, (), {"throw"})
for _ in range(40):
    et.cx, et.stun = 130.0, 5
    gt.player.invincible = 5
    gt.step(set())
check("次の1投げは、また当たる", et.hp == et.max_hp - 2 * C.SHURIKEN_DAMAGE, "体力 %d" % et.hp)
g.items = [Item("leaf", g.player.px, C.FLOOR_Y - 14, g.a)]
run(g, 40)
check("金の葉と三方手裏剣は、同時に持てる", g.player.power and g.player.triple)
snap(g, "two powers")
g.player.take_damage(g.player.px + 5)
check("ダメージを受けると、金の葉も三方手裏剣も消える", not g.player.power and not g.player.triple)
run(g, 60)
run(g, 1, (), {"throw"})
run_until(g, lambda gg: gg.shurikens, (), 40)
check("消えたあとは、手裏剣は1つ", len(g.shurikens) == 1)

# スーパータヌキ
g = fresh(px=100)
run(g, 60, {"right"})
v_normal = g.player.vx
g = fresh([Ochimusha(260)], px=100)
g.items = [Item("super", 100, C.FLOOR_Y - 14, g.a)]
run(g, 2)
check("スーパータヌキを拾う（8秒）", g.player.super_t >= C.SUPER_FRAMES - 2 and g.player.untouchable)
run(g, 60, {"right"})
snap(g, "super")
check("スーパータヌキの間は、速い", g.player.vx > v_normal * 1.3, "%.2f / ふつう %.2f" % (g.player.vx, v_normal))
hp0 = g.player.hp
g.player.px = g.enemies[0].cx
g.waves = [Wave(g.player.px + 6, C.FLOOR_Y - 18, -1, g.a)]
run(g, 20)
check("スーパータヌキの間は、敵や光波に当たっても、ダメージを受けない", g.player.hp == hp0 and not g.player.hurt_t)
check("スーパータヌキで触れたザコ敵は、倒れる", not any(e.active for e in g.enemies))
gb = boss_game()
boss_until(gb, lambda x: x.boss.state == "recover")
gb.player.super_t = 100
gb.player.px = gb.boss.cx
hp_b = gb.boss.hp
gb.step(set())
check("スーパータヌキでも、ボスは触れただけでは倒せない（ダメージも受けない）", gb.boss.hp == hp_b and not gb.player.hurt_t)
check("スーパータヌキの曲は、ファイルがあるときだけ鳴らす（無ければ、面の曲のまま）",
      g.bgm == (C.BGM_SUPER if g.super_bgm else C.BGM_STAGE1) and gb.bgm == C.BGM_BOSS, str(g.bgm))
g.enemies, g.waves = [], []
run(g, C.SUPER_FRAMES)
check("スーパータヌキは、時間で切れる（速さも戻る）", g.player.super_t == 0 and not g.player.untouchable)
x0 = g.player.px
run(g, 80, {"left"})
check("切れたあとは、ふつうの速さ", abs(abs(g.player.vx) - v_normal) < 0.01, "%.2f" % g.player.vx)
g = fresh(px=100)
g.player.super_t = 200
g.player.px, g.player.py = 740.0, float(C.FLOOR_Y)    # 古い地形の穴（700〜780）の上
g.player.on_ground = False
hp0 = g.player.hp
run(g, 120)
check("スーパータヌキでも、穴に落ちるとダメージを受ける", g.player.hp == hp0 - C.FALL_DAMAGE, "HP %d → %d" % (hp0, g.player.hp))

# 中間地点の演出
g = Game()
g.enemies = []
g.sfx.clear()
g.player.px, g.player.py = float(CHECKPOINT[0] - 30), float(CHECKPOINT[1])
run(g, 30, {"right"})
check("中間地点を通ると、演出が始まり、音が鳴る（1回だけ）", g.checkpoint.active and g.checkpoint.fx_t > 0 and g.sfx.count(C.SFX_CHECKPOINT) == 1,
      "残り %d / 音 %r" % (g.checkpoint.fx_t, g.sfx))
run_until(g, lambda gg: gg.checkpoint.fx_t <= C.CHECKPOINT_FX - 22, (), 60)
snap(g, "checkpoint")
run(g, C.CHECKPOINT_FX)
check("演出は、しばらくすると終わる（鳥居は、灯ったまま）", g.checkpoint.fx_t == 0 and g.checkpoint.active and g.sfx.count(C.SFX_CHECKPOINT) == 1)

# ---------------------------------------------------------------- 18. 放っておくと、眠る
R_ = C.REST
g = fresh(px=200)
run(g, R_["start"] - 2)
check("しばらく何もしないでいても、すぐには眠らない", g.player.rest_frame() is None and not g.player.asleep)
run(g, 30)
check("何もしないで立っていると、あくびをする", g.player.rest_frame() == 1, "%r" % g.player.rest_frame())
snap(g, "rest yawn")
run(g, R_["yawn"] + R_["drowsy"] + R_["sit"])
check("そのまま、座って眠る", g.player.asleep and g.player.rest_frame() in C.STORY_SLEEP_SEQ)
run(g, 100)
snap(g, "rest sleep")
check("眠っていても、当たり判定は立っているときと同じ", g.player.rect.height == C.PLAYER_H)
run(g, 1, {"right"})
check("キーを押すと、すぐ起きる", g.player.rest_frame() is None and not g.player.asleep)
run(g, 30, {"right"})
check("起きたら、ふつうに動ける", g.player.px > 210)
g = fresh(px=200)
run(g, R_["start"] + 300)
run(g, 1, (), {"attack"})
check("眠っていても、刀のキーで起きて、すぐ斬る", g.player.attack_t > 0 and g.player.rest_frame() is None)
g = fresh(px=200)
run(g, R_["start"] + 300)
hp0 = g.player.hp
g.player.take_damage(g.player.px + 5)
run(g, 1)
check("眠っている間にダメージを受けると、起きる", g.player.hp == hp0 - 1 and g.player.rest_frame() is None)
g = fresh(px=200)
run(g, R_["start"] + 300, {"down"})
check("しゃがんでいる間は、眠らない", g.player.rest_frame() is None and g.player.crouch)

# ---------------------------------------------------------------- 19. 刀の軌跡（届く距離）
def swing_at(gap):
    """体の端から gap だけ離れた所に落ち武者を置いて、刀を振る。当たったか"""
    gg = fresh(px=200)
    e = Ochimusha(200 + C.PLAYER_W / 2 + gap + C.OCHI["w"] / 2)
    e.stun = 999      # 動かないようにしておく
    e.hp = e.max_hp = 9      # 1振りで倒れないようにする（当たったかを、体力の減りで見る）
    gg.enemies = [e]
    gg.player.invincible = 999
    hp = e.hp
    run(gg, 1, (), {"attack"})
    for _ in range(40):
        e.stun = 999
        run(gg, 1)
    return e.hp < hp


check("刀は、軌跡のぶんだけ遠くまで届く（刀の長さ %d + 軌跡 %d）" % (C.SWORD_W, C.SWORD_TRAIL),
      swing_at(C.SWORD_W + C.SWORD_TRAIL - 2) and swing_at(C.SWORD_W + 2))
check("軌跡の先までは、届かない（光波のようには飛ばない）", not swing_at(C.SWORD_W + C.SWORD_TRAIL + 3))

_STAGES = PROD_STAGES     # 本番の4面で調べる（このテストの大半は、昔の2面で動かしている）
over = [(st.name, pf) for st in _STAGES for pf in st.platforms
        if pf[0] - 34 < st.checkpoint[0] < pf[1] + 34 and st.checkpoint[1] - 110 < pf[2] < st.checkpoint[1]]
check("どの面でも、中間地点（鳥居）の真上に、足場が重ならない", not over, str(over))

# ---------------------------------------------------------------- 弓兵
from sprites import Archer, Arrow  # noqa: E402

Y = C.YUMI
g = fresh([Archer(460)], px=300)
ar = g.enemies[0]
x_a = ar.cx
run(g, Y["first_wait"] + 3)
check("弓兵は、近づくと、弓を引く（その場から動かない。主人公のほうを向く）", ar.draw_t > 0 and ar.cx == x_a and ar.facing == -1)
snap(g, "archer draw")
n = 0
while not g.waves and n < Y["draw_frames"] + 5:
    g.step(set())
    n += 1
check("弓を引ききると、矢を撃つ（予告の長さ）", g.waves and isinstance(g.waves[0], Arrow) and n >= Y["draw_frames"] - 5, "%d フレーム" % n)
aw = g.waves[0]
check("矢は、主人公へ向かって飛ぶ", aw.vx < 0 and abs(aw.vy) < 1.0, "vx=%.2f vy=%.2f" % (aw.vx, aw.vy))
hp0 = g.player.hp
run_until(g, lambda gg: gg.player.hp < hp0, (), 120)
check("矢に当たると、ダメージを受ける（矢は消える）", g.player.hp == hp0 - C.ARROW["damage"] and not g.waves)
check("撃ったあとは、しばらく撃たない（隙）", ar.cool > Y["cooldown"] // 3 and not ar.draw_t)
g = fresh([Archer(460)], px=300)
run_until(g, lambda gg: gg.waves, (), 200)
aw = g.waves[0]
run_until(g, lambda gg: abs(aw.px - gg.player.px) < 46, (), 120)
hp0 = g.player.hp
run(g, 1, {"right"}, {"attack"})
run(g, 14, {"right"})
check("矢は、刀で斬ると消せる（ダメージを受けない。折れた矢が落ちる）", not aw.alive and g.player.hp == hp0)
g = fresh([Archer(460)], px=300)
run_until(g, lambda gg: gg.waves, (), 200)
aw = g.waves[0]
g.player.invincible = 200
run(g, 1, {"right"}, {"throw"})
run(g, 16, {"right"})
check("矢は、手裏剣では消せない（すり抜ける）", aw.alive or g.player.invincible)
g = fresh([Archer(460)], px=300)
ar = g.enemies[0]
ar.hit(C.SHURIKEN_DAMAGE)
alive1 = ar.active
ar.hit(C.SHURIKEN_DAMAGE)
check("弓兵は、手裏剣2発（刀なら1回）で倒れる", alive1 and ar.dying and Y["hp"] <= C.SWORD_DAMAGE)
g = fresh([Archer(460)], px=300)
g.player.py = C.FLOOR_Y - 200.0     # ずっと高い所にいる
g.player.on_ground = False
aimed = Arrow(460, C.FLOOR_Y - 27, 300, C.FLOOR_Y - 400, -1, g.a)
check("矢は、真上・真下へは飛ばない（ねらえる角度に、限りがある）",
      abs(math.degrees(math.atan2(aimed.vy, abs(aimed.vx)))) <= Y["max_angle"] + 0.5)
check("高館に、弓兵がいる（落ち武者も、残っている）",
      sum(k == "yumihei" for k, _ in PROD_STAGES[1].spawns) >= 3 and any(k == "ochimusha" for k, _ in PROD_STAGES[1].spawns))
tr = PROD_STAGES[1].terrain()
check("弓兵の配置が、すべて地面の上", all(tr.height_at(x) is not None for k, x in PROD_STAGES[1].spawns if k == "yumihei"))

# ---------------------------------------------------------------- 本番の4面: すべての足場に、ジャンプで届くか
# ジャンプの軌道（横の速さを5通り）を、実際の重力と初速で計算して、面から面へ、乗り移れるかを調べる
def _jump_arcs():
    out = []
    for vx in (0.0, 0.7, 1.4, 2.1, C.MAX_SPEED):
        x = y = 0.0
        vy = C.JUMP_SPEED
        pts = []
        while y < 300:
            vy = min(vy + C.GRAVITY * (C.FALL_GRAVITY if vy > 0 else 1.0), C.MAX_FALL)
            y += vy
            x += vx
            pts.append((x, -y, vy >= 0))
        out.append(pts)
    return out


_ARCS = _jump_arcs()


def _can_jump(s1, s2):
    (a1, b1, t1), (a2, b2, t2) = s1, s2
    rise = t1 - t2
    for pts in _ARCS:
        for sign in (1, -1):
            for x0 in range(a1, b1 + 1, 4):
                prev = None
                for dx, h, down in pts:
                    if down and prev is not None and prev >= rise >= h and a2 - 6 <= x0 + sign * dx <= b2 + 6:
                        return True
                    prev = h
    return False


# 天狗: かがんでから跳び、プレイヤーの方へ近づく。穴の手前では跳ばない
from sprites import Tengu  # noqa: E402
_e = Tengu(600, None, C.FLOOR_Y)
_pr = pygame.Rect(400, 0, 20, 40)
_air = _crouch = False
for _ in range(200):
    _e.update(_pr, 5000, None)
    _crouch = _crouch or bool(_e.crouch_t)
    _air = _air or _e.air
check("天狗は、かがんでから、跳んで、プレイヤーへ近づく", _crouch and _air and _e.cx < 600 and _e.cy <= C.FLOOR_Y - _e.h / 2 + 0.01)
_e = Tengu(600, None, C.FLOOR_Y)
_pr = pygame.Rect(540 - 8, C.FLOOR_Y - C.PLAYER_H, C.PLAYER_W, C.PLAYER_H)
_touch, _seen_air = 0, False
for _ in range(200):
    _e.update(_pr, 5000, None)
    _touch += _e.rect.colliderect(_pr)
    _seen_air = _seen_air or _e.air
    if _seen_air and not _e.air:      # 最初の着地
        break
check("天狗は、主人公を飛び越えて、うしろに降りる（跳んでいる間は、当たらない。下をくぐれる）", _e.cx < _pr.centerx - 20 and _touch == 0, "x=%.0f 当たり %d" % (_e.cx, _touch))
_e = Tengu(600, None, C.FLOOR_Y)
_t2 = type("T2", (), {"height_at": staticmethod(lambda x: C.FLOOR_Y if (x > 520 or x < 430) else None)})
_pr = pygame.Rect(380, C.FLOOR_Y - C.PLAYER_H, C.PLAYER_W, C.PLAYER_H)
for _ in range(400):
    _e.update(_pr, 5000, _t2)
check("天狗は、穴を越えて、向こう岸の主人公に近づく", _e.cx < 430, "x=%.0f" % _e.cx)
_e = Tengu(600, None, C.FLOOR_Y)
_t = type("T", (), {"height_at": staticmethod(lambda x: C.FLOOR_Y if x > 560 else None)})
for _ in range(200):
    _e.update(_pr, 5000, _t)
check("天狗は、穴には、降りない（地面の端までしか、跳ばない）", _e.cx > 560 and _e.cy <= C.FLOOR_Y - _e.h / 2 + 0.01)


_GROUNDED = ("ochimusha", "miira", "yumihei", "tachiojo", "tengu")
bad = [(st.name, k, x) for st in PROD_STAGES for k, x in st.spawns if k in _GROUNDED
       and len({st.terrain().height_at(x + d) for d in (-16, 0, 16)} - {None}) != 1 or
       k in _GROUNDED and None in [st.terrain().height_at(x + d) for d in (-16, 0, 16)]]
check("[本番] 地上の敵は、穴の上や、段差の境目に置かない（足元の左右16ドットが、同じ高さの地面）", not bad, str(bad))
check("ジャンプの頂点は、70〜74（足場の高さを決める、もとの数字）", 70 <= max(h for pts in _ARCS for _, h, _ in pts) <= 74,
      "%.1f" % max(h for pts in _ARCS for _, h, _ in pts))
for st in PROD_STAGES:
    surf = list(st.ground) + list(st.footholds)
    ng = len(st.ground)
    reach, frontier = {0}, [0]
    while frontier:
        i = frontier.pop()
        for j, s2 in enumerate(surf):
            if j in reach:
                continue
            s1 = surf[i]
            walk = j < ng and i < ng and max(s2[0] - s1[1], s1[0] - s2[1], 0) == 0 and s1[2] <= s2[2]   # 隣の、同じか低い地面へは、歩ける
            if walk or _can_jump(s1, s2):
                reach.add(j)
                frontier.append(j)
    lost = [(surf[j][0], surf[j][1], C.FLOOR_Y - surf[j][2]) for j in range(len(surf)) if j not in reach]
    check("[本番 %s] すべての地面と足場に、ジャンプで届く（軌道を計算して調べる）" % st.name, not lost, "届かない: %s" % lost)

# ---------------------------------------------------------------- 秀衡の連続光波・光波の高さ
from sprites import Boss3  # noqa: E402

b3 = Boss3(600, None, C.FLOOR_Y, 300, 780)
b3.state, b3.st, b3.count = "walk", C.BOSS3["walk_frames"], 0
pr = pygame.Rect(400, C.FLOOR_Y - 36, 16, 36)
got, states = 0, []
for _ in range(400):
    b3.think(pr, 2000)
    got += len(b3.spawned)
    b3.spawned.clear()
    states.append(b3.state)
    if b3.state == "recover":
        break
check("秀衡は、光波を続けて2発撃ってから、隙になる（1面の泰衡は、1発ずつ）", got == C.BOSS3["combo"] == 2 and C.BOSS.get("combo", 1) == 1, "%d 発" % got)
check("2発目の前にも、構え（予告）がある", states.count("ready") >= C.BOSS3["ready_frames"] + C.BOSS3["combo_ready"] - 2)
wv = Wave(100, C.FLOOR_Y + C.WAVE["dy"], 1, None)
check("低い光波は、地面にめり込まない（絵の下端が、地面の高さ。しゃがんでも当たり、跳べば越えられる）",
      C.FLOOR_Y + C.WAVE["dy"] + 31 // 2 <= C.FLOOR_Y and wv.rect.bottom > C.FLOOR_Y - C.CROUCH_H and wv.rect.top > C.FLOOR_Y - 40,
      "下端 %d 床 %d" % (C.FLOOR_Y + C.WAVE["dy"] + 15, C.FLOOR_Y))

# ---------------------------------------------------------------- 立ち往生
from sprites import Tachiojo  # noqa: E402

g = fresh([Tachiojo(380)], px=300)
tj = g.enemies[0]
hp0 = g.player.hp
run(g, 120, {"right"})
check("立ち往生に歩いてぶつかっても、ダメージは無く、通れない（手前で止まる）",
      g.player.hp == hp0 and not g.player.hurt_t and g.player.px <= tj.cx - (tj.w + C.PLAYER_W) / 2 + 0.5, "x=%.1f" % g.player.px)
snap(g, "tachiojo block")
g.sfx.clear()
run(g, 1, {"right"}, {"attack"})
run(g, 14, {"right"})
check("刀で斬っても、倒せない（白く光って、弾く音が鳴る）", tj.alive and not tj.dying and C.SFX_CLANG in g.sfx)
g.sfx.clear()
g.player.px = tj.cx - 80
run(g, 1, set(), {"throw"})
run(g, 40)
check("手裏剣も、弾かれる（手裏剣は、消える）", tj.alive and not tj.dying and not g.shurikens and C.SFX_CLANG in g.sfx)
g = fresh([Tachiojo(380)], px=300)
tj = g.enemies[0]
hp0 = g.player.hp
run_until(g, lambda gg: gg.player.px > tj.cx - 52, {"right"}, 200)
run(g, 1, {"right"}, {"jump"})
run(g, 70, {"right"})
check("手前から跳べば、立ち往生を越えられる（ダメージなし）", g.player.px > tj.cx + 20 and g.player.hp == hp0, "x=%.1f" % g.player.px)
g = fresh([Tachiojo(380)], px=380)
tj = g.enemies[0]
g.player.py, g.player.on_ground, g.player.vy = float(C.FLOOR_Y - 90), False, 0.0     # 真上から落ちてくる
run(g, 60)
check("上には、乗れない（横へ押し出されて、地面に降りる）", g.player.on_ground and g.player.py == C.FLOOR_Y
      and abs(g.player.px - tj.cx) >= (tj.w + C.PLAYER_W) / 2 - 0.5, "x=%.1f y=%.1f" % (g.player.px, g.player.py))
g = fresh([Tachiojo(380)], px=430)      # うしろ（右）に回った
tj = g.enemies[0]
g.player.facing = -1
run(g, 3)
g.sfx.clear()
run(g, 1, {"left"}, {"attack"})
run(g, 12)
check("立ち往生は、うしろから斬ると、倒せる（弾かれない）", tj.dying and C.SFX_CLANG not in g.sfx, "体力 %d" % tj.hp)
run(g, 3)
check("倒すと、おにぎりを必ず落とす。倒れたあとは、通れる", any(it.kind == "onigiri" and it.drop for it in g.items) and not tj.solid)
run(g, C.TACHIOJO["fade"] + 2)
check("立ち往生は、光になって消える", not g.enemies)
g = fresh([Tachiojo(380)], px=300)
check("立ち往生は、向きを変えない（来る側を、にらんだまま）", g.enemies[0].facing == -1)
g.player.px = 430.0
run(g, 5)
check("（うしろに回っても、振り向かない）", g.enemies[0].facing == -1 and g.enemies[0].behind)
g = fresh([Tachiojo(380)], px=350)
g.player.super_t = 100
run(g, 30, {"right"})
check("スーパータヌキでも、立ち往生は倒せない", g.enemies and not g.enemies[0].dying)
g = fresh([Tachiojo(380), Archer(560)], px=300)
tj, ar = g.enemies
hp0 = g.player.hp
g.player.px = tj.cx - (tj.w + C.PLAYER_W) / 2 - 2      # 立ち往生のすぐうしろ（弓兵の反対側）に隠れる
g.sfx.clear()
n_shots = 0
for _ in range(C.YUMI["cooldown"] * 2 + 120):
    n0 = len(g.waves)
    g.step(set())
    n_shots += len(g.waves) > n0
check("立ち往生のうしろに隠れると、弓兵の矢は、弾かれて届かない（矢よけ）",
      n_shots >= 2 and g.player.hp == hp0 and C.SFX_CLANG in g.sfx, "撃った %d 体力 %d" % (n_shots, g.player.hp))
check("高館には、立ち往生も、中ボスの弁慶も、出ない（役割がはっきりしないので、外した）",
      not any(k == "tachiojo" for k, x in PROD_STAGES[1].spawns) and not PROD_STAGES[1].gates)

# ---------------------------------------------------------------- 石灯籠
from sprites import Lantern  # noqa: E402
from stage import Terrain as _Terrain  # noqa: E402

bad = []
for st in _STAGES:
    tr = st.terrain()
    for kind, lx in st.lanterns:
        h = tr.height_at(lx)
        flat = h is not None and tr.height_at(lx - 18) == h == tr.height_at(lx + 18)
        clash = (abs(lx - st.stele_x) < 40 or abs(lx - st.checkpoint[0]) < 50 or not 40 < lx < st.width - 40
                 or any(pf[0] - 30 < lx < pf[1] + 30 and h - 110 < pf[2] < h for pf in st.platforms))
        if not flat or clash or kind == "dango":
            bad.append((st.name, kind, lx))
check("どの面にも石灯籠があり、平らな地面の上で、石碑・鳥居・足場と重ならない（団子は入れない）",
      all(st.lanterns for st in _STAGES) and not bad, str(bad))
_swap = list(STAGES)
STAGES[:] = PROD_STAGES
g = Game()
check("面を始めると、石灯籠が置かれている（火がともっている）", len(g.lanterns) == len(g.stage.lanterns) and all(lt.active for lt in g.lanterns))
lt = g.lanterns[0]
g.enemies = []
g.player.px, g.player.py = lt.cx - 30, lt.floor
run(g, 3)
n_items = len(g.items)
run(g, 1, (), {"attack"})
run(g, 12)
check("刀で斬ると、石灯籠が壊れて、中の物が出る", not lt.active and len(g.items) == n_items + 1 and g.items[-1].kind == lt.kind and g.items[-1].drop,
      "壊れた=%s 物=%d→%d" % (lt.broken, n_items, len(g.items)))
snap(g, "lantern break")
run(g, 60)
run(g, 1, (), {"attack"})
run(g, 12)
check("壊れた石灯籠は、もう何も出さない", len(g.items) <= n_items + 1)
C.DROPS = ()
g = Game()
lt = g.lanterns[0]
g.enemies = []
g.player.px, g.player.py = lt.cx - 90, lt.floor
run(g, 3)
run(g, 1, (), {"throw"})
run(g, 40)
check("手裏剣でも、壊せる（手裏剣は、そこで消える）", not lt.active and not g.shurikens)
g.player.hp = 0
for _ in range(C.RESPAWN_AT + 5):
    g.step(set())
check("やられて再開しても、壊した石灯籠は、壊れたまま", g.player.hp > 0 and not g.lanterns[0].active and g.lanterns[1].active)
g.reset(0)
check("最初からやり直すと、石灯籠は、元に戻る", all(x.active for x in g.lanterns))
STAGES[:] = _swap

# ---------------------------------------------------------------- 18. コントローラ
import pygame as _pg  # noqa: E402
import gamepad  # noqa: E402

pad = gamepad.Pad()
check("コントローラが無くても、起動できる（何も押していない扱い）", not pad.connected and pad.held() == set())


def ev(kind, **kw):
    return _pg.event.Event(getattr(_pg, kind), **kw)


if pad.sdl:
    A, B, X, Y = _pg.CONTROLLER_BUTTON_A, _pg.CONTROLLER_BUTTON_B, _pg.CONTROLLER_BUTTON_X, _pg.CONTROLLER_BUTTON_Y
    S = _pg.CONTROLLER_BUTTON_START
    check("Aで、ジャンプ（と、決定）", pad.handle(ev("CONTROLLERBUTTONDOWN", button=A, instance_id=0)) == {"jump", "restart"})
    check("Aを離すと、ジャンプを切る（長押しで高く跳べる）", pad.handle(ev("CONTROLLERBUTTONUP", button=A, instance_id=0)) == {"jump_release"})
    check("Xで刀", pad.handle(ev("CONTROLLERBUTTONDOWN", button=X, instance_id=0)) == {"attack"})
    check("Bで手裏剣（と、決定）、Yで手裏剣", pad.handle(ev("CONTROLLERBUTTONDOWN", button=B, instance_id=0)) == {"throw", "restart"}
          and pad.handle(ev("CONTROLLERBUTTONDOWN", button=Y, instance_id=0)) == {"throw"})
    check("Startで、再開と、ポーズ（遊んでいる間は、ポーズ。それ以外の画面では、決定）", pad.handle(ev("CONTROLLERBUTTONDOWN", button=S, instance_id=0)) == {"restart", "pause"})
    check("割り当てのないボタンは、何もしない", pad.handle(ev("CONTROLLERBUTTONDOWN", button=_pg.CONTROLLER_BUTTON_LEFTSTICK, instance_id=0)) == set())
check("スティックを倒すと、その向きに動く（少し倒しただけでは動かない）",
      gamepad.stick_held(0.9, 0.0) == {"right"} and gamepad.stick_held(-0.9, 0.0) == {"left"} and gamepad.stick_held(0.0, 0.9) == {"down"}
      and gamepad.stick_held(0.2, -0.3) == set() and gamepad.stick_held(0.0, -0.9) == {"up"})
check("抜き差しのイベントが来ても、止まらない", pad.handle(ev("CONTROLLERDEVICEADDED", device_index=99)) == set()
      and pad.handle(ev("CONTROLLERDEVICEREMOVED", instance_id=99)) == set())
pad2 = gamepad.Pad.__new__(gamepad.Pad)    # コントローラの部品が無い環境（ブラウザ版など）の想定
pad2.sdl, pad2.pads, pad2.fallback, pad2.names = None, {}, {}, {}
check("コントローラの部品が無い環境でも、止まらない", pad2.handle(ev("CONTROLLERBUTTONDOWN", button=0, instance_id=0)) == set() and pad2.held() == set())
g = Game()
g.enemies = []
x0 = g.player.px
g.title = False
run(g, 20, {"right"} | pad.held())
check("コントローラの入力を、ゲームに渡す形（キーボードと同じ文字列）で受け取れる", g.player.px > x0)

# ---------------------------------------------------------------- 20. 2面のボス（基衡）
from sprites import Boss2, Fan, Gale, Gust, Petal  # noqa: E402


def boss2_game():
    gg = Game()
    gg.reset(1)
    gg.title = False
    gg.intro_t = 999
    gg.player.hp = 6
    gg.player.px = gg.stage.arena_x0 + C.BOSS_TRIGGER + 10
    gg.player.py = gg.terrain.height_at(gg.player.px)
    run(gg, 2)
    return gg


gg = boss2_game()
check("2面は、基衡が出てくる", isinstance(gg.boss, Boss2) and gg.boss.max_hp == C.BOSS2["hp"])
check("1面は、泰衡のまま", type(Game().stage.boss_kind) is str and Game().stage.boss_kind == "boss")
seen, kinds = [], set()
for _ in range(1600):
    gg.step(set(), set())
    gg.player.hp, gg.player.invincible = 6, 0
    if gg.boss.state not in seen:
        seen.append(gg.boss.state)
    kinds |= {type(w).__name__ for w in gg.waves}
check("基衡は、風と扇を出す", {"Gust", "Fan"} <= kinds, str(kinds))
check("基衡は、構えてから攻撃して、隙になる", all(x in seen for x in ("wind_ready", "wind", "throw_ready", "throw", "recover")), str(seen))
check("体力が多いうちは、花びらを出さない", "Petal" not in kinds and "petal" not in seen)
check("基衡のどの状態でも、絵がある", all(gg.boss.image() is not None for _ in (0,)))

gg = boss2_game()
gg.boss.hp = gg.boss.max_hp // 2
kinds = set()
for _ in range(1500):
    gg.step(set(), set())
    gg.player.hp, gg.player.invincible = 6, 0
    kinds |= {type(w).__name__ for w in gg.waves}
check("体力が半分になると、花びらの雨が入る", "Petal" in kinds, str(kinds))

# 風: ダメージなしで押し戻す
gg = boss2_game()
b = gg.boss
b.state, b.st, b.cx = "walk", 0, gg.player.px + 80
g_ = Gust(gg.player.px + 10, gg.player.py - 17, -1, gg.a)
gg.waves.append(g_)
hp0, x0 = gg.player.hp, gg.player.px
run(gg, 12)
check("風に当たると、押し戻される（ダメージなし）", gg.player.px < x0 - 4 and gg.player.hp == hp0, "x %.1f→%.1f hp %d" % (x0, gg.player.px, gg.player.hp))
gg.waves = []
check("風は、刀で消せない", getattr(Gust, "cuttable", True) is False)

# 大風（月見坂の基衡だけ）: 予告の間は、押さない。吹くと、床にいる主人公を、押し続ける（ダメージなし）。足場の上には、届かない
def hold_boss(game, n):      # ボスを、歩かせたままにして（攻撃させずに）、進める
    for _ in range(n):
        game.boss.state, game.boss.st = "walk", 0
        run(game, 1)


gg = boss2_game()
gg.boss.cx = gg.player.px + 220
ar = gg._arena()
gale = Gale(ar["x0"], ar["x1"], gg.player.py, -1, gg.a)
gg.waves = [gale]
hp0, x0 = gg.player.hp, gg.player.px
hold_boss(gg, C.GALE["warn"] - 2)
check("大風は、予告の間は、押さない（ダメージもない）", not gale.blowing and abs(gg.player.px - x0) < 1 and gg.player.hp == hp0,
      "x %.1f→%.1f hp %d" % (x0, gg.player.px, gg.player.hp))
hold_boss(gg, 30)
x1 = gg.player.px
check("大風が吹くと、床にいる主人公は、押され続ける（ダメージなし）", gale.blowing and x1 < x0 - 40 and gg.player.hp == hp0,
      "x %.1f→%.1f hp %d" % (x0, x1, gg.player.hp))
gg.player.px, gg.player.py = x0, gg.player.py - C.GALE["h"] - 12      # 風より高い所（足場の高さ）
check("大風は、足場の高さには、届かない", not gg.player.rect.colliderect(gale.rect))
gg.player.py += C.GALE["h"] + 12
hold_boss(gg, C.GALE["blow"])
x2 = gg.player.px
hold_boss(gg, 10)
check("大風は、時間がたつと、やむ（やんだら、押されない）", not gale.alive and gale not in gg.waves and abs(gg.player.px - x2) < 1)
check("大風は、刀で消せない", Gale.cuttable is False)
# 高い大風: 足場の高さに吹く。床は静か（立っても、しゃがんでも、当たらない）。跳ぶと、帯に入って、流される
gg = boss2_game()
gg.boss.cx = gg.player.px + 220
ar = gg._arena()
floor0 = gg.player.py
hi = Gale(ar["x0"], ar["x1"], floor0, -1, gg.a, high=True)
gg.waves = [hi]
hp0, x0 = gg.player.hp, gg.player.px
hold_boss(gg, C.GALE["warn"] + 30)
check("高い大風は、床にいれば、押されない（ダメージもない）", hi.blowing and abs(gg.player.px - x0) < 1 and gg.player.hp == hp0,
      "x %.1f→%.1f" % (x0, gg.player.px))
gg.player.jump()
hold_boss(gg, 30)
check("高い大風の間に跳ぶと、風に流される（ダメージなし）", gg.player.px < x0 - 20 and gg.player.hp == hp0, "x %.1f→%.1f" % (x0, gg.player.px))
band = hi.rect
check("高い大風は、足場に立った主人公を包む。床に立った主人公には、届かない",
      band.top <= floor0 - 52 - C.PLAYER_H and floor0 - 52 <= band.bottom and band.bottom <= floor0 - C.PLAYER_H - 6, str(band))
# 基衡が、大風を呼ぶ: 扇を上げる（予告） → 振り下ろす → 風が吹いている間に、扇を投げる
gg = boss2_game()
b = gg.boss
b.pattern, b.count = C.BOSS2_GALE_PATTERN, C.BOSS2_GALE_PATTERN.index("G")
b.cx = gg.player.px + 200
b.state, b.st = "walk", C.BOSS2["walk_frames"] - 1
run(gg, 3)
check("基衡は、扇を高く上げて、大風を呼ぶ（床に、予告の風が流れ始める）",
      b.state == "gale_ready" and any(isinstance(w, Gale) and not w.blowing and not w.high for w in gg.waves), b.state)
gh = boss2_game()
bh = gh.boss
bh.pattern, bh.count = C.BOSS2_GALE_PATTERN, C.BOSS2_GALE_PATTERN.index("H")
bh.cx = gh.player.px + 200
bh.state, bh.st = "walk", C.BOSS2["walk_frames"] - 1
run(gh, 3)
check("順番が H のときは、高い大風を呼ぶ（予告の帯が、足場の高さに出る）",
      bh.state == "gale_ready" and any(isinstance(w, Gale) and w.high and w.rect.w == 0 and w.top < gh.player.py - C.PLAYER_H for w in gh.waves), bh.state)
run(gg, C.GALE["warn"] + C.BOSS2["gale_frames"] + 4)
check("大風が吹いている間に、続けて、扇を投げる", b.state in ("throw_ready", "throw") and any(isinstance(w, Gale) and w.blowing for w in gg.waves), b.state)
st3 = [st for st in PROD_STAGES if st.name == "月見坂"][0]
ar3 = st3.arenas[-1]
pl3 = [pl for pl in st3.platforms if pl[1] > ar3["x0"] and pl[0] < ar3["x1"]]
floor3 = st3.terrain().height_at(ar3["boss_x"])
check("月見坂のボスの間に、大風をやり過ごせる足場が、左右にある（風の高さより、上）",
      len(pl3) >= 2 and all(pl[2] <= floor3 - C.GALE["h"] - 8 for pl in pl3), str(pl3))
_hb, _ht = floor3 - C.GALE["high_bottom"], floor3 - C.GALE["high_bottom"] - C.GALE["high_h"]      # 高い大風の、下の縁・上の縁
check("月見坂のボスの間の足場に立つと、高い大風の帯の中に入る（床に立てば、帯の下）",
      all(_ht <= pl[2] - C.PLAYER_H and pl[2] <= _hb for pl in pl3) and _hb <= floor3 - C.PLAYER_H - 6, "帯 %d〜%d 足場 %s" % (_ht, _hb, pl3))
check("大風を使うのは、月見坂の基衡だけ（足場の無い間で戦う、影の基衡は、使わない）",
      set("GH") <= set(st3.boss_pattern) and not set("GH") & set(C.BOSS2_PATTERN + C.BOSS2_RAGE_PATTERN)
      and [st.name for st in PROD_STAGES if st.boss_kind == "boss2" and set("GH") & set(st.boss_pattern)] == ["月見坂"])

# 扇: 飛んで、戻ってくる。当たるとダメージ。刀で消せる
gg = boss2_game()
b = gg.boss
b.state, b.st = "walk", 0
b.cx = gg.player.px + 200
f = Fan(b.cx - 20, gg.player.py - C.FAN["y"], -1, gg.a, b)
far = f.px
for _ in range(300):
    f.update(gg.stage.width)
    if f.back:
        break
check("扇は、距離まで飛んだら、戻りに入る", f.back and far - f.px >= C.FAN["range"] - 2, "px %.1f" % f.px)
for _ in range(400):
    f.update(gg.stage.width)
    if not f.alive:
        break
check("扇は、ボスのところまで戻ったら、消える", not f.alive)
gg.waves = [Fan(gg.player.px + 4, gg.player.py - 20, -1, gg.a, b)]
hp0 = gg.player.hp
gg.step(set(), set())
check("扇に当たると、ダメージ", gg.player.hp == hp0 - C.FAN["damage"])
gg = boss2_game()
b = gg.boss
b.state, b.st = "walk", 0
gg.player.facing = 1
gg.waves = [Fan(gg.player.px + 14, gg.player.py - 20, -1, gg.a, b)]
gg.player.attack()
run(gg, 8)
check("扇は、刀で消せる", not any(isinstance(w, Fan) and w.alive for w in gg.waves) or gg.player.hp == 6)

# 花びら: 落ちる前は、当たらない。落ちたら、ダメージ
gg = boss2_game()
pt = Petal(gg.player.px, gg.player.py, gg.a)
check("花びらは、落ちる前は当たらない", pt.rect.w == 0)
gg.waves = [pt]
run(gg, C.PETAL["warn"] + 160)
check("花びらは、落ちて消える", not pt.alive)
gg = boss2_game()
gg.waves = [Petal(gg.player.px, gg.player.py, gg.a)]
gg.waves[0].t = C.PETAL["warn"]
gg.waves[0].py = gg.player.py - 20
hp0 = gg.player.hp
run(gg, 12)
check("花びらに当たると、ダメージ", gg.player.hp == hp0 - C.PETAL["damage"])

# 倒す: 吹っ飛んで、倒れた絵になる
gg = boss2_game()
run(gg, 400)
gg.boss.hit(gg.boss.hp)
run(gg, 200)
check("基衡を倒すと、倒れた絵になる", gg.boss.dying and gg.boss.image() is gg.a.boss2["down"][gg.boss.facing > 0])
snap(gg, "boss2 down")

# ---------------------------------------------------------------- 21. 面の順（本番）
# 実際の地理に合わせて、毛越寺 → 月見坂（月見坂の上が金色堂）。ボスは場所ではなく、遊ぶ順で決まる
STAGES[:] = PROD_STAGES
check("面の順は、毛越寺 → 高館 → 月見坂 → 金色堂", [st.name for st in STAGES] == ["毛越寺", "高館", "月見坂", "金色堂"] and Game().stage.name == "毛越寺")
check("面の番号が、遊ぶ順（面の名前・石碑の絵の番号）", [st.number for st in STAGES] == [1, 2, 3, 4])
import sprites  # noqa: E402
check("面の名前と石碑の絵が、1〜4番とも、ある", all(os.path.exists(os.path.join(sprites.IMG, f"{n}_{k}.png")) for k in range(1, 5) for n in ("stage_title", "stele")))
gp = Game()
gp.reset(0)
gp.title = False
gp.intro_t = 999
gp.player.px = gp.stage.arena_x0 + C.BOSS_TRIGGER + 10
gp.player.py = gp.terrain.height_at(gp.player.px)
run(gp, 2)
check("1面（毛越寺）のボスは、泰衡", gp.boss is not None and type(gp.boss).__name__ == "Boss" and gp.stage.name == "毛越寺")
gp = Game()
gp.reset(2)
gp.title = False
gp.intro_t = 999
gp.player.px = gp.stage.arena_x0 + C.BOSS_TRIGGER + 10
gp.player.py = gp.terrain.height_at(gp.player.px)
run(gp, 2)
check("3面（月見坂）のボスは、基衡", gp.boss is not None and type(gp.boss).__name__ == "Boss2" and gp.stage.name == "月見坂" and gp.boss.max_hp == C.BOSS2["hp"])
gp = Game()
gp.reset(1)
check("2面（高館）のボスは、秀衡", gp.stage.name == "高館" and gp.stage.boss_kind == "boss3")

# 地図: 面をクリアすると、前の場所から次の場所へ、道を歩く。高館が無い間は、寄らずに、分かれ道を通って月見坂へ
gm = Game(title=True)
gm.title = False
gm.reset(0)
gm.cleared = True
gm.advance()
check("クリアのあと、地図が出る（毛越寺から高館へ、歩く）", gm.map_on and gm.map_to == 2 and gm.map_len > 0 and gm.map_path[0] == C.MAP_PADS[1]
      and gm.map_path[-1] == C.MAP_PADS[2] and C.MAP_JUNCTION in gm.map_path)
pos0, _, arr0 = gm._map_pos()
run(gm, C.MAP_WAIT + 40)
pos1, _, arr1 = gm._map_pos()
check("駒は、待ってから、道を歩いていく", pos0 == C.MAP_PADS[1] and not arr0 and pos1 != pos0 and not arr1 and gm.map_on)
run(gm, int(gm.map_len / C.MAP_WALK_SPEED) + 5)
pos2, _, arr2 = gm._map_pos()
check("歩ききると、高館に着く", arr2 and pos2 == C.MAP_PADS[2] and gm.map_on, "%s on=%s t=%d len=%.0f" % (pos2, gm.map_on, gm.map_t, gm.map_len))
# 分かれ道と高館の間は、行き（毛越寺→高館）と帰り（高館→月見坂）で、同じ道。金の上に、帰りの白い点が、重なっていた
shared = [kind for (x, y), kind in gm._map_dot_kinds() if x > C.MAP_JUNCTION[0] + 4]
check("高館に着くと、分かれ道から高館までの道も、金になる（白い点が残らない）", bool(shared) and set(shared) == {"gold"}, str(sorted(set(shared))))
check("高館から先（月見坂へ）の道は、白のまま", "white" in {kind for (x, y), kind in gm._map_dot_kinds() if x < C.MAP_JUNCTION[0] - 8 and y < C.MAP_JUNCTION[1] - 8})
run(gm, C.MAP_HOLD + 5)
check("着いて少し待つと、ひとりでに、ゲームが始まる", not gm.map_on and gm.stage.name == "高館" and 0 < gm.frames < C.MAP_HOLD)
gm.player.hp, gm.lives = 0, 3
run(gm, C.RESPAWN_AT + 5)
check("やられて再開するときは、地図を出さない", not gm.map_on and gm.player.hp > 0)
gm.player.hp, gm.lives = 0, 1
run(gm, C.GAMEOVER_WAIT + 5)
run(gm, 1, (), {"restart"})
check("ゲームオーバーのやり直しも、地図を出さない", not gm.map_on)
# 高館がまだ無い間は、寄らずに、分かれ道を通って月見坂へ（高館を一時的に外して確かめる）
_keep = list(STAGES)
STAGES[:] = [STAGES[0], STAGES[2]]
gk = Game(title=True)
gk.title = False
gk.reset(0)
gk.cleared = True
gk.advance()
check("まだ無い面（高館）には寄らずに、分かれ道を通って、月見坂へ歩く", gk.map_to == 3 and C.MAP_PADS[2] not in gk.map_path and C.MAP_JUNCTION in gk.map_path)
STAGES[:] = _keep

# 難易度: 配置表のどの敵にも、討伐難易度が決まっている。面の敵の密度が、目標の幅に収まっている
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import difficulty  # noqa: E402
from collections import Counter  # noqa: E402

check("配置表の敵には、すべて討伐難易度が決まっている", all(difficulty.difficulty_of(k) for st in STAGES for k, _ in st.spawns))
for st in STAGES:
    cnt = Counter(k for k, _ in st.spawns)
    dens = sum(difficulty.difficulty_of(k) * n for k, n in cnt.items()) / (st.width / 1000)
    tgt = C.STAGE_TARGET[st.number][0]
    check("第%d面の敵の密度が、目標の幅に収まっている" % st.number, tgt * (1 - C.DENSITY_TOLERANCE) <= dens <= tgt * (1 + C.DENSITY_TOLERANCE), "%.1f / %g" % (dens, tgt))

# ---------------------------------------------------------------- 22. 4面のボス（清衡）
from sprites import Bead  # noqa: E402


def boss4_game():
    gg = Game()
    gg.reset(3)
    gg.title = False
    gg.intro_t = 999
    gg.player.hp = 6
    gg.player.px = gg.stage.arena_x0 + C.BOSS_TRIGGER + 10
    gg.player.py = gg.terrain.height_at(gg.player.px)
    run(gg, 2)
    return gg


gg = boss4_game()
check("4面は、清衡が出てくる（地面から浮いている）", type(gg.boss).__name__ == "Boss4" and gg.stage.name == "金色堂" and gg.boss.max_hp == C.BOSS4["hp"]
      and gg.boss.floor == gg.terrain.height_at(gg.stage.boss_x) - C.BOSS4["hover"])
seen, beads, ys = [], 0, set()
for _ in range(1500):
    gg.step(set(), set())
    gg.player.hp, gg.player.invincible = 6, 0
    if gg.boss.state not in seen:
        seen.append(gg.boss.state)
    for w in gg.waves:
        if isinstance(w, Bead) and w.t == 1:
            beads += 1
            ys.add(round(w.py))
check("清衡は、手を合わせてから、数珠の玉を飛ばす", all(x in seen for x in ("ready", "cast", "recover")) and beads >= 3, "%s %d" % (seen, beads))
check("玉は、低い・真ん中・高いの、3つの高さを飛ぶ", len(ys) >= 3, str(sorted(ys)))
gg.waves = [Bead(gg.player.px + 20, gg.player.py - 10, -1, gg.a)]
gg.player.hp, gg.player.invincible = 6, 0
run(gg, 12)
check("玉に当たると、ダメージ", gg.player.hp == 6 - C.BEAD["damage"])
gg = boss4_game()
b = gg.boss
b.state, b.st = "walk", 0
gg.player.facing = 1
gg.waves = []
gg.player.attack()
for _ in range(30):      # 刀が出る（振っている間の）フレームまで進めて、そこに玉を置く
    gg.step(set(), set())
    if gg.player.sword_rect():
        break
cx, cy = gg.player.sword_rect().center
gg.waves = [Bead(cx, cy, -1, gg.a)]
gg.step(set(), set())
check("玉は、刀で消せる（ダメージを受けずに）", not any(isinstance(w, Bead) and w.alive for w in gg.waves) and gg.player.hp == 6)
gg2 = boss4_game()
gg2.boss.hp = gg2.boss.max_hp // 2
check("体力が半分になると、玉が増える（構えの長さも変わる）", gg2.boss.rage and len(gg2.boss._volley()) > len(C.BOSS4_VOLLEYS[0]))
gg3 = boss4_game()
run(gg3, 400)
gg3.boss.hit(gg3.boss.hp)
run(gg3, 200)
check("清衡を倒すと、倒れた絵になる", gg3.boss.dying and gg3.boss.image() is gg3.a.enemy["boss4"]["death"][gg3.boss.facing > 0][1])

# ---------------------------------------------------------------- 23. 2面のボス（三代・秀衡。代をさかのぼる順で、2面）
gb = Game()
gb.reset(1)
gb.title = False
gb.intro_t = 999
gb.player.hp = 6
gb.player.px = gb.stage.arena_x0 + C.BOSS_TRIGGER + 10
gb.player.py = gb.terrain.height_at(gb.player.px)
gb.enemies = []
run(gb, 2)
check("2面（高館）は、秀衡が出てくる（体が大きく、体力が多い）", type(gb.boss).__name__ == "Boss3" and gb.boss.h == C.BOSS3["h"] and gb.boss.max_hp > C.BOSS["hp"])
heights = ""
gb.boss.P = dict(C.BOSS3, thrust_near=0)      # 光波の順番だけを見る（踏み込み突きは、下の検査で見る）
for _ in range(2400):
    gb.step(set(), set())
    gb.player.hp, gb.player.invincible = 6, 0
    gb.player.px = float(gb.stage.arena_x0 + 200)     # 跳びかかりで壁ぎわへ押されると、いつも跳びかかるので、真ん中に戻す
    for w in gb.waves:
        if isinstance(w, Wave) and w.t == 1:
            heights += "H" if w.tall else "L"
    if len(heights) >= 6:
        break
check("秀衡は、光波を、低・高と薙ぎ分ける（順番どおり）", heights == C.BOSS3_PATTERN[:len(heights)] and len(heights) >= 6, heights)
gb.boss.hit(gb.boss.hp)
run(gb, 200)
# 踏み込み突き: 近いと、光波の代わりに、速くて短い低い光波で突く（泰衡と、違う型にするため）
gt = Game()
gt.reset(1)
gt.title = False
gt.intro_t = 999
gt.player.hp = 6
gt.player.px = gt.stage.arena_x0 + C.BOSS_TRIGGER + 10
gt.player.py = gt.terrain.height_at(gt.player.px)
gt.enemies = []
run(gt, 2)
thrusts, normal, dashed, marker = [], [], False, False
for _ in range(3000):
    gt.step(set(), set())
    gt.player.hp, gt.player.invincible = 6, 0
    gt.player.px = float(gt.boss.cx - 110)       # 近くに立ち続ける（距離 150 より内側）
    gt.player.px = max(gt.player.px, float(gt.stage.arena_x0 + 40))
    marker = marker or (gt.boss.state == "ready" and gt.boss.thrust)
    for w in gt.waves:
        if isinstance(w, Wave) and w.t == 1:
            (thrusts if w.speed == C.BOSS3["thrust_speed"] else normal).append(w)
    if len(thrusts) >= 2:
        break
check("秀衡は、近いと、踏み込み突き（速くて短い、低い光波）を出す", len(thrusts) >= 2 and all(not w.tall and w.reach == C.BOSS3["thrust_range"] for w in thrusts), "%d" % len(thrusts))
check("突きの構えの間は、赤い矢印の予告が出る（thrust が立つ）", marker)
gf = Game()
gf.reset(1)
gf.title = False
gf.intro_t = 999
gf.player.hp = 6
gf.player.px = gf.stage.arena_x0 + C.BOSS_TRIGGER + 10
gf.player.py = gf.terrain.height_at(gf.player.px)
gf.enemies = []
run(gf, 2)
gf.boss.cx = gf.stage.arena_x0 + 420.0
x0 = gf.boss.cx
gf.boss.thrust, gf.boss.facing = True, -1
gf.boss._set("swing")
run(gf, 12)
check("突きのとき、前へ踏み込む（thrust_dash ドットほど）", abs((x0 - gf.boss.cx) - C.BOSS3["thrust_dash"]) <= 2, "%.1f" % (x0 - gf.boss.cx))
check("秀衡を倒すと、倒れた絵になる", gb.boss.dying and gb.boss.image() is gb.a.enemy["boss3"]["death"][gb.boss.facing > 0][1])

# ---------------------------------------------------------------- 24. 面の途中のボスの間（影のボス）
st4 = STAGES[3]
arenas = st4.arenas
check("4面には、ボスの間が4つ（影3つ＋清衡）", [a["kind"] for a in arenas] == ["boss", "boss3", "boss2", "boss4"] and [a["shadow"] for a in arenas] == [True, True, True, False])
check("ボスの間の地面は、平ら（幅480）", all(any(a0 <= a["x0"] and a["x1"] <= b0 and len({t for x0, x1, t in st4.ground if x0 < a["x1"] and a["x0"] < x1}) == 1 for a0, b0, _ in st4.ground) for a in arenas[:3]))


def gate_game(i=0):
    gg = Game()
    gg.reset(3)
    gg.title = False
    gg.intro_t = 999
    gg.player.hp = 6
    gg.enemies = []
    ar = st4.arenas[i]
    gg.player.px = float(ar["x0"] + C.BOSS_TRIGGER + 10)
    gg.player.py = float(gg.terrain.height_at(gg.player.px))
    run(gg, 2)
    return gg, ar


gg, ar = gate_game(0)
check("1つ目の間で、影の泰衡が出る（体力は半分、暗い）", type(gg.boss).__name__ == "Boss" and gg.boss.shadow and gg.boss.max_hp == max(C.SHADOW_MIN_HP, C.BOSS["hp"] // 2)
      and gg.boss_on and gg.arena_i == 0)
gg.player.hp = 6
for _ in range(400):
    gg.step(set(), set())
    gg.player.hp, gg.player.invincible = 6, 0
    gg.player.px = min(gg.player.px, ar["x1"] - 20)
    if gg.boss and gg.boss.intro_done:
        break
gg.player.px = float(ar["x1"] + 200)       # 右へ出ようとしても、影の間の右には出られない
gg.step(set(), set())
check("影の間の右へは出られない", gg.player.px <= ar["x1"] - C.PLAYER_W / 2 + 0.01 and gg.boss_on, "%.0f" % gg.player.px)
score0 = gg.score
gg.boss.hit(gg.boss.hp)
for _ in range(400):
    gg.step(set(), set())
    gg.player.hp = 6
    if gg.boss is None:
        break
check("影を倒すと、寸劇には入らず、先へ進める（ボスの間が開く）", gg.boss is None and not gg.boss_on and not gg.ending and not gg.cleared and gg.arena_i == 1)
check("影を倒すと、点が入り、おにぎりが出る", gg.score == score0 + C.SCORE_SHADOW and any(it.kind == "onigiri" and it.alive for it in gg.items[-3:]))
check("影を倒した所が、再開の場所になる", gg.gate_cp is not None and gg.gate_cp[3] == ar["x1"] + 60)
gg.player.px = float(ar["x1"] + 100)
gg.player.py = float(gg.terrain.height_at(gg.player.px))
cam0 = gg.cam_x
run(gg, 10)
cam1 = gg.cam_x
run(gg, 200)
check("影を倒したあとは、画面が、ゆっくり主役に戻る（急に飛ばない）", cam0 < cam1 < gg.player.px - 100 and abs(cam1 - cam0) <= 10 * C.BOSS_CAM_SPEED + 1
      and gg.cam_x >= gg.player.rect.centerx - C.BASE_W // 2 - 1, "%.0f %.0f %.0f" % (cam0, cam1, gg.cam_x))
gg.player.hp, gg.lives = 0, 3
run(gg, C.RESPAWN_AT + 5)
check("影を倒したあとにやられると、その所から再開する", gg.player.px == ar["x1"] + 60 and gg.player.hp > 0 and gg.boss is None)
gg2, ar2 = gate_game(1)
check("2つ目の間で、影の秀衡が出る", type(gg2.boss).__name__ == "Boss3" and gg2.boss.shadow and gg2.arena_i == 1)
gg2.player.hp, gg2.lives = 0, 3
run(gg2, C.RESPAWN_AT + 5)
check("影の間でやられると、その間の入口から再開する", abs(gg2.player.px - (ar2["x0"] + 100)) < 1 and gg2.boss is None and not gg2.boss_on)
gg3, ar3 = gate_game(2)
check("3つ目の間で、影の基衡が出る", type(gg3.boss).__name__ == "Boss2" and gg3.boss.shadow)
gg4 = Game()
gg4.reset(3)
gg4.title = False
gg4.intro_t = 999
gg4.player.px = float(st4.arena_x0 + C.BOSS_TRIGGER + 10)
gg4.player.py = float(gg4.terrain.height_at(gg4.player.px))
run(gg4, 2)
check("最後の間（清衡）は、本家（影ではない）", type(gg4.boss).__name__ == "Boss4" and not getattr(gg4.boss, "shadow", False) and gg4.arena_i == 3)

# ---------------------------------------------------------------- 出力
# ---------------------------------------------------------------- 清衡の攻撃（数珠の玉・光の柱・数珠の輪・転移）
from sprites import Boss4, Pillar  # noqa: E402
b4 = Boss4(400, None, C.FLOOR_Y, 0, 480, quick=True)
b4.state, b4.cy = "walk", b4.floor - b4.h / 2
me = pygame.Rect(100, C.FLOOR_Y - 36, 16, 36)
seen4, kinds4, x_before = [], set(), None
for _ in range(2600):
    b4.think(me, 480)
    if not seen4 or seen4[-1] != b4.state:
        seen4.append(b4.state)
    if b4.state == "warp_out" and x_before is None:
        x_before, hp_w = b4.cx, b4.hp
        b4.hit(1)
        warp_safe = b4.hp == hp_w
    kinds4 |= {type(w).__name__ for w in b4.spawned}
check("清衡は、数珠の玉・光の柱・数珠の輪・転移を、順に出す", all(k in seen4 for k in ("ready", "cast", "pillar_ready", "ring_ready", "warp_out", "warp_in"))
      and kinds4 == {"Bead", "Pillar"}, str(sorted(set(seen4))))
check("転移の間は、攻撃が当たらない。現れた先から、すぐ次の攻撃に移る（隙が無い）",
      warp_safe and seen4[seen4.index("warp_in") + 1] in ("ready", "ring_ready", "pillar_ready"))
b4 = Boss4(100, None, C.FLOOR_Y, 0, 480, quick=True)
b4.state, b4.cy = "walk", b4.floor - b4.h / 2
me = pygame.Rect(200, C.FLOOR_Y - 36, 16, 36)
b4._begin("warp", me)
check("転移は、主人公をはさんで、反対側へ（離れた所に現れる）", b4.dest > me.centerx and abs(b4.dest - me.centerx) >= C.BOSS4["warp_min"], "%.0f" % b4.dest)
b4.spawned.clear()
b4._begin("pillar", me)
ps = list(b4.spawned)
check("光の柱は3本。1本は主人公の足元、間に立てる幅がある", len(ps) == 3 and any(abs(q.px - me.centerx) < 1 for q in ps)
      and C.PILLAR["spread"] - C.PILLAR["w"] >= C.PLAYER_W + 20)
q = ps[1]
safe = all(not q.rect.colliderect(me) for _ in range(q.warn - 1) if q.update(480) is None)
q.update(480)
q.update(480)
check("光の柱は、予告の間は当たらない。落ちてくると当たる。刀では消せない", safe and q.rect.colliderect(me) and not q.cuttable)
# 予告は、1秒以上（60フレーム）。前は 0.9秒・怒ると 0.7秒で、発生が早すぎて、よけづらかった。清衡は、柱が落ちきるまで、手を上げている
_PL = C.PILLAR
check("光の柱の予告は、1秒以上ある（怒ったあとも）", _PL["warn"] >= 72 and _PL["rage_warn"] >= 60, "%d / %d" % (_PL["warn"], _PL["rage_warn"]))
check("清衡は、光の柱が落ちきるまで、次の動きに移らない",
      C.BOSS4["pillar_frames"] >= max(_PL["warn"] + _PL["stagger"] * (_PL["count"] // 2), _PL["rage_warn"] + _PL["stagger"] * (_PL["rage_count"] // 2)) + _PL["beam"])
b4.spawned.clear()
b4._set("ring_ready")
for _ in range(C.BOSS4["ring_ready"]):
    b4.think(me, 480)
ring = list(b4.spawned)
crouch = pygame.Rect(me.x, C.FLOOR_Y - C.CROUCH_H, 16, C.CROUCH_H)
flat = [r_ for r_ in ring if abs(r_.vy) < 0.01]
check("数珠の輪は、8つの玉が八方へ飛ぶ。横へ飛ぶ玉は、しゃがめば当たらない高さ",
      len(ring) == 8 and len(flat) == 2 and all(r_.rect.bottom <= crouch.top for r_ in flat), str([r_.rect.bottom for r_ in flat]))
b4.hp = b4.max_hp // 2
b4._set("walk")
for _ in range(C.BOSS4["rage_walk_frames"] + 1):
    b4.think(me, 480)
check("体力が半分になると、怒る（画面が揺れて、すぐ転移する）。柱は5本に増える", b4.state == "roar" and b4.landed and C.PILLAR["rage_count"] == 5)

# ---------------------------------------------------------------- 難しさ（やさしい・ふつう・むずかしい）
def level_game(level):
    gl = Game()
    gl.level = level
    gl.reset(1)
    return gl


ge, gn, gh = level_game("easy"), level_game("normal"), level_game("hard")
check("やさしい: 敵が減り、残機と団子が増える", len(ge.enemies) < len(gn.enemies) and ge.lives > gn.lives and ge.player.ammo > gn.player.ammo,
      "敵 %d / %d" % (len(ge.enemies), len(gn.enemies)))
check("むずかしい: 敵の数は同じ。落ち武者・弓兵が硬くなり、狐火・烏は1発のまま。残機と団子が減る",
      len(gh.enemies) == len(gn.enemies) and gh.lives < gn.lives and gh.player.ammo < gn.player.ammo
      and all(a.hp == b.hp + (1 if b.hp >= 2 else 0) for a, b in zip(gh.enemies, gn.enemies)))
check("ふつう: これまでと同じ（敵は、配置表どおり）", len(gn.enemies) == len(STAGES[1].spawns) and gn.lives == C.LIVES and gn.player.ammo == C.AMMO["start"])
hps = []
for gl in (ge, gn, gh):
    gl.title, gl.intro_t = False, 999
    gl.player.px = float(gl.stage.arenas[0]["x0"] + C.BOSS_TRIGGER + 10)
    gl.player.py = float(gl.terrain.height_at(gl.player.px))
    run(gl, 2)
    hps.append(gl.boss.max_hp)
check("ボス・中ボスの体力は、やさしい < ふつう < むずかしい", hps[0] < hps[1] < hps[2], str(hps))
gt = Game(title=True)
gt.title_t = 999
gt.step({"right"})
check("メニューを開く前は、左右を押しても、難しさは変わらない", gt.level == "normal")
gt.step(set(), {"restart"})
gt.step({"down"})
gt.step(set(), {"restart"})
gt.step({"right"})
gt.step({"right"})
check("メニューの LEVEL で、右を押すと、難しさが1つ上がる（押しっぱなしでは、進まない）", gt.level == "hard" and gt.lives == C.LEVELS["hard"]["lives"])
gt.step(set())
gt.step({"left"})
gt.step(set())
gt.step({"left"})
gt.step(set())
gt.step({"left"})
check("左で下がる。端で止まる", gt.level == "easy")
snap(gt, "title level")

# ---------------------------------------------------------------- 面の仕掛け（山おろし・光の柱の廊下）
from sprites import HillGust  # noqa: E402
wx0, wx1, wper = STAGES[2].winds[0]
gw = Game()
gw.reset(2)
gw.title, gw.enemies = False, []
gw.intro_t = wper - 1
gw.player.px = float(wx0 + 60)
gw.player.py = float(gw.terrain.height_at(gw.player.px))
run(gw, 2)
gust = [w for w in gw.waves if isinstance(w, HillGust)]
check("月見坂の坂では、上から、山おろしが吹き下ろす（坂の上の端から、左へ）", len(gust) == 1 and gust[0].dir == -1 and gust[0].px > wx1 - 20)
ys = set()
for _ in range(260):
    gust[0].update(gw.stage.width)
    h = gw.terrain.height_at(gust[0].px)
    if h is not None:
        ys.add(round(gust[0].rect.bottom - h))
check("山おろしは、段差を、地面ぞいに降りる", ys == {0} and gust[0].alive, str(ys))
gw.player.px, hp0 = gust[0].px - 6, gw.player.hp
gw.player.py = float(gw.terrain.height_at(gw.player.px))
x_before = gw.player.px
run(gw, 12)
check("山おろしに当たると、押し戻される（ダメージは無い）。跳べば越えられる高さ",
      gw.player.px < x_before - 10 and gw.player.hp == hp0 and C.GUST["h"] < 70, "%.0f" % (gw.player.px - x_before))
gw2 = Game()
gw2.reset(2)
gw2.intro_t = wper - 1
gw2.player.px = float(wx0 - C.WIND["near"] - 200)
run(gw2, 2)
check("離れている間は、風は吹かない", not any(isinstance(w, HillGust) for w in gw2.waves))
trap = STAGES[3].traps[0]
gp = Game()
gp.reset(3)
gp.title, gp.enemies = False, []
gp.player.px = float(trap[0] + 30)
gp.player.py = float(gp.terrain.height_at(gp.player.px))
gp.intro_t = trap[3] - 1
spots = gp._trap_spots(trap)
seen_x = set()
for _ in range(trap[3]):
    gp.player.hp = 6
    gp.step(set())
    seen_x |= {round(w.px) for w in gp.waves if isinstance(w, Pillar)}
check("金色堂の廊下では、床の印の所に、左から順に、光の柱が落ちる（印の間に、立てる幅がある）",
      seen_x == set(spots) and len(spots) >= 3 and trap[2] - C.PILLAR["w"] >= C.PLAYER_W + 40, "%s / %s" % (sorted(seen_x), spots))

# ---------------------------------------------------------------- 効果音
import sprites as _sp  # noqa: E402
_audio = os.path.join(os.path.dirname(__file__), "..", "assets", "audio")
lost = [f for f in C.SFX.values() if not os.path.exists(os.path.join(_audio, f))]
check("遊びの効果音のファイルが、すべてある（%d 種類）。大きさも、決めてある" % len(C.SFX), not lost and all(C.SFX[k] in C.SFX_VOLUME for k in C.SFX), str(lost))
used = set(k for call in re.findall(r'snd\(([^)]*)\)', open(os.path.join(os.path.dirname(__file__), "..", "sprites.py"), encoding="utf-8").read())
           for k in re.findall(r'"(\w+)"', call))
_unused = set(re.findall(r'snd\("(\w+)"', open(os.path.join(os.path.dirname(__file__), "..", "sprites.py"), encoding="utf-8").read()))
used |= set(re.findall(r'C\.SFX\["(\w+)"\]', open(os.path.join(os.path.dirname(__file__), "..", "main.py"), encoding="utf-8").read()))
check("用意した効果音は、すべて、どこかで鳴らしている（名前の書き間違いも無い）", used == set(C.SFX), "使っていない: %s / 無い名前: %s" % (sorted(set(C.SFX) - used), sorted(used - set(C.SFX))))
_sp.SOUNDS.clear()
g = fresh([Ochimusha(340)], px=300)
run(g, 1, pressed_first={"jump"})
heard = set(_sp.SOUNDS)
run(g, 30)
run(g, 1, pressed_first={"attack"})
run(g, 12)
heard |= set(_sp.SOUNDS)
check("跳ぶ・斬る・当たる、で音が鳴る", {C.SFX["jump"], C.SFX["swing"], C.SFX["hit"]} <= heard, str(sorted(heard)))
_sp.SOUNDS.clear()

# ---------------------------------------------------------------- ポーズ
g = fresh([Ochimusha(420)], px=300)
run(g, 5, {"right"})
x0, ex0 = g.player.px, g.enemies[0].cx
run(g, 1, (), {"pause"})
run(g, 40, {"right"}, {"jump"})
check("ポーズ中は、主人公も敵も、止まる（キーを押しても、動かない）", g.paused and g.player.px == x0 and g.enemies[0].cx == ex0 and g.player.on_ground)
snap(g, "pause")
run(g, 1, (), {"pause"})
run(g, 5, {"right"})
check("もう一度押すと、続きから動く", not g.paused and g.player.px > x0)
gt = Game(title=True)
gt.step(set(), {"pause"})
check("スタート画面では、ポーズにならない", not gt.paused and gt.title)
g = fresh(px=300)
g.step(set(), {"pause_on"})
g.step(set(), {"pause_on"})
check("窓が後ろに回ると、止まる（もう一度来ても、解除はされない）", g.paused)

# ---------------------------------------------------------------- 25. 中ボス（弁慶）。いまは、面から外してある。仕組みは残してあるので、テストの間だけ、高館に置いて確かめる
st3 = STAGES[1]
st3.gates = ((2820, "benkei"),)
ar3 = st3.arenas[0]
tr3 = st3.terrain()
check("弁慶の間を置ける場所が、高館にある（中間地点の手前。弁慶の立つあたりは、平ら）",
      ar3["kind"] == "benkei" and ar3["x1"] <= st3.checkpoint[0]
      and len({tr3.height_at(x) for x in range(ar3["x0"] + C.BOSS_TRIGGER, ar3["x1"], 20)}) == 1)


def benkei_game(dist):
    gb = Game()
    gb.reset(1)
    gb.title = False
    gb.intro_t = 999
    gb.enemies = []
    gb.player.px = float(ar3["x0"] + C.BOSS_TRIGGER + 10)
    gb.player.py = float(gb.terrain.height_at(gb.player.px))
    run(gb, 2)
    gb.cam_x = ar3["x0"]
    gb.player.px = float(gb.boss.cx - dist)
    return gb


gb = benkei_game(200)
bk = gb.boss
check("弁慶の間に入ると、弁慶が、最初から地面に立っている（影ではない・降ってこない）",
      type(bk).__name__ == "Benkei" and not getattr(bk, "shadow", False) and bk.midway and abs(bk.rect.bottom - gb.terrain.height_at(bk.cx)) <= 1)
x0 = bk.cx
run_until(gb, lambda q: q.boss.state == "ready", ())
check("離れていると、薙ぎ（光波）の構えになる。動かない", not bk.thrust and bk.cx == x0)
snap(gb, "benkei ready")
run_until(gb, lambda q: q.waves, ())
check("構えのあと、光波が、主人公のほうへ飛ぶ", bool(gb.waves) and gb.waves[0].vx < 0 if hasattr(gb.waves[0], "vx") else bool(gb.waves))
gb = benkei_game(50)
bk = gb.boss
gb.player.hp = 6
run_until(gb, lambda q: q.boss.state == "ready", ())
check("近づいていると、突きの構えになる", bk.thrust)
snap(gb, "benkei thrust")
gb.player.px = float(bk.cx - 150)        # 構えを見て、下がる
run_until(gb, lambda q: q.boss.state == "recover", ())
run(gb, 30)
check("突きは、下がれば届かない", gb.player.hp == 6, "HP %d" % gb.player.hp)
hp_b = bk.hp
bk.hit(1)
check("弁慶は、正面から斬っても、効く（特別な決まりは無い）", bk.hp == hp_b - 1)
bk.hit(bk.hp)
snap(gb, "benkei fade")
done = run_until(gb, lambda q: q.boss is None, ())
check("弁慶を倒すと、光になって消えて、先へ進める（おにぎりが出て、ここから再開できる）",
      done and not gb.boss_on and gb.arena_i == 1 and gb.gate_cp is not None and any(it.kind == "onigiri" for it in gb.items))
st3.gates = ()      # もとに戻す（本番の高館には、弁慶は出ない）

# ---------------------------------------------------------------- 崖登り（高館。画面が、上下にも動く）
from sprites import Arrow  # noqa: E402

gc = Game()
gc.reset(1)
tc = gc.terrain
cx0, cx1, ch = tc.climb
B = C.FLOOR_Y + ch      # 崖の下の、いちばん低い地面の高さ
TOP = C.FLOOR_Y - 64    # 崖の上
check("高館には、崖登りがある（面の絵が、崖の高さぶん、縦に長い）", tc.world_h == C.BASE_H + ch and gc._world is not None)
check("毛越寺と月見坂は、縦に動かない（面の絵は、画面と同じ高さ）",
      all(st.terrain().world_h == C.BASE_H for i, st in enumerate(STAGES) if i in (0, 2)))


def climb_at(x, y):
    gc._start(x, float(y))
    gc.enemies = []
    run(gc, 3)


climb_at(600, tc.height_at(600))
check("崖の手前では、画面は、崖の下の高さで止まっている（足元は、いままでと同じ高さに見える）",
      gc.cam_y == ch and gc.player.on_ground and gc.player.hp == C.PLAYER_HP and gc.player.py - gc.cam_y == tc.height_at(600) - ch)
climb_at(4700, tc.height_at(4700))
check("崖の上では、画面は、ふつうの高さで止まっている", gc.cam_y == 0 and gc.player.on_ground and gc.player.hp == C.PLAYER_HP)
arrow = Arrow(700, B - 60, 600, B - 40, -1, gc.a)
arrow.update(gc.stage.width)
check("崖の下でも、矢は、消えずに飛ぶ（面の下端は、崖の高さぶん、下にある）", arrow.alive)

# 実際に、跳んで登る（操作を入れて、1フレームずつ進める）
ROUTE = [(3645, 3695, B - 84), (3700, 3860, B - 128), (3805, 3855, B - 180), (3860, 4180, B - 224),
         (4035, 4085, B - 272), (4125, 4175, B - 322), (4035, 4085, B - 372), (4090, 4150, B - 424),
         (4040, 4080, B - 474), (4125, 4175, B - 520), (4180, 4400, TOP)]
check("崖登りの道すじの足場が、面のデータにある", all(s in tc.platforms or s in tc.ground for s in ROUTE))
climb_seen = []     # 登っている間の、足元の、画面の上での高さ


climb_safe = False      # 登る道すじだけを確かめるとき: 仕掛け（光の柱）に当たっても、落とされないようにする


def climb_step(held, pressed=()):
    if climb_safe:
        gc.player.invincible = 5
    gc.step(set(held), set(pressed))
    climb_seen.append(gc.player.py - gc.cam_y)


def hop(cur, nxt):
    """cur の上から、nxt へ跳ぶ。乗れたら True"""
    p = gc.player
    goal = max(cur[0] + 6, min(cur[1] - 6, (nxt[0] + nxt[1]) / 2))
    for n in range(600):        # 踏み切る所まで、歩く。離してから止まるまでに、20ドットほど滑るので、近くでは、1フレームずつ押す
        d = goal - p.px
        if abs(d) < 3 and abs(p.vx) < 0.1:
            break
        press = abs(d) > 24 or (abs(d) >= 3 and abs(p.vx) < 0.1 and n % 3 == 0)
        climb_step({"right" if d > 0 else "left"} if press else ())
    mid = (nxt[0] + nxt[1]) / 2
    for i in range(120):
        held = {"jump"} | ({"right"} if p.px < mid - 3 else {"left"} if p.px > mid + 3 else set())
        climb_step(held, {"jump"} if i == 0 else ())
        if i > 4 and p.on_ground:
            break
    return p.on_ground and p.py == nxt[2] and nxt[0] - 6 <= p.px <= nxt[1] + 6


climb_at(3600, B - 32)
cur, lost = (3540, 3700, B - 32), []
for nxt in ROUTE:
    if not hop(cur, nxt):
        lost.append((nxt, round(gc.player.px), round(gc.player.py)))
        break
    cur = nxt
    if nxt[2] == B - 372:
        snap(gc, "climb")
check("崖登り: 足場を1つずつ跳んで、崖の上まで登れる（操作を入れて、確かめる）", not lost and gc.player.hp == C.PLAYER_HP, str(lost))
check("登っている間、主役は、いつも画面の中にいる（足元が、画面の上 40〜下 240 の間）",
      40 <= min(climb_seen) and max(climb_seen) <= 240, "%.0f〜%.0f" % (min(climb_seen), max(climb_seen)))
run(gc, 60)
check("登りきると、画面は、崖の上の高さで止まる", gc.cam_y == 0 and gc.player.py == TOP)
snap(gc, "climb top")

# 落ちたとき: ミスにはならない。下の足場か、崖の下の地面に戻る
climb_at(4150, B - 520)
climb_seen.clear()
for _ in range(120):
    climb_step({"left"} if gc.player.on_ground and gc.player.py == B - 520 else ())
check("いちばん上の足場から、左へ踏み外しても、壁の下までは落ちない（途中の足場に乗る。体力は減らない）",
      gc.player.on_ground and B - 520 < gc.player.py < B - 224 and gc.player.hp == C.PLAYER_HP, "y=%.0f" % (B - gc.player.py))
climb_at(4060, B - 474)
climb_seen.clear()
for _ in range(200):
    climb_step({"left"} if gc.player.px > 4010 else ())
check("壁の下まで落ちても、ミスにならない（二段目の地面に戻るだけ）",
      gc.player.on_ground and gc.player.py == B - 224 and gc.player.hp == C.PLAYER_HP, "y=%.0f" % (B - gc.player.py))
check("落ちている間も、画面が追いかけて、主役は画面の中にいる", max(climb_seen) <= 240, "%.0f" % max(climb_seen))
check("落ちたあと、画面は、着地した高さに合う", abs(gc.cam_y - (B - 224 - C.CLIMB_CAM["feet"])) < 1, "%.0f" % gc.cam_y)

# 穴に落ちた判定は、その場所の高さに合わせる
gc._start(812, float(B - 80))       # 崖の下の、崖の切れ目（800〜880）
gc.enemies = []
deep = []
for _ in range(120):
    gc.step(set())
    deep.append((gc.player.py, gc.player.hp))
    if gc.player.hp < C.PLAYER_HP:
        break
check("崖の下の穴は、崖の下の画面から出たときに、落ちた扱いになる（それより上では、ならない）",
      gc.player.hp == C.PLAYER_HP - C.FALL_DAMAGE and max(y for y, hp in deep[:-1]) > C.FALL_Y + ch - C.MAX_FALL and all(hp == C.PLAYER_HP for y, hp in deep[:-1]),
      "%.0f まで落ちた（線は %d）" % (max(y for y, hp in deep[:-1]), C.FALL_Y + ch))
gc._start(4450, float(TOP - 10))    # 崖の上の、切れ目（4400〜4510）
gc.enemies = []
deep = []
for _ in range(120):
    gc.step(set())
    deep.append(gc.player.py)
    if gc.player.hp < C.PLAYER_HP:
        break
check("崖の上の穴は、いままでどおり、画面から出たら、落ちた扱いになる（崖の下までは、落ち続けない）",
      gc.player.hp == C.PLAYER_HP - C.FALL_DAMAGE and max(deep) < C.FALL_Y + C.MAX_FALL * 2, "%.0f" % max(deep))

# 金色堂の、最後の登り（清衡のいる壇へ。同じ仕組み）
gc = Game()
gc.reset(3)
tc = gc.terrain
cx0, cx1, ch = tc.climb
B = C.FLOOR_Y + ch
ROUTE4 = [(7325 + S4, 7375 + S4, B - 50), (7380 + S4, 7540 + S4, B - 96), (7485 + S4, 7535 + S4, B - 146), (7540 + S4, 7860 + S4, B - 192),
          (7805 + S4, 7855 + S4, B - 240), (7715 + S4, 7765 + S4, B - 288), (7805 + S4, 7855 + S4, B - 336), (7860 + S4, 8520 + S4, C.FLOOR_Y)]
check("金色堂の登りの道すじの足場が、面のデータにある", all(s in tc.platforms or s in tc.ground for s in ROUTE4),
      str([s for s in ROUTE4 if s not in tc.platforms and s not in tc.ground]))
climb_at(7300 + S4, B)
climb_safe = True
climb_seen.clear()
cur, lost = (7230 + S4, 7380 + S4, B), []
for nxt in ROUTE4:
    if not hop(cur, nxt):
        lost.append((nxt, round(gc.player.px), round(gc.player.py)))
        break
    cur = nxt
    if nxt[2] == B - 288:
        snap(gc, "climb4")
climb_safe = False
check("金色堂: 足場を1つずつ跳んで、清衡のいる壇の上まで登れる（操作を入れて、確かめる）", not lost, str(lost))
check("金色堂: 登っている間、主役は、いつも画面の中にいる", 40 <= min(climb_seen) and max(climb_seen) <= 240,
      "%.0f〜%.0f" % (min(climb_seen), max(climb_seen)))
run(gc, 60)
check("金色堂: 登りきると、画面は、壇の上の高さで止まる（清衡の間は、いままでと同じ高さ）", gc.cam_y == 0 and gc.player.py == C.FLOOR_Y)
gc._start(7740 + S4, float(B - 192))
gc.enemies = []
seen_p = []
for _ in range(400):
    gc.player.invincible = 5
    gc.step(set())
    seen_p += [round(w.px) for w in gc.waves if type(w).__name__ == "Pillar"]
check("金色堂の登りの壁には、足場の2本の柱すじ（7740・7830）に、光の柱が落ちる", set(seen_p) == {7740 + S4, 7830 + S4}, str(sorted(set(seen_p))))
# 影のボスは、床が低い所でも、画面のすぐ上から降ってくる
gz0 = Game()
gz0.reset(3)
a0 = gz0.stage.arenas[0]
gz0._start(a0["x0"] + C.BOSS_TRIGGER - 4, gz0._floor_at(a0["x0"] + 20))
gz0.enemies = []
run_until(gz0, lambda q: q.boss is not None, {"right"}, 60)
check("影のボスは、床が低い所（金色堂の、登りより手前）でも、画面のすぐ上から降ってくる",
      gz0.boss is not None and -C.BOSS["h"] - 1 <= gz0.boss.cy - gz0.cam_y <= 0 and gz0.cam_y == ch and run_until(gz0, lambda q: q.boss.intro_done, (), 400),
      "画面の上からの高さ %.0f" % (gz0.boss.cy - gz0.cam_y if gz0.boss else 0))
# ミイラ: 歩いてくるだけ
from sprites import Miira  # noqa: E402
gm = fresh(px=300)
mi = Miira(420, gm.a)
gm.enemies = [mi]
x_m = mi.cx
run(gm, 120)
check("ミイラは、主人公のほうへ、ゆっくり歩いてくる（落ち武者より遅い）。構えない・光波を出さない",
      0 < x_m - mi.cx <= 120 * C.MIIRA["speed"] + 0.01 and C.MIIRA["speed"] < C.OCHI["speed"] and not gm.waves and not mi.ready_t and not mi.swing_t)
snap(gm, "miira")
mi.hit(1)
check("ミイラは、1発で倒せる", mi.dying)
check("本番の毛越寺で、最初に出会う敵は、ミイラ", min(PROD_STAGES[0].spawns, key=lambda sp: sp[1])[0] == "miira")

# 消える光の足場（金色堂の、光の橋）
gk = Game()
gk.reset(3)
K = C.BLINK
bl = gk.terrain.blinks
check("金色堂に、消える光の足場が3つある（ほかの面には、無い）", len(bl) == 3 and all(not st.blinks for st in STAGES[:3]))
b0 = bl[0]
gk._start((b0[0] + b0[1]) / 2, float(b0[2]))
gk.enemies = []
t_on = (-b0[3]) % K["period"]
gk.intro_t = t_on + 5
run(gk, 10)
check("光の足場は、点いている間、乗れる", gk.player.on_ground and gk.player.py == b0[2])
snap(gk, "blink on")
run(gk, K["on"] - K["warn"])
check("消える前は、点滅する（まだ乗れる）", gk.terrain.blink_state(b0, gk.intro_t) == "warn" and gk.player.on_ground)
snap(gk, "blink warn")
run(gk, K["period"] - (gk.intro_t + b0[3]) % K["period"] - (K["period"] - K["on"]) + 8)     # 消えてから、8フレーム
check("消えると、乗っていても、落ちる", gk.terrain.blink_state(b0, gk.intro_t) == "off" and not gk.player.on_ground and gk.player.py > b0[2])
snap(gk, "blink off")


def _lit_frames(b):
    return {t for t in range(K["period"]) if gk.terrain.blink_state(b, t) != "off"}


both = [len(_lit_frames(a) & _lit_frames(b)) for a, b in zip(bl, bl[1:])]
check("となりどうしの光の足場は、60フレーム以上、一緒に点いている（乗り移る間がある）", min(both) >= 60, str(both))
def run_hop(cur, nxt):
    """走って渡る: 右を押したまま、足場の端で跳ぶ（橋は、立ち止まらずに渡る）"""
    p = gc.player
    for i in range(200):
        edge = p.px >= cur[1] - 14
        climb_step({"right", "jump"} if edge else {"right"}, {"jump"} if edge and p.on_ground else ())
        if i > 6 and p.on_ground and p.px > cur[1]:
            break
    return p.on_ground and p.py == nxt[2] and nxt[0] - 6 <= p.px <= nxt[1] + 6


# 実際に、光の橋を渡る（点いたばかりの足場へ、順に跳ぶ）
gc = gk
B = C.FLOOR_Y + gk.terrain.climb[2]
BRIDGE = [(6360 + S4, 6500 + S4, B), bl[0][:3], bl[1][:3], bl[2][:3], (6900 + S4, 7000 + S4, B - 16)]
check("光の橋の足場が、面のデータにある", all(s3 in gk.terrain.ground or s3 in gk.terrain.platforms or s3 in [b[:3] for b in bl] for s3 in BRIDGE))
climb_at(6440 + S4, B)
hp0, lost = gk.player.hp, []
for cur, nxt in zip(BRIDGE, BRIDGE[1:]):
    blink = [b for b in bl if b[:3] == nxt]
    for _ in range(K["period"] + 5):        # 行き先が、点いたばかりになるまで、待つ
        if not blink or (gk.intro_t + blink[0][3]) % K["period"] < 12:
            break
        climb_step(())
    if not run_hop(cur, nxt):
        lost.append((nxt, round(gk.player.px), round(gk.player.py)))
        break
check("光の橋: 点いた足場へ、順に跳んで、向こう岸まで渡れる（操作を入れて、確かめる。落ちない）", not lost and gk.player.hp == hp0, str(lost))
check("光の足場は、左から右へ、順に点く", [(-b[3]) % K["period"] for b in bl] == sorted((-b[3]) % K["period"] for b in bl))

# 動く足場（毛越寺の三つ目の池）
gm4 = Game()
gm4.reset(0)
tm = gm4.terrain
mv = tm.movers[0]
P = C.MOVER["period"]
check("動く足場は、時間の最初は A、半周りで B にいる（両端で止まる）",
      tm.mover_at(mv, 0)[0] == mv[0] and tm.mover_at(mv, P // 2)[0] == mv[2] and tm.mover_at(mv, int(P * 0.05))[0] == mv[0],
      str([tm.mover_at(mv, t)[0] for t in (0, P // 4, P // 2, P * 3 // 4)]))
gm4._start(mv[0] + mv[4] / 2, float(mv[1]))
gm4.enemies = []
gm4.intro_t = 0
x_start = gm4.player.px
rode = True
for _ in range(P // 2):
    gm4.step(set())
    rode = rode and gm4.player.on_ground and abs(gm4.player.py - tm.mover_now[0][2]) < 1.5
check("動く足場に乗ると、一緒に運ばれる（落ちない・足元が板の上に残る）", rode and gm4.player.px - x_start > (mv[2] - mv[0]) * 0.9,
      "動いた距離 %.0f（足場は %d）" % (gm4.player.px - x_start, mv[2] - mv[0]))
gm4._start(mv[0] - 30, float(tm.height_at(mv[0] - 30)))
gm4.enemies = []
gm4.intro_t = 0
gm4.step(set())
check("岸に立っているときは、動く足場に運ばれない", tm.rider(gm4.player.px, gm4.player.py) is None)

# 手裏剣の射程: 画面の端まで飛ぶ（画面の外に出たら、消える）
gs = fresh(px=1000)
run(gs, 2)
run(gs, 1, (), {"throw"})
run_until(gs, lambda q: q.shurikens, (), 40)
sh = gs.shurikens[0]
x_sh, far = sh.px, 0.0
for _ in range(200):
    gs.step(set())
    if not sh.alive:
        break
    far = sh.px - x_sh
edge = gs.cam_x + C.BASE_W - x_sh
check("手裏剣は、画面の端まで飛ぶ（前は、画面の3分の1で消えた）", not sh.alive and edge - 8 <= far <= edge + C.SHURIKEN_W + 1,
      "飛んだ距離 %.0f（画面の端まで %.0f）" % (far, edge))

# ボスと戦っている間、ザコ敵は、動かない（影のボスの間に、外の狐火が入ってこない）
gz = Game()
gz.reset(3)
az = gz.stage.arenas[0]
gz._start(az["x0"] + C.BOSS_TRIGGER - 4, gz._floor_at(az["x0"] + 20))
fire = Kitsunebi(az["x1"] + 100, "low", gz.a)
gz.enemies = [fire]
run(gz, 6, {"right"})
x_fire = fire.cx
for _ in range(240):
    gz.player.invincible = 5
    gz.step(set())
check("影のボスの間で戦っている間、間の外の狐火は、動き出さない（入ってこない）", gz.boss_on and fire.alive and fire.cx == x_fire and not fire.dir,
      "boss_on=%s x=%.0f→%.0f" % (gz.boss_on, x_fire, fire.cx))
from sprites import Pillar as _Pillar  # noqa: E402
import sprites as _sp  # noqa: E402
_sp.SOUNDS.clear()
_Pillar(100, C.FLOOR_Y, gz.a, quiet=True).update(1000)
loud = list(_sp.SOUNDS)
_Pillar(100, C.FLOOR_Y, gz.a).update(1000)
check("光の柱の予告の音は、続けて落ちるうちの、最初の1本だけが鳴らす", not loud and len(_sp.SOUNDS) == 1)
_sp.SOUNDS.clear()

# ---------------------------------------------------------------- 起動時の会社のロゴ画面
from splash import Splash  # noqa: E402
_sp = Splash()
_n = 0
while not _sp.done:
    _sp.step()
    _n += 1
check("ロゴ画面は、約2秒で終わる（現れる・止まる・消える）", _n == C.LOGO["fade"] * 2 + C.LOGO["hold"] and _sp.logo is not None, "frames=%d" % _n)
_sp = Splash()
_a0 = _sp.alpha()
_sp.t = C.LOGO["fade"] + 5
check("ロゴは、最初は見えず、止まっている間は、はっきり見える", _a0 == 0 and _sp.alpha() == 255)
_sp = Splash()
_sp.skip()
check("何かを押すと、ロゴを飛ばせる", _sp.done)

cols = 3
rows = (len(shots) + cols - 1) // cols
sheet = pygame.Surface((cols * C.BASE_W, rows * C.BASE_H))
for i, (label, s) in enumerate(shots):
    sheet.blit(s, ((i % cols) * C.BASE_W, (i // cols) * C.BASE_H))
pygame.image.save(sheet, os.path.join(os.path.dirname(__file__), "..", "assets", "concept", "smoke_sheet.png"))
print("場面:", [s[0] for s in shots])
print("失敗:", fails if fails else "なし")
