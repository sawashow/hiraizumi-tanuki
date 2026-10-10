"""平泉タヌキ侍 - メインループ

操作: ←→ 移動 / SPACE or ↑ ジャンプ / ↓ しゃがむ / Z 刀 / X 木の葉手裏剣 / Enter 再開（ゲームオーバー・クリア時） / ESC 終了
"""
import asyncio
import math
import os
import random
import sys

import pygame

import config as C
from stage import CHECKPOINT, ITEMS, Terrain
from audio import DIR as AUDIO_DIR, Audio
from sprites import Assets, Boss, Checkpoint, draw_zzz, HitEffect, Item, Player, Shuriken, SlashWave, Wave, make_enemy

# 敵の配置（種類, x）。序盤は落ち武者だけ→中盤に狐火→後半に烏→終盤は混ぜる
DANGO_TOTAL = sum(1 for k, _, _ in ITEMS if k == "dango")   # 団子の数

ENEMY_SPAWNS = (
    ("ochimusha", 520), ("ochimusha", 900),
    ("kitsunebi_low", 1250), ("kitsunebi_high", 1420), ("ochimusha", 1455),
    ("karasu", 1850), ("karasu", 2000),
    ("ochimusha", 2100), ("kitsunebi_high", 2200), ("karasu", 2300),
    ("ochimusha", 2460), ("karasu", 2620),
    ("ochimusha", 2880), ("kitsunebi_high", 3000), ("karasu", 3120),
    ("ochimusha", 3260), ("kitsunebi_low", 3400), ("ochimusha", 3480), ("karasu", 3540),
)
# 地面タイルの並べ方（石畳A・B・苔・落ち葉）。位置から決めるので、スクロールしても変わらない
FILL_PATTERN = (0, 3, 0, 4, 3, 0, 3, 5, 0, 3, 4, 0)


def drop_kind(roll):
    """0以上1未満のくじ（roll）から、落とす物を決める。何も落とさないときは None"""
    for kind, chance in C.DROPS:
        if roll < chance:
            return kind
        roll -= chance
    return None


class Game:
    def __init__(self, terrain=None, title=False):
        self.a = Assets()
        self.terrain = terrain or Terrain()
        self.use_title = title   # スタート画面から始める（クリアのあとも、スタート画面へ戻る）
        self.sfx = []            # このフレームに鳴らす効果音（メインループが鳴らして、空にする）
        self.rng = random.Random()   # 落とし物の、くじ
        self.story_bgm = os.path.exists(os.path.join(AUDIO_DIR, C.BGM_STORY))   # 語りの曲があるか
        self.super_bgm = os.path.exists(os.path.join(AUDIO_DIR, C.BGM_SUPER))   # スーパータヌキの曲があるか
        self._enter_title(title)
        self.reset()

    def _enter_title(self, on=True):
        self.title = on          # いま、スタート画面を出している
        self.title_t = 0
        self.thunder_n = 0       # これまでの稲光の回数
        self.thunder_at = C.TITLE_THUNDER[0]   # 次の稲光のフレーム
        self.flash_t = 0         # 稲光で光っている残りフレーム
        self.start_t = 0         # 決定してから、始まるまでの残りフレーム
        self.story = False       # いま、始まりの語りを流している
        self.story_t = 0
        self.story_run = 0       # 決定してからのフレーム数（タヌキ侍が気づいて、駆け抜けている）
        self.story_wake = 0      # 決定してから、走り出すまでのフレーム数
        self.story_woke = False  # 決定したとき、眠っていた
        self.story_x = float(C.STORY_TANUKI["x"])   # タヌキ侍の位置

    def reset(self):
        """最初から（残機・スコア・中間地点も、初期値に戻す）"""
        self.lives = C.LIVES
        self.score = 0
        self.dango = 0
        self.taken = set()          # 取ったアイテム（配置表の番号）
        self.one_up_given = False
        self.checkpoint = Checkpoint(*CHECKPOINT, self.a)
        self.cp_state = None        # 中間地点を通ったときの (スコア, 団子の数, 取ったもの)
        self.boss_state = None      # ボスの場所に入ったときの (スコア, 団子の数, 取ったもの)。入り直すと、出てくる場面が短くなる
        self.frames = 0             # 遊んだ時間（フレーム数。クリア画面に出す）
        self.cleared = False
        self.clear_t = 0            # クリアしてからの経過フレーム
        self._start(60, float(C.FLOOR_Y))

    def respawn(self):
        """やられて、残機が残っているとき: 中間地点（なければ最初）から、体力満タンで再開する。
        再開した場所の近くの敵は置かない。ボスまで進んでいたら、ボスの場所の入口から（ザコ敵は置かない）"""
        if self.boss_state:
            self.score, self.dango, taken = self.boss_state
            self.taken = set(taken)
            self._start(C.ARENA_X0 + 100, float(self.terrain.height_at(C.ARENA_X0 + 100) or C.FLOOR_Y), C.RESPAWN_CLEAR)
            self.enemies = []
        elif self.cp_state:
            self.score, self.dango, taken = self.cp_state
            self.taken = set(taken)
            self._start(self.checkpoint.x, float(self.checkpoint.y), C.RESPAWN_CLEAR)
        else:
            self.score, self.dango, self.taken = 0, 0, set()
            self._start(60, float(C.FLOOR_Y), C.RESPAWN_CLEAR)

    def _start(self, x, y, clear=0):
        """clear を渡すと（再開のとき）、その距離までの敵は置かず、少しのあいだ無敵にする"""
        self.player = Player(x, self.a)
        self.player.py = y
        self.player.safe_x, self.player.safe_y = float(x), y
        if clear:
            self.player.invincible = C.INVINCIBLE_FRAMES
        self.enemies = [make_enemy(kind, ex, self.a, self.terrain) for kind, ex in ENEMY_SPAWNS
                        if abs(ex - x) > clear]
        self.shurikens = []
        self.throw_n = 0    # 手裏剣を投げた回数（1投げごとの番号に使う）
        self.boss = None    # ボス（ボスの場所に入ると、出てくる）
        self.boss_on = False
        self.shake_t = 0    # 画面が揺れている残りフレーム（ボスの着地）
        self.bar_t = 0      # ボスが出てくる場面の、上下の黒い帯の出ぐあい
        self.ending = 0     # ボスを倒したあとの寸劇に入ってからのフレーム数（0 は、寸劇ではない）
        self.end_ready = False   # 寸劇: ボスが倒れて、タヌキ侍が話す場所に着いた
        self.end_wait = 0   # 寸劇: そこまでにかかっているフレーム数
        self.waves = []     # 敵の光波
        self.slashes = []   # 強化中の、主人公の光波
        self.items = [Item(kind, ix, iy, self.a, n) for n, (kind, ix, iy) in enumerate(ITEMS) if n not in self.taken]
        self.effects = []
        self.cam_x = max(0, min(int(x) - C.BASE_W // 2, C.STAGE_W - C.BASE_W))
        self.over_t = 0   # やられてからの経過フレーム
        self.dead = False
        self.msg_t = 0    # 「1UP!」を出している残りフレーム

    # --- 1フレーム進める。held は押している間のキー、pressed はこのフレームに押したキー ---
    def step(self, held, pressed=()):
        p = self.player
        if self.story:      # 始まりの語り: 決定のキーを押すまで、続く。押すと、タヌキ侍が気づいて、右へ駆け抜けて、ゲームが始まる
            T = C.STORY_TANUKI
            self.story_t += 1
            if self.story_run:
                self.story_run += 1
                if self.story_run > self.story_wake:    # 気づいた（飛び起きた）あと、走り出す
                    self.story_x += T["run_speed"]
                if self.story_x > C.BASE_W + T["head_x"]:
                    self.story = False
            elif self.story_t > C.STORY_SKIP_WAIT and {"restart", "attack", "jump"} & set(pressed):
                self.story_wake = T["wake"] if self.story_asleep else T["notice"]
                self.story_woke = self.story_asleep     # 眠っていたか（飛び起きる動きにする）
                self.story_run = 1
            return
        if self.title:      # スタート画面: 止めておく。Enter（刀・ジャンプのキーでも）で、刀の音が鳴って始まる
            self.title_t += 1
            if self.flash_t:
                self.flash_t -= 1
            if self.start_t:
                self.start_t -= 1
                if not self.start_t:
                    self.title = False
                    self.story, self.story_t, self.story_run = True, 0, 0
                    self.story_x = float(C.STORY_TANUKI["x"])
                return
            if {"restart", "attack", "jump"} & set(pressed):
                self.start_t = C.TITLE_START
                self.flash_t = 0
                self.sfx.append(C.SFX_SWORD)
                return
            if self.title_t == self.thunder_at:                       # 稲光
                self.flash_t = C.TITLE_FLASH
            elif self.title_t == self.thunder_at + C.THUNDER_DELAY:   # 少し遅れて、雷鳴
                self.sfx.append(C.SFX_THUNDER)
                self.thunder_n += 1
                self.thunder_at += C.TITLE_THUNDER[self.thunder_n % len(C.TITLE_THUNDER)]
            return
        if self.cleared:    # クリア: 止めて、結果を出す。Enter で最初から（スタート画面があれば、そこへ戻る）
            self.clear_t += 1
            if "restart" in pressed and self.clear_t >= C.CLEAR_WAIT:
                self.reset()
                self._enter_title(self.use_title)
            return
        if p.hp <= 0:
            if not self.dead:
                self.dead = True
                self.lives -= 1
            self.over_t += 1
            p.defeat_t = self.over_t
            if self.lives > 0:
                if self.over_t >= C.RESPAWN_AT:
                    self.respawn()
            elif "restart" in pressed and self.over_t >= C.GAMEOVER_WAIT:
                self.reset()
            return
        if self.ending:     # ボスを倒したあとの寸劇（動かせない。時間も止まる）
            self._step_ending(set(pressed))
            return
        self.frames += 1
        if self.boss_intro:   # ボスが出てくる場面の間は、動かせない
            held, pressed = set(), set()
        if "jump" in pressed:
            p.jump()
        if "jump_release" in pressed:
            p.cut_jump()
        if "attack" in pressed:
            p.attack()
        if "throw" in pressed:
            p.throw()
        p.update(held, C.STAGE_W, self.terrain)
        self._boss_area(p)
        foes = self.enemies + ([self.boss] if self.boss else [])
        if p.release:   # 手裏剣（三方手裏剣なら、前・斜め上・斜め下の3つ）
            self.throw_n += 1
            for vy in (C.TRIPLE_VY if p.triple else (0.0,)):
                self.shurikens.append(Shuriken(*p.shuriken_spawn(), self.a, vy))
                self.shurikens[-1].throw_id = self.throw_n   # 同じ1投げの手裏剣（三方手裏剣の3つ）は、同じ番号
        if p.slash:
            self.slashes.append(SlashWave(*p.slash_spawn(), self.a))
        for e in foes:
            e.update(p.rect, C.STAGE_W, self.terrain)
            spawned = getattr(e, "spawned", None)
            if spawned:
                self.waves.extend(spawned)
                spawned.clear()
        for w in self.waves:
            w.update(C.STAGE_W)
        for s in self.slashes:
            s.update(C.STAGE_W)
        for it in self.items:
            it.update(self.terrain)
        self.checkpoint.update()
        for s in self.shurikens:
            s.update(C.STAGE_W)

        # 刀 → 敵（1振りにつき、同じ敵に1回だけ）
        sword = p.sword_rect()
        if sword:
            for e in foes:
                if e.active and e.last_swing != p.swing_id and sword.colliderect(e.rect):
                    e.last_swing = p.swing_id
                    e.hit(C.SWORD_DAMAGE)
        # 手裏剣 → 敵
        for s in self.shurikens:
            for e in foes:
                if s.alive and e.active and s.rect.colliderect(e.rect):
                    s.alive = False
                    tid = getattr(s, "throw_id", None)
                    if tid is None or getattr(e, "last_throw", None) != tid:   # 1投げにつき、同じ敵に当たるのは1つだけ（残りは、消えるだけ）
                        e.last_throw = tid
                        e.hit(C.SHURIKEN_DAMAGE)
                    self.effects.append(HitEffect(*s.rect.center, self.a))
        # 強化中の光波 → 敵
        for s in self.slashes:
            for e in foes:
                if s.alive and e.active and s.rect.colliderect(e.rect):
                    s.alive = False
                    e.hit(C.SLASH["damage"])
                    self.effects.append(HitEffect(*s.rect.center, self.a))
        # 倒した敵が、物を落とす（ボスは落とさない）
        for e in self.enemies:
            if e.dying and not getattr(e, "dropped", False):
                e.dropped = True
                kind = drop_kind(self.rng.random())
                if kind:
                    self.items.append(Item(kind, e.rect.centerx, e.rect.centery, self.a, drop=True))
        # アイテムを拾う
        for it in self.items:
            if it.alive and p.rect.colliderect(it.rect):
                it.alive = False
                self.taken.add(it.idx)
                if it.kind == "dango":
                    self.score += C.SCORE_DANGO
                    self.dango += 1
                    if self.dango >= DANGO_TOTAL and not self.one_up_given:
                        self.one_up_given = True    # 団子を全部取ると、残機が1つ増える
                        self.lives += 1
                        self.msg_t = 90
                elif it.kind == "onigiri":
                    if p.hp < C.PLAYER_HP:
                        p.hp = min(C.PLAYER_HP, p.hp + C.HEAL_ONIGIRI)
                    else:
                        self.score += C.SCORE_FULL_HP
                elif it.kind == "leaf":
                    p.power = True
                elif it.kind == "triple":
                    p.triple = True
                else:
                    p.super_t = C.SUPER_FRAMES
        # 中間地点（鳥居）を通る
        if not self.checkpoint.active and p.rect.colliderect(self.checkpoint.rect):
            self.checkpoint.activate()
            self.sfx.append(C.SFX_CHECKPOINT)
            self.cp_state = (self.score, self.dango, frozenset(self.taken))
        if self.msg_t:
            self.msg_t -= 1
        # 刀 → 光波（刀で斬ると消せる。手裏剣は通り抜ける）
        if sword:
            for w in self.waves:
                if w.alive and sword.colliderect(w.rect):
                    w.alive = False
                    self.effects.append(HitEffect(*w.rect.center, self.a))
        # 光波 → 主人公（無敵のあいだは、すり抜ける）
        for w in self.waves:
            if w.alive and not p.untouchable and p.rect.colliderect(w.rect):
                w.alive = False
                p.take_damage(w.px, C.WAVE["damage"])
        # 敵 → 主人公（踏んでも倒せない。触れるとダメージ）
        for e in foes:
            if e.active and p.rect.colliderect(e.rect):
                if p.super_t and e is not self.boss:    # スーパータヌキ: 触れたザコ敵を、倒す（ボスには効かない）
                    e.hit(e.hp)
                    self.effects.append(HitEffect(*e.rect.center, self.a))
                else:
                    p.take_damage(e.rect.centerx, e.P["touch"])

        if self.boss and self.boss.landed:   # ボスが着地した: 画面を揺らす（降ってきたときは、大きく）
            self.boss.landed = False
            self.shake_t = C.BOSS_INTRO["shake"] if self.boss_intro else C.LEAP_SHAKE
            if self.boss_intro:     # 降ってきたボスに、タヌキ侍が驚く
                p.startle_t = C.STARTLE
                p.facing = 1 if self.boss.cx > p.px else -1
        elif self.shake_t:
            self.shake_t -= 1
        self.bar_t = max(0, min(C.BOSS_INTRO["bar_frames"], self.bar_t + (1 if self.boss_intro else -1)))
        self.enemies = [e for e in self.enemies if e.alive]
        if self.boss and self.boss.dying:   # ボスを倒した: すぐ寸劇へ（ボスは吹っ飛んで、倒れたまま残る）
            self.waves, self.shurikens, self.slashes = [], [], []
            self.score += C.SCORE_BOSS
            self.ending = 1
        self.shurikens = [s for s in self.shurikens if s.alive]
        self.waves = [w for w in self.waves if w.alive]
        self.slashes = [s for s in self.slashes if s.alive]
        self.items = [it for it in self.items if it.alive]
        for fx in self.effects:
            fx.update()
        self.effects = [fx for fx in self.effects if fx.alive]

        if not self.boss_on:   # ボスと戦っている間は、画面を動かさない（入ったときだけ、右端まで流す）
            self.cam_x = max(0, min(p.rect.centerx - C.BASE_W // 2, C.STAGE_W - C.BASE_W))
        elif self.cam_x < C.ARENA_X0:
            self.cam_x = min(C.ARENA_X0, self.cam_x + C.BOSS_CAM_SPEED)

    def _end_phase(self):
        """寸劇の、いまの場面と、その場面に入ってからのフレーム数。
        wait（間） → boss（ボスのひとこと） → fade（光になって消える） → reply（タヌキ侍が返す） → run（右へ駆け抜ける）"""
        t = self.ending - 1
        for name in ("wait", "boss", "fade", "reply"):
            if t < C.ENDING[name]:
                return name, t
            t -= C.ENDING[name]
        return "run", t

    def _talk_cells(self, name):
        img = self.a.talk_boss if name == "boss" else self.a.talk_tanuki
        return img.get_width() // C.TALK_CELL

    def _talk_shown(self, name, t):
        """せりふが出始めてから t フレームで、何文字出ているか（途中に、間が入ることがある）"""
        at, wait = C.TALK_PAUSE.get(name, (0, 0))
        k = t // C.ENDING["type"] + 1
        if wait and k > at:
            k = max(at, (t - wait) // C.ENDING["type"] + 1)
        return min(k, self._talk_cells(name))

    def _step_ending(self, pressed):
        E = C.ENDING
        p = self.player
        if self.boss:
            self.boss.update(p.rect, C.STAGE_W, self.terrain)
            if self.boss.landed:    # 吹っ飛んだボスが落ちた: 画面を揺らす
                self.boss.landed = False
                self.shake_t = C.LEAP_SHAKE
        if not self.end_ready:      # ボスが倒れきって、タヌキ侍が話す場所に着くまで、待つ
            self.end_wait += 1
            dx = C.END_TANUKI_X - p.px
            near = abs(dx) <= C.MAX_SPEED
            p.update(set() if near else {"right" if dx > 0 else "left"}, C.STAGE_W, self.terrain)
            p.rest_t = 0
            if near and p.on_ground:
                p.px, p.vx, p.facing = float(C.END_TANUKI_X), 0.0, 1
            arrived = near and p.on_ground and not self.boss.alive
            if arrived or self.end_wait >= C.END_BLOW["limit"]:
                self.end_ready = True
            self._end_common()
            return
        name, t = self._end_phase()
        talk = {"boss": C.SFX_TALK_LOW, "reply": C.SFX_TALK_HIGH}
        if name in talk and t >= E["skip"] and pressed & {"attack", "jump", "restart"}:
            typed = self._talk_cells(name) * E["type"] + C.TALK_PAUSE.get(name, (0, 0))[1]
            # キーを押すと、字が出ている途中なら全部出す。出きっていれば、次へ送る
            self.ending += (typed - t - 1) if t < typed - 1 else (E[name] - t - 1)
        self.ending += 1
        name, t = self._end_phase()
        if name in talk and (t == 0 or self._talk_shown(name, t) > self._talk_shown(name, t - 1)):
            self.sfx.append(talk[name])    # 字が1文字出るたびに、ピッと鳴らす
        if name == "fade" and t == 0:
            self.sfx.append(C.SFX_CHECKPOINT)
        if name in ("reply", "run"):
            self.boss = None
        if name == "run":      # 面の端の先まで走って、画面から出たら、結果へ
            p.update({"right"}, C.STAGE_W + 120, self.terrain)
            if p.px - self.cam_x >= C.BASE_W + E["exit"]:
                self.cleared = True
        else:
            p.update(set(), C.STAGE_W, self.terrain)
            p.rest_t = 0       # 話の途中で、居眠りしない
            if self.boss and p.on_ground:
                p.facing = 1 if self.boss.cx > p.px else -1
        self._end_common()

    def _end_common(self):
        for fx in self.effects:
            fx.update()
        self.effects = [fx for fx in self.effects if fx.alive]
        self.shake_t = max(0, self.shake_t - 1)
        self.bar_t = min(C.BOSS_INTRO["bar_frames"], self.bar_t + 1)

    def _boss_area(self, p):
        """最後の1画面に少し入ったら、ボスが出る（画面は、右端まで流れて止まる。ボスと、離れて向き合う）。そこからは、左へ戻れない"""
        if not self.boss_on and p.hp > 0 and p.px >= C.ARENA_X0 + C.BOSS_TRIGGER:
            self.boss_on = True
            self.cam_x = max(0, min(p.rect.centerx - C.BASE_W // 2, C.ARENA_X0))   # ここから、右端まで流す
            self.boss = Boss(C.BOSS_X, self.a, self.terrain.height_at(C.BOSS_X), C.ARENA_X0, C.STAGE_W,
                             quick=self.boss_state is not None)
            self.boss_state = (self.score, self.dango, frozenset(self.taken))
            self.enemies = []   # ザコ敵は、ここで消える
            self.waves = []
        if self.boss_on and p.px < C.ARENA_X0 + C.PLAYER_W / 2:
            p.px = C.ARENA_X0 + C.PLAYER_W / 2
            p.vx = 0.0

    @property
    def story_asleep(self):
        """語りの画面で、タヌキ侍が眠っている"""
        return self.story and not self.story_run and self.story_t >= C.STORY_TANUKI["sleep_at"]

    @property
    def story_dreaming(self):
        """眠って、おにぎりの夢を見ている"""
        return self.story_asleep and self.story_t >= C.STORY_TANUKI["dream_at"]

    @property
    def boss_intro(self):
        """ボスが出てくる場面の途中か"""
        return self.boss is not None and not self.boss.intro_done

    @property
    def bgm(self):
        """いま鳴らす曲。スタート画面・やられている間・クリアのあとは、鳴らさない（None）。
        始まりの語りの間は、語りの曲（無ければ、無音）。ゲームが始まると、1面の曲。
        ボスが降ってくるまでは静かにして、着地したときに、ボスの曲を始める"""
        if self.player.hp <= 0 or self.cleared or self.ending or self.title:
            return None
        if self.story:
            return C.BGM_STORY if self.story_bgm else None
        if self.boss and self.boss.state in ("wait", "drop"):
            return None
        if self.boss_on:
            return C.BGM_BOSS
        return C.BGM_SUPER if self.player.super_t and self.super_bgm else C.BGM_STAGE1

    # --- 描画 ---
    def draw(self, screen, font):
        if self.story:
            self._draw_story(screen)
            return
        if self.title and self.a.title_bg:   # スタート画面の絵があれば、それだけを出す
            screen.blit(self.a.title_bg, (0, 0))
            self._draw_title(screen, dim=False)
            return
        cam = self.cam_x
        span = C.STAGE_W - C.BASE_W
        # 奥の層ほどゆっくり動く（画像の余りの幅をカメラの移動量に割り振る）
        sky_x = round(cam * (self.a.sky.get_width() - C.BASE_W) / span)
        mid_x = round(cam * (self.a.mid.get_width() - C.BASE_W) / span)
        screen.blit(self.a.sky, (-sky_x, 0))
        screen.blit(self.a.mid, (-mid_x, 0))
        self._draw_ground(screen, cam)
        for e in self.enemies:
            e.draw(screen, cam)
        end = self._end_phase() if self.end_ready else ("", 0)
        if self.boss and end[0] == "fade":
            self._draw_boss_fade(screen, cam, end[1])
        elif self.boss:
            self.boss.draw(screen, cam)
        for s in self.shurikens:
            s.draw(screen, cam)
        for w in self.waves:
            w.draw(screen, cam)
        for s in self.slashes:
            s.draw(screen, cam)
        for it in self.items:
            it.draw(screen, cam)
        self.checkpoint.draw(screen, cam)
        self.player.draw(screen, cam)
        for fx in self.effects:
            fx.draw(screen, cam)
        self.checkpoint.draw_fx(screen, cam)
        if self.title:     # スタート画面: 1面の始まりの景色の上に、題名を出す（体力などは出さない）
            self._draw_title(screen)
            return
        if self.shake_t:   # 画面を、上下に揺らす（だんだん小さく）
            dy = (1 + self.shake_t // 6) * (1 if (self.shake_t // 2) % 2 else -1)
            world = screen.copy()
            screen.fill(C.BLACK)
            screen.blit(world, (0, dy))
        if self.bar_t:     # ボスが出てくる場面: 上下に黒い帯
            h = C.BOSS_INTRO["bar"] * self.bar_t // C.BOSS_INTRO["bar_frames"]
            screen.fill(C.BLACK, (0, 0, C.BASE_W, h))
            screen.fill(C.BLACK, (0, C.BASE_H - h, C.BASE_W, h))
        if self.player.hp <= 0:
            self._draw_dim(screen)
        if end[0] == "boss" and self.boss:
            r = self.boss.rect
            self._draw_bubble(screen, self.a.talk_boss, r.centerx - cam, r.bottom - C.TALK_BOSS_Y, self._talk_shown(*end))
        elif end[0] == "reply":
            r = self.player.rect
            self._draw_bubble(screen, self.a.talk_tanuki, r.centerx - cam, r.top - 4, self._talk_shown(*end))
        self._draw_hud(screen, font)
        if self.player.hp <= 0:
            self._draw_gameover_text(screen, font)
        if self.cleared:
            self._draw_clear(screen, font)

    def _draw_ground(self, screen, cam):
        tiles = self.a.tiles
        top = tiles[1]
        # 穴の底は暗くしておく（地面のない所は、ここが見える）
        pygame.draw.rect(screen, (8, 6, 18), (0, C.GROUND_Y, C.BASE_W, C.BASE_H - C.GROUND_Y))
        for x0, x1, top_y in self.terrain.ground:
            sx0, sx1 = max(x0 - cam, 0), min(x1 - cam, C.BASE_W)
            if sx1 <= sx0:
                continue
            tile_y = top_y - (C.FLOOR_Y - C.GROUND_Y)   # 地面の上端のタイルの高さ
            screen.set_clip(pygame.Rect(sx0, 0, sx1 - sx0, C.BASE_H))   # 区間の端で、タイルを切る
            for i in range(max(x0, cam) // 32, (min(x1, cam + C.BASE_W) - 1) // 32 + 1):
                x = i * 32 - cam
                screen.blit(top, (x, tile_y))
                row = 0
                y = tile_y + top.get_height()
                while y < C.BASE_H:
                    screen.blit(tiles[FILL_PATTERN[(i * 7 + row * 5) % len(FILL_PATTERN)]], (x, y))
                    y += 32
                    row += 1
        screen.set_clip(None)
        # 浮き足場（地面の上端のタイルを、横に並べて使う）
        for x0, x1, top_y in self.terrain.platforms:
            screen.set_clip(pygame.Rect(x0 - cam, 0, x1 - x0, C.BASE_H))
            for tx in range(x0, x1, 32):
                screen.blit(top, (tx - cam, top_y - (C.FLOOR_Y - C.GROUND_Y)))
        screen.set_clip(None)

    def _draw_hud(self, screen, font):
        for i in range(C.PLAYER_HP):
            color = C.HEART if i < self.player.hp else C.HEART_EMPTY
            pygame.draw.rect(screen, C.BLACK, (8 + i * 14 - 1, 8 - 1, 12, 12))
            pygame.draw.rect(screen, color, (8 + i * 14, 8, 10, 10))
        # 持っている強化の印（金の葉・三方手裏剣・スーパータヌキ）。スーパータヌキは、残り時間の棒も出す
        p = self.player
        x = 8 + C.PLAYER_HP * 14 + 2
        for kind, on in (("leaf", p.power), ("triple", p.triple), ("super", p.super_t)):
            if on:
                screen.blit(pygame.transform.scale(self.a.item[kind], (12, 12)), (x, 7))
                x += 15
        if p.super_t:
            pygame.draw.rect(screen, C.BLACK, (x, 10, 42, 6))
            pygame.draw.rect(screen, (252, 208, 40), (x + 1, 11, 40 * p.super_t // C.SUPER_FRAMES, 4))
        text = font.render("%06d" % self.score, False, C.TEXT)
        screen.blit(text, (C.BASE_W - text.get_width() - 8, 8))
        dango = pygame.transform.scale(self.a.item["dango"], (4, 12))
        screen.blit(dango, (8, 24))
        screen.blit(font.render("%d/%d" % (self.dango, DANGO_TOTAL), False, C.TEXT), (16, 26))
        screen.blit(font.render("LIFE x%d" % max(self.lives, 0), False, C.TEXT), (C.BASE_W - 64, 24))
        if self.boss and self.boss.active and self.boss.intro_done:
            self._draw_boss_hp(screen, font)
        if self.boss and self.boss.state == "pose":   # ボスの二つ名と名前（ゆっくり出て、ゆっくり消える）
            t, total, fade = self.boss.st, self.boss.intro["pose"], C.BOSS_INTRO["name_fade"]
            delay = C.BOSS_NAME_DELAY if total > C.BOSS_NAME_DELAY * 3 else 0   # 短いときは、一度に出す
            for img, y, start in ((self.a.boss_title, C.BOSS_TITLE_Y, 0), (self.a.boss_name, C.BOSS_NAME_Y, delay)):
                img.set_alpha(max(0, min(255, (t - start) * 255 // fade, (total - t) * 255 // fade)))
                screen.blit(img, (C.BASE_W // 2 - img.get_width() // 2, y))
        if self.msg_t:   # 団子を全部取った
            screen.blit(self.a.oneup, (self.player.rect.centerx - self.cam_x - self.a.oneup.get_width() // 2,
                                       self.player.rect.top - 28 - (90 - self.msg_t) // 4))

    def _draw_story(self, screen):
        """始まりの語り: 暗い画面の上を、文章が下から上へ流れ（1回だけ）、下にタヌキ侍がいる"""
        T = C.STORY_TANUKI
        screen.fill(C.BLACK)
        # 文章: 決まった範囲の中だけを流す。上下の端では、暗がりに消える
        img = self.a.story
        y = C.STORY_WINDOW - self.story_t * C.STORY_SPEED
        if y > -img.get_height():
            screen.set_clip((0, 0, C.BASE_W, C.STORY_WINDOW))
            img.set_alpha(max(0, 255 - self.story_run * 16))    # 決定したら、文章は、すっと消える
            screen.blit(img, (C.BASE_W // 2 - img.get_width() // 2, round(y)))
            line = pygame.Surface((C.BASE_W, 2))
            for i in range(0, C.STORY_FADE, 2):
                line.set_alpha(255 * (C.STORY_FADE - i) // C.STORY_FADE)
                screen.blit(line, (0, i))
                screen.blit(line, (0, C.STORY_WINDOW - 2 - i))
            screen.set_clip(None)
        # 地面の線
        pygame.draw.rect(screen, (40, 32, 56), (0, T["ground"], C.BASE_W, 2))
        pygame.draw.rect(screen, (24, 20, 36), (0, T["ground"] + 2, C.BASE_W, 2))
        # タヌキ侍: 立っている → あくび → うとうと → 座って眠る → 夢を見る。決定すると、気づいて（飛び起きて）、右へ駆け抜ける
        x, t = round(self.story_x), self.story_t
        frame, dy = 0, 0
        running = self.story_run > self.story_wake
        before = T["sleep_at"] - t     # 眠るまでの残り
        if running:
            n = self.story_run - self.story_wake
            frame = 9 if n < 6 else (10, 9)[(n // T["run_ticks"]) % 2]
            dy = -1 if frame == 10 else 0
        elif self.story_run and self.story_woke:     # 飛び起きる: 目を見開いて、小さく跳ねる
            u = self.story_run / self.story_wake
            if u < 0.4:
                frame = 7
            else:
                frame, dy = 8, -round(8 * math.sin((u - 0.4) / 0.6 * math.pi))
        elif self.story_run:
            frame = 0
        elif self.story_asleep:
            frame = C.STORY_SLEEP_SEQ[((t - T["sleep_at"]) // T["breath"]) % len(C.STORY_SLEEP_SEQ)]
        elif before <= T["sit"]:
            frame = 3
        elif before <= T["sit"] + T["drowsy"]:
            frame = 2
        elif before <= T["sit"] + T["drowsy"] + T["yawn"]:
            frame = 1
        f = self.a.story_tanuki[frame]
        screen.blit(f, (x - T["head_x"], T["ground"] - T["foot_y"] + dy))
        head_y = T["ground"] - (34 if frame in (3, 4, 5, 6, 7) else 42)      # 頭のてっぺんあたり
        if self.story_asleep:
            self._draw_sleep(screen, x, head_y, t)
        if self.story_run and not running:           # 気づいた印「！」
            bx, by = x + 2, head_y - 16 + dy
            for rect in ((bx, by, 3, 7), (bx, by + 9, 3, 3)):
                pygame.draw.rect(screen, C.BLACK, pygame.Rect(rect).inflate(2, 2))
                pygame.draw.rect(screen, (252, 208, 40), rect)
        if not self.story_run and t > C.STORY_SKIP_WAIT and (t // 30) % 2 == 0:
            hint = self.a.title_prompt
            screen.blit(hint, (C.STORY_PROMPT[0] - hint.get_width() // 2, C.STORY_PROMPT[1]))

    def _draw_sleep(self, screen, x, head_y, t):
        """眠っている印: 「Z」が、ひとつずつ浮かんで上がっていく。しばらくすると、おにぎりの夢の吹き出しが出る"""
        T = C.STORY_TANUKI
        if not self.story_dreaming:
            draw_zzz(screen, x + 14, head_y + 4, t - T["sleep_at"])
            return
        # 夢の吹き出し: 小さな丸が2つ、その先に大きな雲。中に、おにぎりが浮いている
        grow = min(1.0, (t - T["dream_at"]) / 24)
        white, edge = (244, 244, 252), (16, 10, 24)
        for cx, cy, r in ((x + 18, head_y + 2, 1), (x + 25, head_y - 3, 2)):   # 頭の横へ（上を流れる文章に、かぶらないように）
            pygame.draw.circle(screen, edge, (cx, cy), r + 2)
            pygame.draw.circle(screen, white, (cx, cy), r)
        if grow < 0.4:
            return
        bw, bh = round(42 * grow), round(30 * grow)
        bx, by = x + 52, head_y - 8 + round(math.sin(t / 40) * 1.5)
        cloud = [(-0.28, 0.05, 0.36), (0.0, -0.12, 0.42), (0.28, 0.05, 0.36), (-0.12, 0.2, 0.34), (0.14, 0.2, 0.34)]
        for color, pad in ((edge, 2), (white, 0)):
            for ox, oy, r in cloud:
                pygame.draw.circle(screen, color, (bx + round(ox * bw), by + round(oy * bh)), round(r * bh) + (1 if pad else 0))
        if grow >= 1.0:
            o = self.a.item["onigiri"]
            screen.blit(o, (bx - o.get_width() // 2, by - o.get_height() // 2 + round(math.sin(t / 22) * 1.5)))
            if (t // 24) % 3 == 0:      # きらり
                sx, sy = bx + 10, by - 8
                pygame.draw.rect(screen, (252, 208, 40), (sx - 2, sy, 5, 1))
                pygame.draw.rect(screen, (252, 208, 40), (sx, sy - 2, 1, 5))

    def _draw_title(self, screen, dim=True):
        if dim:
            veil = pygame.Surface((C.BASE_W, C.BASE_H))
            veil.set_alpha(C.TITLE_DIM)
            screen.blit(veil, (0, 0))
        if self.flash_t:    # 稲光: 空に稲妻が走る。ぱっと光って、少し間をおいて、もう一度弱く光る
            t = C.TITLE_FLASH - self.flash_t
            power = 1.0 - t / 5 if t < 5 else (0.6 - (t - 10) / 16 if 10 <= t < 20 else 0.0)
            if power > 0:
                B = C.BOLT
                light = pygame.Surface((C.BASE_W, C.BASE_H))
                light.fill(B["sky"])
                light.set_alpha(int(B["sky_alpha"] * power))
                screen.blit(light, (0, 0))
                bolt, branch = self._bolt()
                for pts, wide in ((bolt, True), (branch, False)):
                    if wide:
                        pygame.draw.lines(screen, B["glow"], False, pts, 4)
                    pygame.draw.lines(screen, B["core"] if wide and power > 0.4 else B["glow"], False, pts, 2 if wide else 1)
        logo = self.a.title_logo
        screen.blit(logo, (C.TITLE_LOGO[0] - logo.get_width() // 2, C.TITLE_LOGO[1]))
        if (self.title_t // (4 if self.start_t else 30)) % 2 == 0:   # 点滅（決定したあとは、速く）
            img = self.a.title_prompt
            screen.blit(img, (C.TITLE_PROMPT[0] - img.get_width() // 2, C.TITLE_PROMPT[1]))

    def _bolt(self):
        """稲妻の折れ線（本体, 枝）。雷ごとに形が変わる（同じ雷の間は、同じ形）"""
        B = C.BOLT
        rnd = random.Random(self.thunder_n * 7919 + 11)
        x = rnd.uniform(B["x0"], B["x1"])
        pts = [(round(x), B["top"])]
        for y in range(B["top"] + B["step"], B["bottom"] + 1, B["step"]):
            x = max(B["x0"] - 6, min(B["x1"] + 6, x + rnd.uniform(-B["jitter"], B["jitter"])))
            pts.append((round(x), y))
        i = rnd.randrange(len(pts) // 3, len(pts) * 2 // 3)   # 途中から、短い枝が出る
        side = rnd.choice((-1, 1))
        bx, by = pts[i]
        branch = [(bx, by)] + [(bx + side * (k * 6 + rnd.randrange(4)), by + k * 7) for k in (1, 2, 3)]
        return pts, branch

    def _draw_boss_hp(self, screen, font):
        w, x, y = 160, C.BASE_W // 2 - 80, C.BASE_H - 16
        pygame.draw.rect(screen, C.BLACK, (x - 1, y - 1, w + 2, 8))
        pygame.draw.rect(screen, C.HEART_EMPTY, (x, y, w, 6))
        pygame.draw.rect(screen, C.HEART, (x, y, w * max(self.boss.hp, 0) // self.boss.max_hp, 6))
        screen.blit(font.render("BOSS", False, C.TEXT), (x - 40, y - 4))

    def _draw_bubble(self, screen, img, x, y, shown):
        """吹き出し。x, y は、しっぽの先（話している者の上）。shown は、出ている字の数（左から1文字ずつ出す）"""
        w, h = img.get_width() + 24, img.get_height() + 16
        bx = max(8, min(x - w // 2, C.BASE_W - w - 8))
        by = y - 9 - h
        pygame.draw.rect(screen, C.BLACK, (bx - 2, by - 2, w + 4, h + 4), border_radius=7)
        pygame.draw.rect(screen, C.WHITE, (bx, by, w, h), border_radius=5)
        base = by + h - 1
        pygame.draw.polygon(screen, C.BLACK, ((x - 9, base + 2), (x + 9, base + 2), (x, y + 3)))   # しっぽ（黒い縁）
        pygame.draw.polygon(screen, C.WHITE, ((x - 6, base), (x + 6, base), (x, y - 1)))
        ink = img.get_bounding_rect()     # 字そのものの範囲。これを、枠の真ん中に置く（字の絵の余白で、片寄らないように）
        tx, ty = bx + (w - ink.w) // 2 - ink.x, by + (h - ink.h) // 2 - ink.y
        screen.blit(img, (tx, ty), (0, 0, shown * C.TALK_CELL, img.get_height()))

    def _draw_boss_fade(self, screen, cam, t):
        """倒れたボスが、光になって消える: 白く光ってから、薄くなりながら昇る。光の粒が、上へ昇っていく"""
        b, total = self.boss, C.ENDING["fade"]
        r = b.rect.move(-cam, 0)
        img = b.image()
        art = C.ENEMY_ART[b.KIND]
        x = r.centerx - art["ax"]
        y = r.bottom - art["h"] if art["mode"] == "bottom" else r.centery - art["ay"]
        glow = pygame.mask.from_surface(img).to_surface(setcolor=(255, 248, 200, 255), unsetcolor=(0, 0, 0, 0))
        half = total // 2
        if t < half:
            screen.blit(img, (x, y))
            glow.set_alpha(255 * t // half)
            screen.blit(glow, (x, y))
        else:
            glow.set_alpha(255 * (total - t) // (total - half))
            screen.blit(glow, (x, y - (t - half) // 3))
        for i in range(14):     # 光の粒
            age = t - i * 3
            if age >= 0:
                px = r.left + (i * 37) % max(1, r.w) + (1 if (age // 6 + i) % 2 else -1)
                py = r.bottom - 6 - (i * 11) % 30 - int(age * (0.6 + (i % 3) * 0.3))
                pygame.draw.rect(screen, (255, 248, 200) if i % 2 else C.WHITE, (px, py, 2, 2))

    def _draw_clear(self, screen, font):
        """クリアの結果（スコア・団子・時間）。文字は、仮に英字で出している"""
        veil = pygame.Surface((C.BASE_W, C.BASE_H))
        veil.set_alpha(min(C.GAMEOVER_DIM, self.clear_t * 4))
        screen.blit(veil, (0, 0))
        sec = self.frames // C.FPS
        lines = ["STAGE CLEAR", "", "SCORE  %06d" % self.score, "DANGO  %d/%d" % (self.dango, DANGO_TOTAL),
                 "TIME   %d:%02d" % (sec // 60, sec % 60)]
        if self.clear_t >= C.CLEAR_WAIT and (self.clear_t // 30) % 2 == 0:
            lines += ["", "PRESS ENTER"]
        for i, line in enumerate(lines[:1 + self.clear_t // 20]):   # 1行ずつ出てくる
            img = font.render(line, False, C.TEXT)
            screen.blit(img, (C.BASE_W // 2 - img.get_width() // 2, 70 + i * 18))

    def _draw_dim(self, screen):
        """画面を、少しずつ暗くする"""
        t = max(0, self.over_t - C.GAMEOVER_START)
        alpha = min(C.GAMEOVER_DIM, t * C.GAMEOVER_DIM // C.GAMEOVER_FADE)
        veil = pygame.Surface((C.BASE_W, C.BASE_H))
        veil.set_alpha(alpha)
        screen.blit(veil, (0, 0))

    def _draw_gameover_text(self, screen, font):
        t = self.over_t - C.GAMEOVER_START
        if self.lives > 0:   # 残機が残っている: 「のこり N」だけ出して、自動で再開する
            if t >= C.GAMEOVER_TEXT_AT:
                img = self.a.life_text[min(self.lives, 4)]
                screen.blit(img, (C.BASE_W // 2 - img.get_width() // 2, C.BASE_H // 2 - img.get_height() // 2))
            return
        if t >= C.GAMEOVER_TEXT_AT:
            img = self.a.gameover
            img.set_alpha(min(255, (t - C.GAMEOVER_TEXT_AT) * 255 // 20))   # 少しずつ、はっきりする
            screen.blit(img, (C.BASE_W // 2 - img.get_width() // 2, C.BASE_H // 2 - img.get_height() // 2 - 14))
        if t >= C.GAMEOVER_PROMPT_AT and (t // 30) % 2 == 0:   # 点滅
            img = self.a.gameover_prompt
            screen.blit(img, (C.BASE_W // 2 - img.get_width() // 2, C.BASE_H // 2 + 40))


def keys_to_input(keys):
    held = set()
    if keys[pygame.K_LEFT]:
        held.add("left")
    if keys[pygame.K_RIGHT]:
        held.add("right")
    if keys[pygame.K_DOWN]:
        held.add("down")
    return held


KEYDOWN_MAP = {
    pygame.K_SPACE: "jump", pygame.K_UP: "jump", pygame.K_z: "attack",
    pygame.K_x: "throw", pygame.K_RETURN: "restart",
}


async def main():
    pygame.init()
    window = pygame.display.set_mode((C.BASE_W * C.SCALE, C.BASE_H * C.SCALE))
    pygame.display.set_caption(C.TITLE)
    screen = pygame.Surface((C.BASE_W, C.BASE_H))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 20)
    game = Game(title=not {"boss", "cp"} & set(sys.argv[1:]))
    if "cp" in sys.argv[1:]:     # 確認用: python main.py cp で、中間地点の手前から始める（スタート画面は出さない）
        game.player.px, game.player.py = float(CHECKPOINT[0] - 70), float(CHECKPOINT[1])
        game.enemies = [e for e in game.enemies if abs(e.cx - CHECKPOINT[0]) > 200]
    if "boss" in sys.argv[1:]:   # 確認用: python main.py boss で、ボスの場所の手前から始める（スタート画面は出さない）
        game.player.px = float(C.ARENA_X0 + 100)
        game.enemies = []
    audio = Audio()

    while True:
        pressed = set()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN and event.key in KEYDOWN_MAP:
                pressed.add(KEYDOWN_MAP[event.key])
            if event.type == pygame.KEYUP and event.key in (pygame.K_SPACE, pygame.K_UP):
                pressed.add("jump_release")
        game.step(keys_to_input(pygame.key.get_pressed()), pressed)
        for name in game.sfx:
            audio.play_sfx(name)
        game.sfx.clear()
        if game.bgm:
            audio.play_bgm(game.bgm)        # ボスの場所に入ると、曲が変わる
        else:
            audio.fade_out(C.BGM_FADE_MS)   # やられたら（クリアしたら）、曲を消していく。再開すると、また始まる
        game.draw(screen, font)
        pygame.transform.scale(screen, window.get_size(), window)
        pygame.display.flip()
        clock.tick(C.FPS)
        await asyncio.sleep(0)   # ブラウザ版では、毎フレームここで制御をブラウザに返す


if __name__ == "__main__":
    asyncio.run(main())
