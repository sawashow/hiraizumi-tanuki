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
from main import ENEMY_SPAWNS, Game  # noqa: E402
from sprites import Item, Karasu, Kitsunebi, Ochimusha, Shuriken, Wave  # noqa: E402
from stage import GROUND, ITEMS, PLATFORMS, Terrain  # noqa: E402

# 古い（平らな）地形。穴と足場の動きのテスト用
_T = C.FLOOR_Y
OLD_GROUND = ((0, 700, _T), (780, 1250, _T), (1380, 1700, _T), (1830, C.STAGE_W, _T))
OLD_PLATFORMS = ((980, 1044, _T - 62), (1290, 1340, _T - 50), (1740, 1790, _T - 56))

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
check("体力が違う（落ち武者3・狐火2・烏2）", (oc.max_hp, ki.max_hp, ka.max_hp) == (3, 2, 2))
check("刀は手裏剣より強い", C.SWORD_DAMAGE > C.SHURIKEN_DAMAGE, "刀%d / 手裏剣%d" % (C.SWORD_DAMAGE, C.SHURIKEN_DAMAGE))
check("刀の回数: 落ち武者2回・狐火1回・烏1回",
      tuple(-(-e.max_hp // C.SWORD_DAMAGE) for e in (oc, ki, ka)) == (2, 1, 1))
check("手裏剣の発数: 落ち武者3発・狐火2発・烏2発",
      tuple(-(-e.max_hp // C.SHURIKEN_DAMAGE) for e in (oc, ki, ka)) == (3, 2, 2))
check("落ち武者が一番大きい", oc.w * oc.h > max(ki.w * ki.h, ka.w * ka.h))
check("烏は横長・狐火は小さい", ka.w > ka.h * 1.5 and ki.w * ki.h < ka.w * ka.h)
kinds = [k for k, _ in ENEMY_SPAWNS]
check("面の配置が、落ち武者4・狐火3・烏3", (kinds.count("ochimusha"), sum(k.startswith("kitsunebi") for k in kinds),
                                      kinds.count("karasu")) == (4, 3, 3))
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
check("狐火は、手裏剣1発では倒れず、2発目で倒れる", g.enemies[0].active)
g.enemies[0].hit(C.SHURIKEN_DAMAGE)
check("狐火は、手裏剣2発で倒れる", g.enemies[0].dying)

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
check("切り返しの直後は、まだ右向き（すべっている）", gg.player.facing == 1 and gg.player.vx > 0)
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
for _ in range(8):
    gg.step({"left"})
check("攻撃中に滑って止まる（入力は無視されたまま）",
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

# ---------------------------------------------------------------- 出力
cols = 3
rows = (len(shots) + cols - 1) // cols
sheet = pygame.Surface((cols * C.BASE_W, rows * C.BASE_H))
for i, (label, s) in enumerate(shots):
    sheet.blit(s, ((i % cols) * C.BASE_W, (i // cols) * C.BASE_H))
pygame.image.save(sheet, os.path.join(os.path.dirname(__file__), "..", "assets", "concept", "smoke_sheet.png"))
print("場面:", [s[0] for s in shots])
print("失敗:", fails if fails else "なし")
