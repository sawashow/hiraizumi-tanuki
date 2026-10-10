"""ヘッドレスで操作を再生して、動きの結果を確認し、場面ごとのスクリーンショットを保存する。

使い方: python tools/smoke_test.py
出力: assets/concept/smoke_sheet.png（場面の一覧）
"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame  # noqa: E402

import config as C  # noqa: E402
from main import Game  # noqa: E402

pygame.init()
pygame.display.set_mode((C.BASE_W, C.BASE_H))
font = pygame.font.Font(None, 20)
screen = pygame.Surface((C.BASE_W, C.BASE_H))
g = Game()
shots = []
fails = []


def snap(label):
    g.draw(screen, font)
    shots.append((label, screen.copy()))


def run(n, held=(), pressed_first=()):
    for i in range(n):
        g.step(set(held), set(pressed_first) if i == 0 else set())


def check(name, cond, detail=""):
    print(("OK  " if cond else "NG  ") + name + (" " + detail if detail else ""))
    if not cond:
        fails.append(name)


# 1. 開始と歩き
snap("start")
x0 = g.player.px
run(40, {"right"})
check("右に歩ける", g.player.px > x0 + 50, "x=%.0f" % g.player.px)
snap("walk")

# 2. ジャンプ（頂点と着地）
run(1, (), {"jump"})
peak = 99999
for _ in range(60):
    run(1)
    peak = min(peak, g.player.py)
    if g.player.vy > -0.5 and g.player.vy < 0.5 and len(shots) == 2:
        snap("jump top")
check("ジャンプで上がる", C.FLOOR_Y - peak > 50, "高さ=%.0f" % (C.FLOOR_Y - peak))
check("ジャンプ後に着地する", g.player.on_ground)

# 3. 刀で敵を倒す（敵の少し手前まで歩いてから振る）
g.player.px = 440.0
target = min(g.enemies, key=lambda e: abs(e.px - 520))
while g.player.rect.right + 40 < target.rect.left:
    run(1, {"right"})
while abs(g.player.vx) > 0:   # 慣性があるので、手を離して滑り終わるのを待つ
    run(1)
while g.player.rect.right + 10 < target.rect.left:
    run(1, {"right"})
    if g.player.rect.right + 10 >= target.rect.left:
        break
hp_before = target.hp
run(1, (), {"attack"})
sword_seen = False
for _ in range(30):
    run(1)
    if g.player.sword_rect() is not None and not sword_seen:
        sword_seen = True
        snap("sword active")
check("刀の判定が出る", sword_seen)
check("刀で敵にダメージ", target.hp < hp_before or not target.alive, "敵HP %d→%d" % (hp_before, target.hp))
check("1振りで同じ敵に1回だけ", hp_before - target.hp <= 1)

# 4. 手裏剣（直前の被ダメージの硬直が残らないよう、状態を戻してから）
g.player.hurt_t = 0
g.player.invincible = 0
g.player.px = 700.0
g.player.facing = 1
n_before = len(g.enemies)
run(1, (), {"throw"})
released = False
for _ in range(12):
    run(1)
    if g.shurikens and not released:
        released = True
        snap("shuriken thrown")
check("手裏剣が発射される", released)
for _ in range(80):
    run(1)
    if g.effects and len(shots) < 8 and shots[-1][0] != "shuriken hit":
        snap("shuriken hit")
hit_enemy = [e for e in g.enemies if e.px > 700]
check("手裏剣が敵に当たる（敵HPが減る）", any(e.hp < C.ENEMY_HP for e in g.enemies) or len(g.enemies) < n_before)

# 5. 敵に触れてダメージ（踏んでも倒せない）
e = g.enemies[0]
g.player.px = float(e.rect.centerx)
g.player.py = float(C.FLOOR_Y)
hp = g.player.hp
run(1)
check("敵に触れるとダメージ", g.player.hp == hp - 1, "HP %d→%d" % (hp, g.player.hp))
snap("hurt")
run(2)
check("無敵中は連続ダメージを受けない", g.player.hp == hp - 1)
check("敵は踏んでも倒れない", e.alive)

# 6. ゲームオーバーと再開
g.player.invincible = 0
g.player.hp = 1
g.player.px = float(g.enemies[0].rect.centerx)
run(1)
check("HP0でゲームオーバー", g.player.hp == 0)
snap("game over")
g.step(set(), {"restart"})
check("Enterで再開", g.player.hp == C.PLAYER_HP and g.player.px == 60)

# 7. 面の終わり（カメラが止まる）
g.player.px = float(C.STAGE_W - 40)
run(2)
check("カメラが面の端で止まる", g.cam_x == C.STAGE_W - C.BASE_W, "cam=%d" % g.cam_x)
snap("stage end")


# 8. 慣性（マリオのような操作感）
def fresh():
    gg = Game()
    gg.player.px = 800.0
    for e in gg.enemies:
        e.px = 5000.0   # 邪魔にならない所へ
        e.x0 = 5000.0
    return gg


def vx_after(held_frames, held):
    gg = fresh()
    for _ in range(held_frames):
        gg.step(set(held))
    return gg


# 加速: 押した直後は遅く、約0.3秒（18フレーム）で最高速
gg = fresh(); gg.step({"right"})
check("押した直後はまだ遅い（加速する）", 0 < gg.player.vx < 0.5, "vx=%.2f" % gg.player.vx)
gg = vx_after(25, {"right"})
check("しばらく押すと最高速に届く", abs(gg.player.vx - C.MAX_SPEED) < 0.01, "vx=%.2f" % gg.player.vx)
# 減速: 離しても少し滑る
gg = vx_after(25, {"right"}); x_release = gg.player.px
gg.step(set())
check("離した直後はまだ動いている（滑る）", gg.player.vx > 1.5, "vx=%.2f" % gg.player.vx)
n = 0
while abs(gg.player.vx) > 0 and n < 60:
    gg.step(set()); n += 1
check("離すと十数フレームで止まる", 8 <= n <= 20, "止まるまで %d フレーム" % n)
check("滑った距離が0より大きい", gg.player.px - x_release > 10, "滑走 %.0f px" % (gg.player.px - x_release))
# 切り返し: すべってから向きが変わる
gg = vx_after(25, {"right"})
gg.step({"left"})
check("切り返しの直後は、まだ右向き（すべっている）", gg.player.facing == 1 and gg.player.vx > 0, "vx=%.2f 向き=%d" % (gg.player.vx, gg.player.facing))
for _ in range(30):
    gg.step({"left"})
check("そのまま押すと左向きに変わって左へ進む", gg.player.facing == -1 and gg.player.vx < 0, "vx=%.2f" % gg.player.vx)
# ジャンプの勢いが保たれる
gg = vx_after(25, {"right"}); gg.step({"right"}, {"jump"})
vx_jump = gg.player.vx
for _ in range(10):
    gg.step(set())
check("ジャンプ中に手を離しても勢いが残る", gg.player.vx > vx_jump - 0.3 and not gg.player.on_ground, "vx=%.2f" % gg.player.vx)
# 空中の方向転換
gg = vx_after(25, {"right"}); gg.step({"right"}, {"jump"})
for _ in range(10):
    gg.step({"left"})
check("空中で向きを変えられる", gg.player.facing == -1)
vx_a = gg.player.vx
for _ in range(10):
    gg.step({"left"})
check("空中で反対に押し続けると、緩やかに逆向きになる", gg.player.vx < vx_a, "vx %.2f→%.2f" % (vx_a, gg.player.vx))
# 空中の攻撃中も向きを変えられる
gg = fresh(); gg.step(set(), {"jump"})
for _ in range(5):
    gg.step(set())
gg.step(set(), {"attack"})
gg.step({"left"})
check("空中で刀を振っていても向きを変えられる", gg.player.facing == -1)
# 地上の攻撃中は入力を受けず、勢いのまま滑って止まる
gg = vx_after(25, {"right"})
gg.step({"right"}, {"attack"})
v0 = gg.player.vx
for _ in range(10):
    gg.step({"left"})
check("地上の攻撃中は入力を受けず、向きも変わらない", gg.player.attack_t > 0 and gg.player.facing == 1)
for _ in range(8):
    gg.step({"left"})
check("攻撃中に滑って止まる（入力は無視されたまま）", gg.player.attack_t > 0 and abs(gg.player.vx) < 0.01 and gg.player.facing == 1,
      "vx=%.2f" % gg.player.vx)
# 可変ジャンプ
def jump_height(release_after):
    gg = fresh(); gg.step(set(), {"jump"}); top = gg.player.py
    for i in range(1, 80):
        gg.step(set(), {"jump_release"} if i == release_after else set())
        top = min(top, gg.player.py)
    return C.FLOOR_Y - top
h_long, h_short = jump_height(None), jump_height(2)
check("ボタンを長く押すと高く、早く離すと低い", h_short < h_long * 0.7, "長押し %.0f / 早離し %.0f" % (h_long, h_short))
check("早く離しても跳ぶ（0にはならない）", h_short > 15)

# 9. 空中の軽さ
gg = vx_after(25, {"right"}); gg.step({"right"}, {"jump"})
n = 0
while gg.player.vx > -1.0 and n < 120 and not gg.player.on_ground:
    gg.step({"left"}); n += 1
check("空中で逆向きに押すと約0.4秒で反転方向に動く", n <= 30 and gg.player.vx <= -1.0, "%d フレームで vx=%.2f" % (n, gg.player.vx))
def air_time_and_height():
    gg = fresh(); gg.step(set(), {"jump"}); up = down = 0; top = gg.player.py; peaked = False
    for _ in range(200):
        gg.step(set())
        if gg.player.on_ground:
            break
        if not peaked and gg.player.vy > 0:
            peaked = True
        top = min(top, gg.player.py)
        if peaked: down += 1
        else: up += 1
    return up, down, C.FLOOR_Y - top
up, down, height = air_time_and_height()
check("下降は上昇より速い（ふわっとしない）", down < up, "上昇 %d / 下降 %d フレーム" % (up, down))
check("ジャンプの高さは変わらない", 65 <= height <= 80, "高さ %.0f" % height)

cols = 3
rows = (len(shots) + cols - 1) // cols
sheet = pygame.Surface((cols * C.BASE_W, rows * C.BASE_H))
for i, (label, s) in enumerate(shots):
    sheet.blit(s, ((i % cols) * C.BASE_W, (i // cols) * C.BASE_H))
pygame.image.save(sheet, os.path.join(os.path.dirname(__file__), "..", "assets", "concept", "smoke_sheet.png"))
print("場面:", [s[0] for s in shots])
print("失敗:", fails if fails else "なし")
