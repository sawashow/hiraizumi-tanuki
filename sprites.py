"""絵の読み込みと、主人公・敵・手裏剣・命中エフェクトのクラス"""
import math
import os

import pygame

import config as C

IMG = os.path.join(os.path.dirname(__file__), "assets", "images")


def _load(name):
    return pygame.image.load(os.path.join(IMG, name)).convert_alpha()


class Assets:
    """絵をまとめて読み込む。左向き用は反転して持つ"""

    def __init__(self):
        n = 27
        self.player = {True: [_load(f"player_{i:02d}.png") for i in range(n)]}  # True=右向き
        self.player[False] = [pygame.transform.flip(s, True, False) for s in self.player[True]]
        self.shuriken = [_load(f"shuriken_{i:02d}.png") for i in range(4)]
        self.shuriken_left = [pygame.transform.flip(s, True, False) for s in self.shuriken]
        self.hit = [_load(f"hit_{i:02d}.png") for i in range(3)]
        # 敵の絵。種類 → 動き → {右向きか: コマの一覧}
        self.enemy = {}
        for kind, anims in C.ENEMY_FRAMES.items():
            self.enemy[kind] = {}
            for anim, n in anims.items():
                right = [_load(f"enemies/{kind}_{anim}_{i}.png") for i in range(n)]
                self.enemy[kind][anim] = {True: right,
                                          False: [pygame.transform.flip(f, True, False) for f in right]}
        wave = [_load(f"enemies/wave_{i}.png") for i in range(C.WAVE_FRAMES)]
        self.wave = {True: wave, False: [pygame.transform.flip(f, True, False) for f in wave]}   # True=右向き
        slash = [_load(f"slash_{i}.png") for i in range(C.SLASH_FRAMES)]
        self.slash = {True: slash, False: [pygame.transform.flip(f, True, False) for f in slash]}
        self.item = {k: _load(f"items/{k}.png") for k in ("dango", "onigiri", "leaf")}
        self.life_text = {n: _load(f"life_{n}.png") for n in (1, 2, 3, 4)}   # 「のこり 2」など
        self.oneup = _load("oneup.png")
        self.torii = {False: _load("items/torii_off.png"), True: _load("items/torii_on.png")}   # 中間地点（通る前・通った後）
        self.gameover = _load("gameover.png")             # 「無念…」（ドット風フォントで書き出した絵）
        self.gameover_prompt = _load("gameover_prompt.png")  # 「Enterキーで再開」
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
        self.defeat_t = 0   # 倒れてからの経過フレーム（Game が進める）
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
        self.safe_x = float(x)   # 穴に落ちたときに戻る場所（最後に、縁から離れた地面に立っていた位置）
        self.safe_y = float(C.FLOOR_Y)
        self.power = False      # 金の葉で強化中（ダメージを受けると消える）
        self.slash = False      # このフレームに、刀の光波を出す
        self._sword_was_active = False

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
        self.power = False
        self.attack_t = 0
        self.throw_t = 0
        self.vx = C.KNOCKBACK if self.px >= from_x else -C.KNOCKBACK

    # --- 更新 ---
    def update(self, held, stage_w, terrain=None):
        self.release = False
        self.slash = False
        old_px = self.px
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
        # 地面の横の面（壁・穴の縁）にぶつかったら止まる
        if terrain:
            nx = terrain.push_x(old_px, self.px, self.py, C.PLAYER_W / 2)
            if nx != self.px:
                self.px = nx
                self.vx = 0.0
        self.moving = abs(self.vx) >= C.WALK_MIN_SPEED

        was_air = not self.on_ground
        self.vy = min(self.vy + C.GRAVITY * (C.FALL_GRAVITY if self.vy > 0 else 1.0), C.MAX_FALL)
        new_bottom = self.py + self.vy
        if terrain is None:
            surface = (C.FLOOR_Y, True) if new_bottom >= C.FLOOR_Y else None
        else:
            surface = terrain.support(self.px, self.py, new_bottom) if self.vy >= 0 else None
        if surface is not None:
            height, is_ground = surface
            self.py = float(height)
            self.vy = 0.0
            self.on_ground = True
            if was_air:
                self.land_t = 6
            if terrain and is_ground and terrain.safe_spot(self.px, height):
                self.safe_x, self.safe_y = self.px, float(height)
        else:
            self.py = new_bottom
            self.on_ground = False
            self.air_t += 1
        if self.land_t:
            self.land_t -= 1
        if self.py > C.FALL_Y and self.hp > 0:
            self._fall_into_pit()

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
        active = self.sword_rect() is not None
        if self.power and active and not self._sword_was_active:
            self.slash = True
        self._sword_was_active = active
        if self.invincible:
            self.invincible -= 1

        self.walk_t = self.walk_t + 1 if self.moving and self.on_ground else 0
        self.idle_t = self.idle_t + 1 if not self.moving else 0

    def _fall_into_pit(self):
        """穴に落ちた: ダメージを受けて、最後に立っていた地面へ戻る（体力が尽きたらゲームオーバー）"""
        self.hp = max(0, self.hp - C.FALL_DAMAGE)
        self.power = False
        if self.hp <= 0:
            return
        self.px = float(self.safe_x)
        self.py = self.safe_y
        self.vx = self.vy = 0.0
        self.on_ground = True
        self.attack_t = self.throw_t = 0
        self.invincible = C.INVINCIBLE_FRAMES

    def slash_spawn(self):
        r = self.rect
        return (r.centerx + self.facing * 18, r.centery - 2, self.facing)

    def shuriken_spawn(self):
        r = self.rect
        return (r.centerx + self.facing * 14, r.top + 14, self.facing)

    # --- 描画 ---
    def frame_index(self):
        if self.hp <= 0:
            f = seq_frame(self.defeat_t, C.DEFEAT_SEQ)
            return f[1] if f else C.DEFEAT_END
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
    """ザコ敵の共通部分。当たり判定・体力・被弾の点滅と硬直・やられの動き。動きは think() を種類ごとに作る"""

    P = {}       # 種類ごとの設定（config）
    KIND = ""    # 絵の種類名
    DEATH_TICKS = 8   # やられの1コマの長さ

    def __init__(self, x, y=None, assets=None):
        P = self.P
        self.a = assets
        self.w, self.h = P["w"], P["h"]
        self.max_hp = self.hp = P["hp"]
        self.cx = float(x)
        self.cy = float(y if y is not None else C.FLOOR_Y - self.h / 2)   # 中心の高さ
        self.facing = -1
        self.t = 0
        self.flash = 0
        self.stun = 0
        self.last_swing = 0
        self.alive = True       # やられの動きが終わるまで True
        self.dying = False
        self.dead_t = 0

    @property
    def active(self):
        """攻撃を受ける・ダメージを与える状態（やられの動き中は、どちらもしない）"""
        return self.alive and not self.dying

    @property
    def rect(self):
        return pygame.Rect(round(self.cx - self.w / 2), round(self.cy - self.h / 2), self.w, self.h)

    def update(self, player_rect, stage_w, terrain=None):
        self.t += 1
        if self.dying:
            self.dead_t += 1
            if self.dead_t >= self.DEATH_TICKS * len(self.a.enemy[self.KIND]["death"][True]):
                self.alive = False
            return
        if self.flash:
            self.flash -= 1
        if self.stun:
            self.stun -= 1
            return
        self.think(player_rect, stage_w, terrain)

    def think(self, player_rect, stage_w, terrain=None):
        pass

    def hit(self, damage=1):
        if self.dying:
            return
        self.hp -= damage
        self.flash = C.HIT_FLASH
        self.stun = C.HIT_STUN
        if self.hp <= 0:
            self.dying = True
            self.dead_t = 0

    def image(self):
        """いま表示するコマ（種類ごとに決める）。絵がなければ None"""
        return None

    def draw(self, surface, cam_x):
        r = self.rect.move(-cam_x, 0)
        img = self.image() if self.a else None
        if img is None:   # 絵がないときの仮の四角
            pygame.draw.rect(surface, C.BLACK, r.inflate(2, 2))
            pygame.draw.rect(surface, (168, 0, 32), r)
            return
        if self.flash:   # 攻撃を受けた直後は、白いシルエットにする
            img = pygame.mask.from_surface(img).to_surface(setcolor=C.WHITE, unsetcolor=(0, 0, 0, 0))
        art = C.ENEMY_ART[self.KIND]
        y = r.bottom - art["h"] if art["mode"] == "bottom" else r.centery - art["ay"]
        surface.blit(img, (r.centerx - art["ax"], y))

    def _frames(self, anim):
        return self.a.enemy[self.KIND][anim][self.facing > 0]


class Ochimusha(Enemy):
    """落ち武者: 地面を歩いて近づく。近づくと一度止まって構える。体力3"""
    P = C.OCHI
    KIND = "ochimusha"
    DEATH_TICKS = 8

    def __init__(self, x, assets=None, floor=None):
        self.floor = float(floor if floor is not None else C.FLOOR_Y)   # 立っている地面の高さ
        super().__init__(x, y=self.floor - C.OCHI["h"] / 2, assets=assets)
        self.x0 = float(x)
        self.ready_t = 0
        self.swing_t = 0
        self.turn_t = 0     # 端で折り返して歩く残りフレーム
        self.cool = 0
        self.patrol_dir = 1
        self.spawned = []   # 出した光波（Game が受け取って動かす）

    def think(self, pr, stage_w, terrain=None):
        P = self.P
        dx = pr.centerx - self.cx
        self.facing = 1 if dx > 0 else -1
        if self.cool:
            self.cool -= 1
        if self.ready_t:
            self.ready_t -= 1       # 構えている間は止まる
            if not self.ready_t:
                self.swing_t = P["swing_frames"]
            return
        if self.swing_t:            # 刀を振る。振り下ろした瞬間に光波が出て、そのあとは隙になる
            self.swing_t -= 1
            if self.swing_t == P["swing_frames"] - P["wave_at"]:
                self.spawned.append(Wave(self.cx + self.facing * 24, self.cy + self.h / 2 + C.WAVE["dy"],
                                         self.facing, self.a))
            return
        if self.turn_t:             # 端（穴・段差）まで来たので、反対側へ歩く。端から端まで往復する
            self.turn_t -= 1
            self.facing = self.patrol_dir
            if not self._step(self.patrol_dir * P["speed"], terrain):
                self.patrol_dir = -self.patrol_dir
            return
        if abs(dx) <= P["active"]:
            if abs(dx) < P["ready_dist"] and not self.cool:
                self.ready_t = P["ready_frames"]
                self.cool = P["cooldown"]
                return
            if not self._step(self.facing * P["speed"], terrain):
                self.turn_t = P["turn_frames"]      # 進めない（端に来た）: 折り返す
                self.patrol_dir = -self.facing
        else:
            moved = self._step(self.patrol_dir * P["speed"] * 0.5, terrain)
            if not moved or abs(self.cx - self.x0) > P["patrol"]:
                self.patrol_dir = -self.patrol_dir

    def _step(self, dx, terrain):
        """横に進む。足元に地面がなければ（穴の縁）、進まない"""
        nx = self.cx + dx
        if terrain:   # 体の中心が、同じ高さの地面の上にあるうちだけ進む（穴・段差の手前で止まる）
            h = terrain.height_at(nx)
            if h is None or abs(h - self.floor) > 1:
                return False
        self.cx = nx
        return True

    def image(self):
        if self.dying:
            f = self._frames("death")
            return f[min(self.dead_t // self.DEATH_TICKS, len(f) - 1)]
        if self.swing_t:
            f = self._frames("swing")
            return f[0 if self.P["swing_frames"] - self.swing_t < self.P["wave_at"] else 1]
        if self.ready_t:
            f = self._frames("stance")
            done = self.P["ready_frames"] - self.ready_t
            return f[min(done * len(f) // self.P["ready_frames"], len(f) - 1)]
        f = self._frames("walk")
        return f[(self.t // 10) % len(f)]


class Kitsunebi(Enemy):
    """狐火: 空中を上下に揺れながら横に進む。近づくと動き出し、主人公のいる側へ向かう。体力1"""
    P = C.KITSUNEBI
    KIND = "kitsunebi"
    DEATH_TICKS = 6

    def __init__(self, x, level="low", assets=None):
        super().__init__(x, C.KITSUNEBI[level], assets)
        self.base_y = self.cy
        self.dir = 0

    def think(self, pr, stage_w, terrain=None):
        P = self.P
        dx = pr.centerx - self.cx
        if not self.dir:
            if abs(dx) > P["active"]:
                return
            self.dir = 1 if dx > 0 else -1     # 動き出したときの向きで、まっすぐ進む
            self.t = 0
        self.facing = self.dir
        self.cx += self.dir * P["speed"]
        self.cy = self.base_y + P["bob"] * math.sin(self.t * 2 * math.pi / P["period"])
        if self.cx < -40 or self.cx > stage_w + 40:
            self.alive = False

    def image(self):
        if self.dying:
            f = self._frames("death")
            return f[min(self.dead_t // self.DEATH_TICKS, len(f) - 1)]
        f = self._frames("flicker")
        return f[(self.t // 8) % len(f)]


class Karasu(Enemy):
    """烏: 空中で待ち、近づくと羽ばたいて予告し、そのときの主人公の位置へ急降下して通り過ぎる。体力1"""
    P = C.KARASU
    KIND = "karasu"
    DEATH_TICKS = 10

    def __init__(self, x, assets=None):
        super().__init__(x, C.KARASU["height"], assets)
        self.state = "wait"
        self.vx = self.vy = 0.0

    def think(self, pr, stage_w, terrain=None):
        P = self.P
        dx = pr.centerx - self.cx
        if self.state == "wait":
            self.facing = 1 if dx > 0 else -1
            if abs(dx) <= P["active"]:
                self.state = "telegraph"
                self.t = 0
        elif self.state == "telegraph":
            self.facing = 1 if dx > 0 else -1
            if self.t >= P["telegraph"]:
                tx, ty = pr.centerx - self.cx, pr.centery - self.cy
                n = math.hypot(tx, ty) or 1.0
                self.vx, self.vy = tx / n * P["speed"], ty / n * P["speed"]   # この瞬間の位置へ向かう
                self.state = "dive"
        else:
            self.cx += self.vx
            self.cy += self.vy
            h = terrain.height_at(self.cx) if terrain else None
            floor = (C.FLOOR_Y if h is None else h) - self.h / 2
            if self.cy > floor:      # 地面すれすれを、横に通り過ぎる
                self.cy = floor
                self.vy = 0.0
            self.facing = 1 if self.vx > 0 else -1
            if self.cx < -60 or self.cx > stage_w + 60:
                self.alive = False

    def image(self):
        if self.dying:
            f = self._frames("death")
            return f[min(self.dead_t // self.DEATH_TICKS, len(f) - 1)]
        if self.state == "dive":
            f = self._frames("dive")
            return f[(self.t // 6) % len(f)]
        f = self._frames("flap")
        step = 5 if self.state == "telegraph" else 14   # 予告のときは、速く羽ばたく
        return f[(self.t // step) % len(f)]


def make_enemy(kind, x, assets=None, terrain=None):
    """配置表の名前から敵を作る（地上の敵は、そこにある地面の上に立つ）"""
    if kind == "ochimusha":
        return Ochimusha(x, assets, terrain.height_at(x) if terrain else None)
    if kind == "kitsunebi_low":
        return Kitsunebi(x, "low", assets)
    if kind == "kitsunebi_high":
        return Kitsunebi(x, "high", assets)
    if kind == "karasu":
        return Karasu(x, assets)
    raise ValueError(kind)


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


class Wave:
    """落ち武者の光波。まっすぐ飛んで、一定の距離で消える"""

    def __init__(self, x, y, direction, assets):
        self.a = assets
        self.px, self.py = float(x), float(y)
        self.dir = direction
        self.travel = 0.0
        self.t = 0
        self.alive = True

    @property
    def rect(self):
        w, h = C.WAVE["w"], C.WAVE["h"]
        return pygame.Rect(round(self.px - w / 2), round(self.py - h / 2), w, h)

    def update(self, stage_w):
        self.px += self.dir * C.WAVE["speed"]
        self.travel += C.WAVE["speed"]
        self.t += 1
        if self.travel > C.WAVE["range"] or not (0 <= self.px <= stage_w):
            self.alive = False

    def draw(self, surface, cam_x):
        frames = self.a.wave[self.dir > 0]
        img = frames[(self.t // C.WAVE["ticks"]) % len(frames)]
        surface.blit(img, (round(self.px) - img.get_width() // 2 - cam_x, round(self.py) - img.get_height() // 2))


class SlashWave:
    """強化中の、刀の光波。敵に当たると消える"""

    def __init__(self, x, y, direction, assets):
        self.a = assets
        self.px, self.py = float(x), float(y)
        self.dir = direction
        self.travel = 0.0
        self.t = 0
        self.alive = True

    @property
    def rect(self):
        w, h = C.SLASH["w"], C.SLASH["h"]
        return pygame.Rect(round(self.px - w / 2), round(self.py - h / 2), w, h)

    def update(self, stage_w):
        self.px += self.dir * C.SLASH["speed"]
        self.travel += C.SLASH["speed"]
        self.t += 1
        if self.travel > C.SLASH["range"] or not (0 <= self.px <= stage_w):
            self.alive = False

    def draw(self, surface, cam_x):
        frames = self.a.slash[self.dir > 0]
        img = frames[(self.t // C.SLASH["ticks"]) % len(frames)]
        surface.blit(img, (round(self.px) - img.get_width() // 2 - cam_x, round(self.py) - img.get_height() // 2))


class Item:
    """拾えるもの。dango=スコア / onigiri=回復 / leaf=強化。絵ができるまでは、色付きの図形で描く"""

    def __init__(self, kind, x, y, assets=None, idx=-1):
        self.kind = kind
        self.idx = idx   # 配置表の何番目か（やられて再開するとき、取ったものを覚えておく）
        self.a = assets
        self.cx, self.cy = float(x), float(y)
        self.t = 0
        self.alive = True

    @property
    def rect(self):
        s = C.ITEM_SIZE
        return pygame.Rect(round(self.cx - s / 2), round(self.cy - s / 2), s, s)

    def update(self):
        self.t += 1

    def draw(self, surface, cam_x):
        x = round(self.cx) - cam_x
        y = round(self.cy + math.sin(self.t / 18) * 2)
        imgs = getattr(self.a, "item", None) if self.a else None
        if imgs and self.kind in imgs:
            img = imgs[self.kind]
            surface.blit(img, (x - img.get_width() // 2, y - img.get_height() // 2))
            return
        if self.kind == "dango":
            pygame.draw.circle(surface, C.BLACK, (x, y), 6)
            pygame.draw.circle(surface, (248, 168, 192), (x, y), 5)
            pygame.draw.circle(surface, (252, 232, 240), (x - 2, y - 2), 2)
        elif self.kind == "onigiri":
            pts = [(x, y - 7), (x + 7, y + 6), (x - 7, y + 6)]
            pygame.draw.polygon(surface, C.BLACK, pts)
            pygame.draw.polygon(surface, (252, 252, 252), [(x, y - 4), (x + 4, y + 4), (x - 4, y + 4)])
            pygame.draw.rect(surface, (24, 40, 32), (x - 4, y + 2, 8, 3))
        else:
            pts = [(x, y - 8), (x + 6, y), (x, y + 8), (x - 6, y)]
            pygame.draw.polygon(surface, C.BLACK, pts)
            pygame.draw.polygon(surface, (252, 208, 40), [(x, y - 5), (x + 3, y), (x, y + 5), (x - 3, y)])


class Checkpoint:
    """中間地点（鳥居）。通ると、やられたとき、ここから再開する。絵ができるまでは、図形で描く"""

    def __init__(self, x, y, assets=None):
        self.a = assets
        self.x, self.y = x, y     # y は足元
        self.active = False

    @property
    def rect(self):
        return pygame.Rect(self.x - C.CHECKPOINT_W // 2, self.y - 40, C.CHECKPOINT_W, 40)

    def draw(self, surface, cam_x):
        x, y = self.x - cam_x, self.y
        if self.a:
            img = self.a.torii[self.active]
            surface.blit(img, (x - img.get_width() // 2, y - img.get_height() + 1))
            return
        post = (200, 36, 36) if self.active else (110, 70, 70)
        for px in (x - 10, x + 7):
            pygame.draw.rect(surface, C.BLACK, (px - 1, y - 37, 6, 38))
            pygame.draw.rect(surface, post, (px, y - 36, 4, 36))
        pygame.draw.rect(surface, C.BLACK, (x - 15, y - 41, 31, 8))
        pygame.draw.rect(surface, post, (x - 14, y - 40, 29, 5))
        pygame.draw.rect(surface, C.BLACK, (x - 11, y - 30, 23, 4))
        pygame.draw.rect(surface, post, (x - 10, y - 29, 21, 2))


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
