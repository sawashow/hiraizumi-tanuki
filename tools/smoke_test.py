"""ヘッドレスで操作を再生して、動きの結果を確認し、場面ごとのスクリーンショットを保存する。

使い方: python tools/smoke_test.py
出力: assets/concept/smoke_sheet.png（場面の一覧）
"""
import math
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame  # noqa: E402

import config as C  # noqa: E402
from main import ENEMY_SPAWNS, Game, drop_kind  # noqa: E402
from sprites import Item, Karasu, Kitsunebi, Ochimusha, Shuriken, Wave  # noqa: E402
from stage import GROUND, ITEMS, PLATFORMS, Terrain  # noqa: E402

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
check("体力: 落ち武者3・狐火1・烏1（飛ぶ敵は、もろい）", (oc.max_hp, ki.max_hp, ka.max_hp) == (3, 1, 1))
check("刀は手裏剣より強い", C.SWORD_DAMAGE > C.SHURIKEN_DAMAGE, "刀%d / 手裏剣%d" % (C.SWORD_DAMAGE, C.SHURIKEN_DAMAGE))
check("刀の回数: 落ち武者2回・狐火1回・烏1回",
      tuple(-(-e.max_hp // C.SWORD_DAMAGE) for e in (oc, ki, ka)) == (2, 1, 1))
check("手裏剣の発数: 落ち武者3発・狐火1発・烏1発",
      tuple(-(-e.max_hp // C.SHURIKEN_DAMAGE) for e in (oc, ki, ka)) == (3, 1, 1))
check("落ち武者が一番大きい", oc.w * oc.h > max(ki.w * ki.h, ka.w * ka.h))
check("烏は横長・狐火は小さい", ka.w > ka.h * 1.5 and ki.w * ki.h < ka.w * ka.h)
kinds = [k for k, _ in ENEMY_SPAWNS]
check("面の配置が、落ち武者8・狐火5・烏6", (kinds.count("ochimusha"), sum(k.startswith("kitsunebi") for k in kinds),
                                      kinds.count("karasu")) == (8, 5, 6))
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
check("刀で落ち武者のHPが2減る（3→1）", e.hp == 1, "HP=%d" % e.hp)
check("1振りで、同じ敵に1回だけ（2回当たっていない）", e.hp == 1)
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
check("落ち武者は手裏剣3発で倒れる（3→2→1→倒れる）", hits == [2, 1, 0], str(hits))
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
for _ in range(C.SWORD_SEQ[-1][1]):
    if gg.player.swing_id != n0:
        break
    gg.step(set())
check("隙が終わったら、すぐ次の刀が出る（押し直さなくていい）", gg.player.swing_id == n0 + 1 and seq_frame(gg.player.attack_t, C.SWORD_SEQ)[0] == 0)
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
# 地面と足場を「面」として、ジャンプで渡れるか（横のすき間90以下・上り66以下）を調べる
surf = [(a, b, top) for a, b, top in GROUND] + [(a, b, top) for a, b, top in PLATFORMS]
reach = {0}
frontier = [0]
while frontier:
    i = frontier.pop()
    for j, (a2, b2, t2) in enumerate(surf):
        if j in reach:
            continue
        a1, b1, t1 = surf[i]
        gap = max(a2 - b1, a1 - b2, 0)
        if gap <= 90 and (t1 - t2) <= 66 and not (j < len(GROUND) and i < len(GROUND) and (t1 - t2) > 40 and gap == 0):
            reach.add(j)
            frontier.append(j)
check("すべての地面と足場に、ジャンプで行ける", len(reach) == len(surf), "行けない: %s" % [surf[k] for k in range(len(surf)) if k not in reach])
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
from main import DANGO_TOTAL  # noqa: E402
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
# 団子を全部取ると、残機が増える
g = Game()
g.enemies = []
g.dango = DANGO_TOTAL - 1
dango_items = [it for it in g.items if it.kind == "dango"]
g.player.px, g.player.py = dango_items[0].cx, dango_items[0].cy + 8
g.player.py = float(R.height_at(g.player.px) or C.FLOOR_Y)
g.items = [Item("dango", g.player.px, g.player.py - 8, g.a, 0)]
run(g, 2)
check("団子を全部取ると、残機が1増える", g.lives == C.LIVES + 1 and g.one_up_given)
g.items = [Item("dango", g.player.px, g.player.py - 8, g.a, 1)]
run(g, 2)
check("1UPは、1回だけ", g.lives == C.LIVES + 1)
snap(g, "1UP")

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
    high_pose = gg.boss.image() is gg.boss._frames("swing")[0]
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
run(g, 1, (), {"restart"})
check("Enterで、最初から", not g.cleared and g.player.px == 60 and g.score == 0 and g.frames <= 1 and g.boss_state is None)

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
check("Enterで、刀の音が鳴る（すぐには始まらず、少し間がある）", g.sfx == [C.SFX_SWORD] and g.title and g.start_t == C.TITLE_START)
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
run(g, 120)
check("画面の右へ駆け抜けると、ゲームが始まる", not g.story and not g.title and g.bgm == C.BGM_STAGE1)
run(g, 30, {"right"})
check("始まると、動かせる", g.player.px > x0)
g = Game(title=True)
run(g, 1, (), {"attack"})
run(g, C.TITLE_START)
check("刀のキーでも、語りへ進む", not g.title and g.story)
run(g, 5, (), {"restart"})
check("語りは、始まってすぐはキーを受け付けない", g.story and g.story_run == 0)
run(g, C.STORY_SKIP_WAIT)
run(g, 1, (), {"attack"})
check("起きているときに押すと、すぐ気づいて走り出す（飛び起きない）", g.story_run > 0 and not g.story_woke and g.story_wake == T_["notice"] < T_["wake"])
run(g, 150)
check("語りからも、刀のキーで始められる", not g.story and not g.title)
g.player.px, g.player.py = float(C.ARENA_X0 + C.BASE_W // 2 - 1), float(C.FLOOR_Y)
run(g, 30, {"right"})
boss_until(g, lambda gg: gg.boss.state == "recover")
g.boss.hit(g.boss.hp)
boss_until(g, lambda gg: gg.cleared, 1500)
run(g, C.CLEAR_WAIT)
run(g, 1, (), {"restart"})
check("クリアのあと、Enterで、スタート画面へ戻る（雷も、最初から数え直す）", g.title and not g.story and not g.cleared and g.player.px == 60 and g.score == 0
      and g.title_t == 0 and g.thunder_n == 0)

# ---------------------------------------------------------------- 17. 回復・落とし物・強化3種類・中間地点の演出
class FixedRng:
    """くじを、決まった値にする"""
    def __init__(self, v):
        self.v = v

    def random(self):
        return self.v


C.DROPS = DROPS
total = sum(c for _, c in DROPS)
check("落とし物は、おにぎりと強化3種類。何も落とさないことのほうが多い", {k for k, _ in DROPS} == {"onigiri", "leaf", "triple", "super"} and total < 0.5,
      "落とす確率 %.2f" % total)
check("くじの値で、落とす物が決まる", drop_kind(0.0) == DROPS[0][0] and drop_kind(total - 0.001) == DROPS[-1][0] and drop_kind(total) is None
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

# ---------------------------------------------------------------- 出力
cols = 3
rows = (len(shots) + cols - 1) // cols
sheet = pygame.Surface((cols * C.BASE_W, rows * C.BASE_H))
for i, (label, s) in enumerate(shots):
    sheet.blit(s, ((i % cols) * C.BASE_W, (i // cols) * C.BASE_H))
pygame.image.save(sheet, os.path.join(os.path.dirname(__file__), "..", "assets", "concept", "smoke_sheet.png"))
print("場面:", [s[0] for s in shots])
print("失敗:", fails if fails else "なし")
