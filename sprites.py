"""絵の読み込みと、主人公・敵・手裏剣・命中エフェクトのクラス"""
import os

import pygame

import config as C

IMG = os.path.join(os.path.dirname(__file__), "assets", "images")


def _load(name):
    return pygame.image.load(os.path.join(IMG, name)).convert_alpha()


class Assets:
    """絵をまとめて読み込む。左向き用は反転して持つ"""

    def __init__(self):
        n = 23
        self.player = {True: [_load(f"player_{i:02d}.png") for i in range(n)]}  # True=右向き
        self.player[False] = [pygame.transform.flip(s, True, False) for s in self.player[True]]
        self.shuriken = [_load(f"shuriken_{i:02d}.png") for i in range(4)]
        self.shuriken_left = [pygame.transform.flip(s, True, False) for s in self.shuriken]
        self.hit = [_load(f"hit_{i:02d}.png") for i in range(3)]
        self.sky = _load("bg_sky.png")
        self.mid = _load("bg_mid.png")
        self.tiles = [_load(f"tile_{i:02d}.png") for i in range(6)]


def _approach(value, target, step):
    """value を target に向けて、1回に step だけ近づける"""
    if value < target:
        return min(value + step, target)
    return max(value - step, target)


def seq_frame(t, seq):
    """経過フレーム t（1始まり）が、seq の何番目のコマか。(番号, コマ番号) を返す。終わっていれば None"""
    acc = 0
    for i, (frame, dur) in enumerate(seq):
        acc += dur
        if t <= acc:
            return i, frame
    return None


class Player:
    def __init__(self, x, assets):
        self.a = assets
        self.px = float(x)
        self.py = float(C.FLOOR_Y)   # 足元の高さ
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        self.on_ground = True
        self.hp = C.PLAYER_HP
        self.invincible = 0
        self.hurt_t = 0
        self.jump_cut_done = False
        self.attack_t = 0
        self.throw_t = 0
        self.swing_id = 0
        self.air_t = 0
        self.land_t = 0
        self.walk_t = 0
        self.idle_t = 0
        self.moving = False
        self.release = False   # このフレームに手裏剣を発射する

    # --- 当たり判定 ---
    @property
    def rect(self):
        return pygame.Rect(round(self.px - C.PLAYER_W / 2), round(self.py - C.PLAYER_H), C.PLAYER_W, C.PLAYER_H)

    def sword_rect(self):
        """振り下ろしのコマの間だけ、向いている側に出る"""
        if not self.attack_t:
            return None
        cur = seq_frame(self.attack_t, C.SWORD_SEQ)
        if cur is None or cur[0] != C.SWORD_ACTIVE:
            return None
        r = self.rect
        top = r.top + 2
        if self.facing > 0:
            return pygame.Rect(r.right, top, C.SWORD_W, C.SWORD_H)
        return pygame.Rect(r.left - C.SWORD_W, top, C.SWORD_W, C.SWORD_H)

    # --- 操作 ---
    @property
    def busy(self):
        return bool(self.attack_t or self.throw_t or self.hurt_t)

    def jump(self):
        if self.on_ground and not self.busy and self.hp > 0:
            self.vy = C.JUMP_SPEED
            self.on_ground = False
            self.air_t = 0
            self.jump_cut_done = False

    def cut_jump(self):
        """ジャンプボタンを早く離したとき、上昇を弱める（押し続けるほど高く跳ぶ）"""
        if not self.on_ground and not self.jump_cut_done and self.vy < C.JUMP_CUT_MIN:
            self.vy *= C.JUMP_CUT
            self.jump_cut_done = True

    def attack(self):
        if not self.busy and self.hp > 0:
            self.attack_t = 1
            self.swing_id += 1

    def throw(self):
        if not self.busy and self.hp > 0:
            self.throw_t = 1

    def take_damage(self, from_x, amount=1):
        if self.invincible or self.hp <= 0:
            return
        self.hp -= amount
        self.invincible = C.INVINCIBLE_FRAMES
        self.hurt_t = C.HURT_FRAMES
        self.attack_t = 0
        self.throw_t = 0
        self.vx = C.KNOCKBACK if self.px >= from_x else -C.KNOCKBACK

    # --- 更新 ---
    def update(self, held, stage_w):
        self.release = False
        direction = ("right" in held) - ("left" in held)
        if self.hp <= 0 or self.hurt_t:
            if self.hurt_t:
                self.hurt_t -= 1
            self.vx = _approach(self.vx, 0.0, C.FRICTION)   # のけぞり・倒れている間は操作を受けない
        elif self.on_ground:
            if self.attack_t or self.throw_t:
                self.vx = _approach(self.vx, 0.0, C.FRICTION)   # 攻撃中は入力を受けず、勢いのまま滑って止まる
            elif direction == 0:
                self.vx = _approach(self.vx, 0.0, C.FRICTION)
            elif self.vx * direction < 0:
                self.vx = _approach(self.vx, 0.0, C.TURN_DECEL)  # 逆向きに押したら、まず減速（すべる）
            else:
                self.vx = _approach(self.vx, direction * C.MAX_SPEED, C.ACCEL)
            # 向きは、進む向きと押している向きがそろったときに変える（すべっている間は変えない）
            if direction and not (self.attack_t or self.throw_t) and self.vx * direction >= 0:
                self.facing = direction
        else:
            # 空中は、攻撃中でも向きを変えられる。加速は緩く、離しても勢いはほぼ保つ
            if direction:
                self.vx = _approach(self.vx, direction * C.MAX_SPEED, C.AIR_ACCEL)
                self.facing = direction
            else:
                self.vx = _approach(self.vx, 0.0, C.AIR_FRICTION)
        self.px += self.vx
        lo, hi = C.PLAYER_W / 2, stage_w - C.PLAYER_W / 2
        if not lo <= self.px <= hi:
            self.px = max(lo, min(self.px, hi))
            self.vx = 0.0
        self.moving = abs(self.vx) >= C.WALK_MIN_SPEED

        was_air = not self.on_ground
        self.vy = min(self.vy + C.GRAVITY * (C.FALL_GRAVITY if self.vy > 0 else 1.0), C.MAX_FALL)
        self.py += self.vy
        if self.py >= C.FLOOR_Y:
            self.py = float(C.FLOOR_Y)
            self.vy = 0.0
            self.on_ground = True
            if was_air:
                self.land_t = 6
        else:
            self.on_ground = False
            self.air_t += 1
        if self.land_t:
            self.land_t -= 1

        if self.attack_t:
            self.attack_t += 1
            if seq_frame(self.attack_t, C.SWORD_SEQ) is None:
                self.attack_t = 0
        if self.throw_t:
            self.throw_t += 1
            cur = seq_frame(self.throw_t, C.THROW_SEQ)
            if cur is None:
                self.throw_t = 0
            elif cur[0] == C.THROW_RELEASE and seq_frame(self.throw_t - 1, C.THROW_SEQ)[0] != C.THROW_RELEASE:
                self.release = True
        if self.invincible:
            self.invincible -= 1

        self.walk_t = self.walk_t + 1 if self.moving and self.on_ground else 0
        self.idle_t = self.idle_t + 1 if not self.moving else 0

    def shuriken_spawn(self):
        r = self.rect
        return (r.centerx + self.facing * 14, r.top + 14, self.facing)

    # --- 描画 ---
    def frame_index(self):
        if self.hp <= 0:
            return C.HURT[1]
        if self.hurt_t:
            return C.HURT[0] if self.hurt_t > C.HURT_FRAMES // 2 else C.HURT[1]
        if self.attack_t:
            return seq_frame(self.attack_t, C.SWORD_SEQ)[1]
        if self.throw_t:
            return seq_frame(self.throw_t, C.THROW_SEQ)[1]
        if not self.on_ground:
            if self.air_t < 4:
                return C.JUMP_TAKEOFF
            if self.vy < -2:
                return C.JUMP_RISE
            if self.vy <= 2:
                return C.JUMP_TOP
            return C.JUMP_FALL
        if self.land_t:
            return C.JUMP_LAND
        if self.moving:
            return C.WALK[(self.walk_t // C.WALK_TICKS) % len(C.WALK)]
        return C.IDLE[(self.idle_t // 60) % len(C.IDLE)]

    def draw(self, surface, cam_x):
        if self.invincible and not self.hurt_t and (self.invincible // 4) % 2:
            return  # 無敵中は点滅
        img = self.a.player[self.facing > 0][self.frame_index()]
        r = self.rect
        # 絵の頭の位置を体の中心に合わせる（左向きは反転しているので反対側）
        head = C.HEAD_X if self.facing > 0 else C.FRAME_W - C.HEAD_X
        surface.blit(img, (r.centerx - head - cam_x, r.bottom - C.FRAME_H + 1))


class Enemy:
    """仮の赤い四角。踏んでも倒せない。刀や手裏剣で倒す"""

    def __init__(self, x):
        self.x0 = x
        self.px = float(x)
        self.dir = 1
        self.hp = C.ENEMY_HP
        self.last_swing = 0
        self.alive = True

    @property
    def rect(self):
        return pygame.Rect(round(self.px - C.ENEMY_W / 2), C.FLOOR_Y - C.ENEMY_H, C.ENEMY_W, C.ENEMY_H)

    def update(self):
        self.px += self.dir * C.ENEMY_SPEED
        if abs(self.px - self.x0) > C.ENEMY_PATROL:
            self.dir = -self.dir

    def hit(self, damage=1):
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface, cam_x):
        r = self.rect.move(-cam_x, 0)
        pygame.draw.rect(surface, C.BLACK, r.inflate(2, 2))
        pygame.draw.rect(surface, C.ENEMY, r)
        eye_x = r.centerx + (3 if self.dir > 0 else -5)
        pygame.draw.rect(surface, C.WHITE, (eye_x, r.top + 5, 3, 3))


class Shuriken:
    def __init__(self, x, y, direction, assets):
        self.a = assets
        self.px, self.py = float(x), float(y)
        self.dir = direction
        self.travel = 0.0
        self.t = 0
        self.alive = True

    @property
    def rect(self):
        return pygame.Rect(round(self.px - C.SHURIKEN_W / 2), round(self.py - C.SHURIKEN_H / 2),
                           C.SHURIKEN_W, C.SHURIKEN_H)

    def update(self, stage_w):
        self.px += self.dir * C.SHURIKEN_SPEED
        self.travel += C.SHURIKEN_SPEED
        self.t += 1
        if self.travel > C.SHURIKEN_RANGE or not (0 <= self.px <= stage_w):
            self.alive = False

    def draw(self, surface, cam_x):
        frames = self.a.shuriken
        img = frames[(self.t // C.SHURIKEN_TICKS) % len(frames)]
        surface.blit(img, (round(self.px) - img.get_width() // 2 - cam_x, round(self.py) - img.get_height() // 2))


class HitEffect:
    def __init__(self, x, y, assets):
        self.a = assets
        self.x, self.y = x, y
        self.t = 0
        self.alive = True

    def update(self):
        self.t += 1
        if self.t >= C.HIT_TICKS * len(self.a.hit):
            self.alive = False

    def draw(self, surface, cam_x):
        img = self.a.hit[min(self.t // C.HIT_TICKS, len(self.a.hit) - 1)]
        surface.blit(img, (self.x - img.get_width() // 2 - cam_x, self.y - img.get_height() // 2))
