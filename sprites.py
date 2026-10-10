"""絵の読み込みと、主人公・敵・手裏剣・命中エフェクトのクラス"""
import math
import os

import pygame

import config as C

IMG = os.path.join(os.path.dirname(__file__), "assets", "images")


def _load(name):
    return pygame.image.load(os.path.join(IMG, name)).convert_alpha()


def _boss_frame(img):
    big = pygame.transform.scale(img, (img.get_width() * 2, img.get_height() * 2))
    big.fill((70, 10, 0), special_flags=pygame.BLEND_RGB_ADD)
    return big


def _triple_icon(shuriken):
    icon = pygame.Surface((C.ITEM_SIZE, C.ITEM_SIZE), pygame.SRCALPHA)
    small = pygame.transform.scale(shuriken, (10, 10))
    for x, y in ((0, 3), (6, 0), (6, 6)):   # 手裏剣を3つ、扇の形に
        icon.blit(small, (x, y))
    return icon


def _star_icon():
    s = C.ITEM_SIZE
    icon = pygame.Surface((s, s), pygame.SRCALPHA)
    c = s / 2
    for r_out, r_in, color in ((8.0, 3.6, C.BLACK), (6.2, 2.6, (252, 208, 40)), (3.4, 1.4, (255, 248, 176))):
        pts = [(c + (r_out if k % 2 == 0 else r_in) * math.sin(k * math.pi / 5),
                c - (r_out if k % 2 == 0 else r_in) * math.cos(k * math.pi / 5)) for k in range(10)]
        pygame.draw.polygon(icon, color, pts)
    return icon


def draw_zzz(surface, x, y, t):
    """眠っている印: 「Z」が3つ、ひとつずつ浮かんで上がっていく。(x, y) は出どころ、t は眠ってからのフレーム数"""
    for n in range(3):
        if t / 90 < n * 0.33:
            continue
        u = (t / 90 - n * 0.33) % 1.0
        s = 3 + round(u * 4)
        pts = [(2, 2), (2 + s, 2), (2, 2 + s), (2 + s, 2 + s)]
        z = pygame.Surface((s + 5, s + 5), pygame.SRCALPHA)
        pygame.draw.lines(z, C.BLACK, False, pts, 3)
        pygame.draw.lines(z, (200, 220, 255), False, pts, 1)
        z.set_alpha(round(255 * min(1.0, (1 - u) * 2.5)))
        surface.blit(z, (x + round(u * 16) - 2, y - round(u * 26) - 2))


def _sword_trail():
    """刀を振った勢いの軌跡: 右向きの三日月（外側が青白く、内側が白い）"""
    w, h = C.SWORD_TRAIL + 8, C.SWORD_H + 4
    img = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(img, (150, 180, 255), (-w, 0, w * 2, h))
    pygame.draw.ellipse(img, (255, 255, 255), (-w, 2, w * 2 - 3, h - 4))
    pygame.draw.ellipse(img, (0, 0, 0, 0), (-w - 7, -1, w * 2, h + 2))     # 内側をくり抜いて、三日月にする
    return img


class Assets:
    """絵をまとめて読み込む。左向き用は反転して持つ"""

    def __init__(self):
        n = 37
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
        # ボスの絵（仮）: 落ち武者を2倍にして、赤みを足したもの。絵ができたら、差し替える
        self.enemy["boss"] = {anim: {d: [_boss_frame(f) for f in fs] for d, fs in dirs.items()}
                              for anim, dirs in self.enemy["ochimusha"].items()}
        self.boss_title = _load(C.BOSS_TITLE)
        self.boss_name = _load(C.BOSS_NAME)
        wave = [_load(f"enemies/wave_{i}.png") for i in range(C.WAVE_FRAMES)]
        self.wave = {True: wave, False: [pygame.transform.flip(f, True, False) for f in wave]}   # True=右向き
        slash = [_load(f"slash_{i}.png") for i in range(C.SLASH_FRAMES)]
        self.slash = {True: slash, False: [pygame.transform.flip(f, True, False) for f in slash]}
        self.item = {k: _load(f"items/{k}.png") for k in ("dango", "onigiri", "leaf")}
        # 三方手裏剣・スーパータヌキの絵（仮）: 手裏剣の絵を縮めたものと、図形で描いた星。絵ができたら、差し替える
        self.item["triple"] = _triple_icon(self.shuriken[0])
        self.item["super"] = _star_icon()
        self.cp_text = _load("checkpoint_text.png")   # 「中間地点」
        self.talk_boss = _load(C.TALK_BOSS)       # 寸劇のせりふ（吹き出しの中の字）
        self.talk_tanuki = _load(C.TALK_TANUKI)
        self.life_text = {n: _load(f"life_{n}.png") for n in (1, 2, 3, 4)}   # 「のこり 2」など
        self.oneup = _load("oneup.png")
        self.torii = {False: _load("items/torii_off.png"), True: _load("items/torii_on.png")}   # 中間地点（通る前・通った後）
        self.title_logo = _load("title_logo.png")       # 題名「平泉 タヌキ侍」（昔のゲームのロゴ風）
        self.title_prompt = _load("title_prompt.png")   # 「PUSH ENTER KEY」
        # スタート画面の絵（無ければ、1面の景色で代わりにする）
        self.title_bg = _load(C.TITLE_BG) if os.path.exists(os.path.join(IMG, C.TITLE_BG)) else None
        self.story = _load("story_intro.png")           # 始まりの語り（縦に長い1枚）
        trail = _sword_trail()
        self.sword_trail = {True: trail, False: pygame.transform.flip(trail, True, False)}   # True=右向き
        self.story_tanuki = [_load(f"story/tanuki_{i:02d}.png") for i in range(11)]   # 語りの画面のタヌキ侍（居眠りは、ゲーム中にも使う）
        self.story_tanuki_left = [pygame.transform.flip(f, True, False) for f in self.story_tanuki]
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
        self.triple = False     # 三方手裏剣（ダメージを受けると消える）
        self.super_t = 0        # スーパータヌキの残りフレーム
        self.slash = False      # このフレームに、刀の光波を出す
        self.crouch = False     # しゃがんでいる（地上で、下を押している間）
        self.crouch_act = False  # いまの刀・手裏剣は、しゃがんで始めた（終わるまで、しゃがんだまま）
        self.rest_t = 0         # 何もしないで立っているフレーム数（長くなると、あくびをして眠る）
        self.startle_t = 0      # 驚いて跳ねている残りフレーム（ボスが降ってきたとき）
        self.jump_q = 0         # ジャンプを覚えている残りフレーム
        self.jump_boost = False  # このフレームに跳んだ（左右を押していれば、横の速さを足す）
        self.jumped = False     # 跳んで空中にいる（足場から落ちただけなら False）
        self.fall_t = 0         # 地面を離れてからのフレーム数
        self.queued = None      # 動作の途中で押された、次の動作（"attack" か "throw"）
        self.queue_t = 0        # それを覚えている残りフレーム
        self._sword_was_active = False

    # --- 当たり判定 ---
    @property
    def rect(self):
        h = C.CROUCH_H if self.crouch else C.PLAYER_H
        return pygame.Rect(round(self.px - C.PLAYER_W / 2), round(self.py - h), C.PLAYER_W, h)

    def sword_rect(self):
        """振り下ろしのコマの間だけ、向いている側に出る"""
        if not self.attack_t:
            return None
        cur = seq_frame(self.attack_t, C.SWORD_SEQ)
        if cur is None or cur[0] != C.SWORD_ACTIVE:
            return None
        r = self.rect
        top = r.top + 2
        w = C.SWORD_W + C.SWORD_TRAIL    # 刀と、その先の軌跡
        if self.facing > 0:
            return pygame.Rect(r.right, top, w, C.SWORD_H)
        return pygame.Rect(r.left - w, top, w, C.SWORD_H)

    # --- 操作 ---
    @property
    def busy(self):
        return bool(self.attack_t or self.throw_t or self.hurt_t)

    @property
    def recovering(self):
        """刀・手裏剣の、出し終わったあとの隙（最後のコマ）。この間は、別の動作（歩く・跳ぶ・しゃがむ、刀なら手裏剣、手裏剣なら刀）で
        打ち切れる。同じ動作では打ち切れない（刀の連打・手裏剣の連打は、隙が終わるまで出ない）"""
        a = seq_frame(self.attack_t, C.SWORD_SEQ) if self.attack_t else None
        t = seq_frame(self.throw_t, C.THROW_SEQ) if self.throw_t else None
        return bool((a and a[0] == len(C.SWORD_SEQ) - 1) or (t and t[0] == len(C.THROW_SEQ) - 1))

    def _cancel(self):
        if self.recovering and not self.hurt_t:
            self.attack_t = self.throw_t = 0

    def jump(self):
        """跳ぶ。いまは跳べなくても、少しのあいだ覚えておく（着地の直前、振り終わりの直前に押しても、跳べる）"""
        if not self._try_jump():
            self.jump_q = C.JUMP_BUFFER

    def _try_jump(self):
        self._cancel()
        late = not self.on_ground and not self.jumped and self.fall_t <= C.COYOTE   # 縁から出た直後
        if (self.on_ground or late) and not self.busy and self.hp > 0:
            self.vy = C.JUMP_SPEED
            self.on_ground = False
            self.air_t = 0
            self.jump_cut_done = False
            self.jumped = True
            self.jump_boost = True
            self.jump_q = 0
            return True
        return False

    def cut_jump(self):
        """ジャンプボタンを早く離したとき、上昇を弱める（押し続けるほど高く跳ぶ）"""
        if not self.on_ground and not self.jump_cut_done and self.vy < C.JUMP_CUT_MIN:
            self.vy *= C.JUMP_CUT
            self.jump_cut_done = True

    def attack(self):
        if self.throw_t:        # 手裏剣の隙は、刀で打ち切れる（刀の隙は、刀では打ち切れない）
            self._cancel()
        if not self.busy and self.hp > 0:
            self.attack_t = 1
            self.swing_id += 1
            self.crouch_act = self.crouch
            self.queued = None
        elif self.attack_t or self.throw_t:    # 前の動作の途中で押した: 覚えておいて、終わったらすぐ出す
            self.queued, self.queue_t = "attack", C.INPUT_BUFFER

    def throw(self):
        if self.attack_t:
            self._cancel()
        if not self.busy and self.hp > 0:
            self.throw_t = 1
            self.crouch_act = self.crouch
            self.queued = None
        elif self.attack_t or self.throw_t:
            self.queued, self.queue_t = "throw", C.INPUT_BUFFER

    @property
    def untouchable(self):
        """敵や光波に当たっても、ダメージを受けない（無敵時間か、スーパータヌキ）"""
        return bool(self.invincible or self.super_t)

    def take_damage(self, from_x, amount=1):
        if self.untouchable or self.hp <= 0:
            return
        self.hp -= amount
        self.invincible = C.INVINCIBLE_FRAMES
        self.hurt_t = C.HURT_FRAMES
        self.power = self.triple = False
        self.attack_t = 0
        self.throw_t = 0
        self.vx = C.KNOCKBACK if self.px >= from_x else -C.KNOCKBACK

    # --- 更新 ---
    def update(self, held, stage_w, terrain=None):
        self.release = False
        self.slash = False
        self.startle_t = max(0, self.startle_t - 1)
        old_px = self.px
        direction = ("right" in held) - ("left" in held)
        boost = C.SUPER_SPEED if self.super_t else 1.0   # スーパータヌキの間は、速い
        top = C.MAX_SPEED * boost
        if self.super_t:
            self.super_t -= 1
        if self.jump_q:
            self.jump_q -= 1
            self._try_jump()
        if self.recovering and (direction or ("down" in held) != self.crouch_act):
            self._cancel()      # 隙は、歩く・向きを変える・しゃがむ（立つ）で打ち切れる
        # しゃがみ: 地上で、下を押している間。しゃがんで始めた刀・手裏剣は、終わるまでしゃがんだまま（立って始めたら、立ったまま）
        acting = bool(self.attack_t or self.throw_t)
        self.crouch = (self.on_ground and self.hp > 0 and not self.hurt_t
                       and (self.crouch_act if acting else "down" in held))
        if self.hp <= 0 or self.hurt_t:
            if self.hurt_t:
                self.hurt_t -= 1
            self.vx = _approach(self.vx, 0.0, C.FRICTION)   # のけぞり・倒れている間は操作を受けない
        elif self.on_ground:
            if self.attack_t or self.throw_t:
                if direction and 1 in (self.attack_t, self.throw_t) and not self.crouch:
                    self.facing = direction     # 出した瞬間だけは、押している向きへ向く（振り向きながら出せる）
                if direction == self.facing and not self.crouch:
                    # 向いているほうを押し続けていれば、止まらずに、少し遅く進み続ける（振り終わりから、そのまま走りにつながる）
                    self.vx = _approach(self.vx, direction * top * C.ATTACK_MOVE, C.FRICTION)
                else:
                    self.vx = _approach(self.vx, 0.0, C.FRICTION)   # 押していなければ、勢いのまま滑って止まる（向きは変えられない）
            elif self.crouch:
                self.vx = _approach(self.vx, 0.0, C.FRICTION)   # しゃがんでいる間は歩けない（向きは変えられる）
                if direction:
                    self.facing = direction
            elif direction == 0:
                self.vx = _approach(self.vx, 0.0, C.FRICTION)
            elif self.vx * direction < 0:
                self.vx = _approach(self.vx, 0.0, C.TURN_DECEL)  # 逆向きに押したら、まず減速（すべる）
            else:
                self.vx = _approach(self.vx, direction * top, C.ACCEL * boost)
            # 向きは、押した瞬間に変える（体は少しすべるが、すぐ次の動作を、その向きで出せる）
            if direction and not (self.attack_t or self.throw_t or self.crouch):
                self.facing = direction
        else:
            # 空中は、攻撃中でも向きを変えられる。加速は緩く、離しても勢いはほぼ保つ
            if self.jump_boost and direction and self.vx * direction < top * C.JUMP_START:
                self.vx = direction * top * C.JUMP_START    # 跳んだ瞬間: 押しているほうへ、すぐ横の速さを持つ
            if direction:
                self.vx = _approach(self.vx, direction * top, C.AIR_ACCEL * boost)
                self.facing = direction
            else:
                self.vx = _approach(self.vx, 0.0, C.AIR_FRICTION)
        self.jump_boost = False
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
            self.jumped = False
            self.fall_t = 0
            if was_air:
                self.land_t = 6
            if terrain and is_ground and terrain.safe_spot(self.px, height):
                self.safe_x, self.safe_y = self.px, float(height)
        else:
            self.py = new_bottom
            self.on_ground = False
            self.air_t += 1
            self.fall_t += 1
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
        if self.queued:     # 覚えておいた動作: 前の動作が終わったら、すぐ出す（時間が切れたら、忘れる）
            self.queue_t -= 1
            if self.queue_t <= 0 or self.hurt_t or self.hp <= 0:
                self.queued = None
            elif not self.busy or (self.recovering and bool(self.attack_t) != (self.queued == "attack")):
                self.attack() if self.queued == "attack" else self.throw()
        active = self.sword_rect() is not None
        if self.power and active and not self._sword_was_active:
            self.slash = True
        self._sword_was_active = active
        if self.invincible:
            self.invincible -= 1

        resting = self.on_ground and not held and not self.busy and not self.moving and self.hp > 0
        self.rest_t = self.rest_t + 1 if resting else 0
        self.walk_t = self.walk_t + 1 if self.moving and self.on_ground else 0
        self.idle_t = self.idle_t + 1 if not self.moving else 0

    def _fall_into_pit(self):
        """穴に落ちた: ダメージを受けて、最後に立っていた地面へ戻る（体力が尽きたらゲームオーバー）"""
        self.hp = max(0, self.hp - C.FALL_DAMAGE)
        self.power = self.triple = False
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
    def rest_frame(self):
        """何もしないで立っているときの、居眠りの絵の番号（まだ起きているなら None）。あくび → うとうと → 座る → 眠る"""
        R = C.REST
        t = self.rest_t - R["start"]
        if t < 0:
            return None
        for frame, length in ((1, R["yawn"]), (2, R["drowsy"]), (3, R["sit"])):
            if t < length:
                return frame
            t -= length
        return C.STORY_SLEEP_SEQ[(t // R["breath"]) % len(C.STORY_SLEEP_SEQ)]

    @property
    def asleep(self):
        R = C.REST
        return self.rest_t >= R["start"] + R["yawn"] + R["drowsy"] + R["sit"]

    def frame_index(self):
        if self.hp <= 0:
            f = seq_frame(self.defeat_t, C.DEFEAT_SEQ)
            return f[1] if f else C.DEFEAT_END
        if self.hurt_t:
            return C.HURT[0] if self.hurt_t > C.HURT_FRAMES // 2 else C.HURT[1]
        if self.attack_t:
            return seq_frame(self.attack_t, C.CROUCH_SWORD_SEQ if self.crouch else C.SWORD_SEQ)[1]
        if self.throw_t:
            return seq_frame(self.throw_t, C.CROUCH_THROW_SEQ if self.crouch else C.THROW_SEQ)[1]
        if self.crouch:
            return C.CROUCH[(self.idle_t // 60) % len(C.CROUCH)]
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
        if self.invincible and not self.super_t and not self.hurt_t and (self.invincible // 4) % 2:
            return  # 無敵中は点滅
        if self.startle_t and self.on_ground:    # 驚く: 目を見開いて、小さく跳ねる。頭の上に「！」（語りの画面の、飛び起きる絵）
            right = self.facing > 0
            u = 1 - self.startle_t / C.STARTLE
            dy = -round(8 * math.sin(min(1.0, u / 0.6) * math.pi))
            img = (self.a.story_tanuki if right else self.a.story_tanuki_left)[8]
            head = C.STORY_TANUKI["head_x"] if right else img.get_width() - C.STORY_TANUKI["head_x"]
            r = self.rect
            surface.blit(img, (r.centerx - head - cam_x, r.bottom - img.get_height() + 1 + dy))
            bx, by = r.centerx - cam_x + (2 if right else -5), r.bottom - 58 + dy
            for rect in ((bx, by, 3, 7), (bx, by + 9, 3, 3)):
                pygame.draw.rect(surface, C.BLACK, pygame.Rect(rect).inflate(2, 2))
                pygame.draw.rect(surface, (252, 208, 40), rect)
            return
        rest = self.rest_frame()
        if rest is not None:    # 居眠り（語りの画面と同じ絵。枠の大きさと、頭の位置が違う）
            right = self.facing > 0
            img = (self.a.story_tanuki if right else self.a.story_tanuki_left)[rest]
            head = C.STORY_TANUKI["head_x"] if right else img.get_width() - C.STORY_TANUKI["head_x"]
            r = self.rect
            surface.blit(img, (r.centerx - head - cam_x, r.bottom - img.get_height() + 1))
            if self.asleep:
                R = C.REST
                draw_zzz(surface, r.centerx - cam_x + self.facing * 14 - (0 if right else 8), r.bottom - 30,
                         self.rest_t - R["start"] - R["yawn"] - R["drowsy"] - R["sit"])
            return
        img = self.a.player[self.facing > 0][self.frame_index()]
        if self.super_t:   # スーパータヌキ: 体が、色を変えながら光る（切れそうになると、ゆっくり点滅）
            warn = self.super_t < C.SUPER_WARN
            if not warn or (self.super_t // 6) % 2:
                img = img.copy()
                img.fill(((110, 90, 0), (0, 70, 110), (110, 30, 70))[(self.super_t // 4) % 3], special_flags=pygame.BLEND_RGB_ADD)
        r = self.rect
        # 絵の頭の位置を体の中心に合わせる（左向きは反転しているので反対側）
        head = C.HEAD_X if self.facing > 0 else C.FRAME_W - C.HEAD_X
        surface.blit(img, (r.centerx - head - cam_x, r.bottom - C.FRAME_H + 1))
        sword = self.sword_rect()
        if sword:   # 刀を振った勢いの軌跡: 刀の先に、三日月の光が出て、すっと消える
            start = sum(d for _, d in C.SWORD_SEQ[:C.SWORD_ACTIVE])
            u = (self.attack_t - start) / C.SWORD_SEQ[C.SWORD_ACTIVE][1]
            trail = self.a.sword_trail[self.facing > 0]
            trail.set_alpha(max(0, round(255 * (1 - u * 0.8))))
            push = round(u * 4)     # 少しだけ、前へ押し出される
            x = sword.right - trail.get_width() + push if self.facing > 0 else sword.left - push
            surface.blit(trail, (x - cam_x, sword.centery - trail.get_height() // 2))


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


class Boss(Enemy):
    """ボス（1面は、藤原泰衡。見た目は、落ち武者）。上から降ってきて、「歩く → 構えて光波」を2回、「かがんで跳びかかる」を1回、と繰り返す。
    攻撃のあとに隙がある。攻撃を受けても、ひるまない。体力が半分になると、歩く時間と隙が短くなる"""
    P = C.BOSS
    KIND = "boss"
    DEATH_TICKS = 16

    INTRO = ("wait", "drop", "land", "pose")   # 出てくる場面の動き（この間は、攻撃を受けない）

    def __init__(self, x, assets=None, floor=None, x_min=0.0, x_max=None, quick=False):
        self.floor = float(floor if floor is not None else C.FLOOR_Y)
        super().__init__(x, y=-C.BOSS["h"], assets=assets)   # 画面の上から降ってくる
        half = self.w / 2
        self.x_min = x_min + half
        self.x_max = (x_max if x_max is not None else C.STAGE_W) - half
        self.intro = dict(C.BOSS_INTRO, **(C.BOSS_INTRO_QUICK if quick else {}))
        self.state = "wait"   # wait / drop / land / pose（ここまでが、出てくる場面） / walk / ready / swing / crouch / leap / recover
        self.landed = False   # このフレームに着地した（Game が見て、画面を揺らす）
        self.down_t = 0       # 倒されて、地面に落ちてからのフレーム数
        self.st = 0           # いまの動きに入ってからのフレーム数
        self.vx = self.vy = 0.0
        self.count = 0        # 攻撃の回数（3回に1回、跳びかかる）
        self.shots = 0        # 出した光波の数（高い・低いの順番を決める）
        self.spawned = []     # 出した光波（Game が受け取って動かす）

    @property
    def rage(self):
        return self.hp <= self.max_hp // 2

    def update(self, player_rect, stage_w, terrain=None):
        self.t += 1
        if self.dying:      # 決まった場所へ、弧を描いて吹っ飛ぶ。落ちたら、倒れたまま残る
            B = C.END_BLOW
            self.flash = max(0, self.flash - 1)
            if self.dead_t == 0:
                self.vx, self.vy = (C.END_BOSS_X - self.cx) / B["frames"], B["vy"]
                if self.vx:
                    self.facing = -1 if self.vx > 0 else 1    # 後ろ向きに飛ぶ
            self.dead_t += 1
            if self.down_t:
                self.down_t += 1
                if self.down_t > B["rest"]:
                    self.alive = False
                return
            if self.dead_t <= B["frames"]:
                self.cx += self.vx
            self.vy += self.P["gravity"]
            self.cy += self.vy
            if self.cy >= self.floor - self.h / 2 and self.dead_t >= B["frames"]:
                self.cy = self.floor - self.h / 2
                self.cx = float(C.END_BOSS_X)
                self.down_t = 1
                self.landed = True
            elif self.cy > self.floor - self.h / 2:
                self.cy = self.floor - self.h / 2
            return
        if self.flash:
            self.flash -= 1
        self.think(player_rect, stage_w, terrain)

    def _death(self):
        """やられの動き。最後の煙のコマは使わない（倒れたまま残って、ひとこと言ってから、光になって消える）"""
        return self._frames("death")[:-1]

    @property
    def intro_done(self):
        return self.state not in self.INTRO

    def hit(self, damage=1):
        if not self.intro_done:   # 出てくる場面の間は、攻撃を受けない
            return
        super().hit(damage)
        self.stun = 0

    def _set(self, state):
        self.state = state
        self.st = 0

    @property
    def high(self):
        """次の光波が、高いか（構えの絵も、これで変える）"""
        return C.BOSS_PATTERN[self.shots % len(C.BOSS_PATTERN)] == "H"

    def _wave(self, direction, tall=False):
        P = self.P
        y = self.floor - P["high_bottom"] - P["high_h"] / 2 if tall else self.floor + C.WAVE["dy"]
        self.spawned.append(Wave(self.cx + direction * (self.w / 2 + 8), y, direction, self.a,
                                 P["wave_speed"], P["wave_range"], tall))

    def think(self, pr, stage_w, terrain=None):
        P = self.P
        self.st += 1
        s = self.state
        if s == "wait":            # 静かに待つ（まだ、画面の上にいる）
            if self.st >= self.intro["wait"]:
                self._set("drop")
            return
        if s == "land":            # 着地して、かがんだまま止まる
            if self.st >= self.intro["land"]:
                self._set("pose")
            return
        if s == "pose":            # 立って、にらむ（名前が出る）
            self.facing = 1 if pr.centerx > self.cx else -1
            if self.st >= self.intro["pose"]:
                self._set("walk")
            return
        if s in ("drop", "leap"):   # 空中。着地したら、隙になる（降ってきたときは、出てくる場面の続き）
            self.cx = max(self.x_min, min(self.cx + self.vx, self.x_max))
            self.vy += P["gravity"]
            self.cy += self.vy
            if self.cy >= self.floor - self.h / 2:
                self.cy = self.floor - self.h / 2
                self.vx = self.vy = 0.0
                self.landed = True
                self._set("land" if s == "drop" else "recover")
            return
        dx = pr.centerx - self.cx
        if s == "recover":
            if self.st >= P["rage_recover_frames" if self.rage else "recover_frames"]:
                self._set("walk")
        elif s == "walk":
            self.facing = 1 if dx > 0 else -1
            if abs(dx) > P["near"]:
                self.cx = max(self.x_min, min(self.cx + self.facing * P["speed"], self.x_max))
            if self.st >= P["rage_walk_frames" if self.rage else "walk_frames"]:
                self.count += 1
                cornered = min(pr.centerx - (self.x_min - self.w / 2), (self.x_max + self.w / 2) - pr.centerx) < P["corner"]
                self._set("crouch" if self.count % 3 == 0 or cornered else "ready")
        elif s == "ready":         # 構える（光波の予告）
            if self.st >= P["ready_frames"]:
                self._set("swing")
        elif s == "swing":
            if self.st == P["wave_at"]:
                self._wave(self.facing, self.high)
                self.shots += 1
            if self.st >= P["swing_frames"]:
                self._set("recover")
        elif s == "crouch":        # かがむ（跳びかかりの予告）。そのときの主人公の位置へ跳ぶ
            if self.st >= P["crouch_frames"]:
                frames = P["leap_frames"]
                target = max(self.x_min, min(float(pr.centerx), self.x_max))
                self.vx = (target - self.cx) / frames
                self.vy = -P["gravity"] * frames / 2
                self._set("leap")

    def image(self):
        if self.dying:
            return self._death()[1 if self.down_t else 0]    # 飛んでいる間は、のけぞる。落ちたら、倒れる
        s = self.state
        if s == "swing":
            return self._frames("swing")[0 if self.st < self.P["wave_at"] else 1]
        if s in ("drop", "leap") or (s == "ready" and self.high):
            return self._frames("swing")[0]   # 刀を振り上げる（高い光波の構えは、これ）
        if s == "land":
            return self._frames("swing")[1]   # 着地して、かがんでいる
        if s == "pose":
            return self._frames("stance")[0]
        if s in ("ready", "crouch"):
            f = self._frames("stance")
            total = self.P["ready_frames" if s == "ready" else "crouch_frames"]
            return f[min(self.st * len(f) // total, len(f) - 1)]
        if s == "recover":
            return self._frames("swing")[1]   # 振り下ろしたまま（隙）
        f = self._frames("walk")
        return f[(self.t // 12) % len(f)]


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
    def __init__(self, x, y, direction, assets, vy=0.0):
        self.a = assets
        self.px, self.py = float(x), float(y)
        self.dir = direction
        self.vy = vy   # 上下の速さ（三方手裏剣の、斜めの2つ）
        self.travel = 0.0
        self.t = 0
        self.alive = True

    @property
    def rect(self):
        return pygame.Rect(round(self.px - C.SHURIKEN_W / 2), round(self.py - C.SHURIKEN_H / 2),
                           C.SHURIKEN_W, C.SHURIKEN_H)

    def update(self, stage_w):
        self.px += self.dir * C.SHURIKEN_SPEED
        self.py += self.vy
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

    def __init__(self, x, y, direction, assets, speed=None, reach=None, tall=False):
        self.a = assets
        self.px, self.py = float(x), float(y)
        self.dir = direction
        self.speed = speed or C.WAVE["speed"]
        self.reach = reach or C.WAVE["range"]
        self.tall = tall    # ボスの高い光波（頭の高さを飛ぶ。しゃがむと下に入れる）
        self.travel = 0.0
        self.t = 0
        self.alive = True

    @property
    def rect(self):
        w, h = C.WAVE["w"], C.BOSS["high_h"] if self.tall else C.WAVE["h"]
        return pygame.Rect(round(self.px - w / 2), round(self.py - h / 2), w, h)

    def update(self, stage_w):
        self.px += self.dir * self.speed
        self.travel += self.speed
        self.t += 1
        if self.travel > self.reach or not (0 <= self.px <= stage_w):
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
    """拾えるもの。dango=スコア / onigiri=回復 / leaf・triple・super=強化。絵ができるまでは、色付きの図形で描く。
    drop=True は、敵が落とした物: 少し跳ねて地面に落ち、しばらくすると消える"""

    def __init__(self, kind, x, y, assets=None, idx=-1, drop=False):
        self.drop = drop
        self.vy = C.DROP_HOP if drop else 0.0
        self.resting = not drop     # 地面に着いている（置いてある物は、最初から）
        self.life = C.DROP_LIFE if drop else 0
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

    def update(self, terrain=None):
        self.t += 1
        if not self.drop:
            return
        self.life -= 1
        if self.life <= 0:
            self.alive = False
        if self.resting:
            return
        half = C.ITEM_SIZE / 2
        self.vy = min(self.vy + C.DROP_GRAVITY, C.MAX_FALL)
        floor = terrain.support(self.cx, self.cy + half, self.cy + half + self.vy) if terrain and self.vy >= 0 else None
        if terrain is None and self.cy + half + self.vy >= C.FLOOR_Y:
            floor = (C.FLOOR_Y, True)
        if floor:
            self.cy = floor[0] - half - 2
            self.resting = True
        else:
            self.cy += self.vy
            if self.cy > C.FALL_Y:     # 穴に落ちた
                self.alive = False

    def draw(self, surface, cam_x):
        if self.drop and self.life < 120 and (self.life // 5) % 2:
            return   # 消える前は、点滅
        x = round(self.cx) - cam_x
        y = round(self.cy + (math.sin(self.t / 18) * 2 if self.resting else 0))
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
        self.fx_t = 0             # 通ったときの演出の、残りフレーム

    @property
    def rect(self):
        return pygame.Rect(self.x - C.CHECKPOINT_W // 2, self.y - 40, C.CHECKPOINT_W, 40)

    def activate(self):
        self.active = True
        self.fx_t = C.CHECKPOINT_FX

    def update(self):
        if self.fx_t:
            self.fx_t -= 1

    def draw_fx(self, surface, cam_x):
        """通ったときの演出（主人公より手前に描く）: 光の柱が立ち、火花が上がり、「中間地点」の文字が浮かぶ"""
        if not self.fx_t:
            return
        t = C.CHECKPOINT_FX - self.fx_t
        x, y = self.x - cam_x, self.y
        if t < 36:      # 光の柱: 太く立って、細くなって消える
            w = max(2, 34 - t)
            beam = pygame.Surface((w, y), pygame.SRCALPHA)
            beam.fill((255, 240, 170, max(0, 200 - t * 5)))
            surface.blit(beam, (x - w // 2, 0))
        if t < 60:      # 火花: 鳥居から、輪になって広がりながら上がる
            for k in range(10):
                a = k * math.pi / 5 + t * 0.05
                r = 6 + t * 0.9
                sx, sy = x + math.cos(a) * r, y - 22 + math.sin(a) * r * 0.55 - t * 0.5
                size = 3 if t < 30 else 2
                pygame.draw.rect(surface, (255, 248, 176) if (k + t // 4) % 2 else (252, 208, 40), (round(sx), round(sy), size, size))
        if self.a and t >= 8:   # 文字: ゆっくり上がって、消える
            img = self.a.cp_text
            img.set_alpha(min(255, self.fx_t * 255 // 24))
            surface.blit(img, (x - img.get_width() // 2, y - 62 - min(t, 40) // 2))

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
