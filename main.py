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
from stage import STAGE1_LEGACY, STAGES
from audio import DIR as AUDIO_DIR, Audio
from gamepad import Pad
from splash import Splash
from touch import Touch
import sprites
from sprites import Assets, Benkei, HillGust, Pillar, Boss, Boss2, Boss3, Boss4, Checkpoint, draw_zzz, HitEffect, Item, Lantern, Player, Shuriken, SlashWave, Wave, make_enemy

ENEMY_SPAWNS = STAGE1_LEGACY.spawns       # 古い短い版の月見坂の敵の配置（動作テスト用）
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
    def __init__(self, terrain=None, title=False, stage=None):
        self._terrain_fixed = terrain   # テスト用に、地形を固定する（面を変えても、これを使う）
        self.stage_i = STAGES.index(stage) if stage in STAGES else 0
        self.stage = stage or STAGES[0]
        self.a = Assets(self.stage)
        self._stone_cache = {}
        self.terrain = terrain or self.stage.terrain()
        self.use_title = title   # スタート画面から始める（クリアのあとも、スタート画面へ戻る）
        self.use_map = title     # ステージ選択の地図を出す（始まりと、面をクリアしたあと）
        self.paused = False          # ポーズ中（P キー・START）
        self.pause_t = 0
        self.thanks = False          # いま、姫を助ける場面（THANK YOU TANUKI!）を出している
        self.thanks_t = 0
        self.roll = False            # いま、エンドロール（平泉の道を歩く場面）を出している
        self.ending_screen = False   # いま、エンディング画面を出している
        self.ending_t = 0
        self.map_on = False      # いま、地図を出している
        self.map_t = 0
        self.map_to = 1          # 着く場所（面の番号）
        self.map_from = None     # 出発する場所（面の番号）。最初の1面は、歩かない
        self.map_path = []       # 駒が歩く道（点の並び）
        self.map_len = 0.0
        self.sfx = []            # このフレームに鳴らす効果音（メインループが鳴らして、空にする）
        self.rng = random.Random()   # 落とし物の、くじ
        self._songs = {}             # 曲のファイルが、あるか（名前 → あるか）
        self.level = C.LEVEL         # 難しさ（スタート画面で、左右で変える）
        self._lr = 0                 # スタート画面で、前のフレームに押していた左右（押した瞬間だけ、切り替える）
        self._ud = 0                 # 同じく、上下
        self.vol_bgm = self.vol_sfx = C.MENU["steps"]    # 曲と効果音の音量（0〜steps。スタート画面のメニューで変える）
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
        self.menu_on = False     # スタート画面で、メニューを開いている
        self.menu_i = 0          # 選んでいる項目
        self.menu_page = "main"  # メニューの画面（main = STORY・OPTION・DISCOGRAPHY・HOW TO PLAY / option = 難しさ・音量 / disco = 曲の一覧）
        self.disco_song = None   # ディスコグラフィで、いま鳴らしている曲のファイル名
        self.howto = False       # 操作説明を出している
        self._fade_cache = {}    # 崖の縁の、中景の入れ替えに使う、濃さの帯（幅ごとに作る）
        self._roll_fade = None   # エンドロールの、左の枠の右の端を暗くぼかす帯
        self.story = False       # いま、始まりの語りを流している
        self.story_t = 0
        self.story_fade = None      # 文章の上下の透け具合（初めて描くときに作る）
        self.story_run = 0       # 決定してからのフレーム数（タヌキ侍が気づいて、駆け抜けている）
        self.story_wake = 0      # 決定してから、走り出すまでのフレーム数
        self.story_woke = False  # 決定したとき、眠っていた
        self.story_x = float(C.STORY_TANUKI["x"])   # タヌキ侍の位置

    def _set_stage(self, i):
        """i 番目の面に切り替える（地形・背景・タイル・ボスの名前を、その面のものにする）"""
        self.stage_i = i
        self.stage = STAGES[i]
        self.a.load_stage(self.stage)
        self.terrain = self._terrain_fixed or self.stage.terrain()
        # 崖登りのある面は、面の高さぶんの絵に描いて、見えている所だけを、画面に写す（描く側は、縦の位置を気にしなくて済む）
        sprites.WORLD_H = self.terrain.world_h
        self._world = pygame.Surface((C.BASE_W, sprites.WORLD_H)) if sprites.WORLD_H > C.BASE_H else None
        # 崖の壁の左端（崖の上の地面が、始まる所）。崖の上の中景は、ここより右にだけ出す
        climb = self.terrain.climb
        self._wall_x = min((g[0] for g in self.terrain.ground if g[0] >= climb[0] and g[2] <= C.FLOOR_Y), default=climb[1]) if climb else 0

    def _floor_at(self, x):
        return float(self.terrain.height_at(x) or C.FLOOR_Y)

    def reset(self, stage_i=0):
        """stage_i の面を最初から（残機・スコア・中間地点も、初期値に戻す）"""
        self._set_stage(stage_i)
        self.lives = self.L["lives"]
        self.score = 0
        self._begin_stage()

    def advance(self):
        """次の面へ（体力は満タン。残機とスコアは、引き継ぐ）"""
        prev = self.stage.number
        self._set_stage(self.stage_i + 1)
        self._begin_stage()
        if self.use_map:
            self._open_map(prev)

    def _map_route(self, a, b):
        """場所 a から b（a < b）へ歩く道（点の並び）。間の面が無いとき（高館がまだ無い間）は、寄らずに、分かれ道から直接つなぐ"""
        pads, route = C.MAP_PADS, C.MAP_ROUTE
        playable = {st.number for st in STAGES}
        pts = [pads[a]]
        for k in range(a, b):
            seg = list(route[(k, k + 1)])
            if k > a and k not in playable and C.MAP_JUNCTION in seg and C.MAP_JUNCTION in pts:
                pts = pts[:len(pts) - pts[::-1].index(C.MAP_JUNCTION)]
                seg = seg[seg.index(C.MAP_JUNCTION) + 1:]
            pts += seg + [pads[k + 1]]
        return pts

    def _map_chain(self):
        """地図に点線で描く、場所の順。遊べる面と、そのあとに続く（まだ無い）面。間の、まだ無い面は、飛ばす"""
        playable = {st.number for st in STAGES}
        top = max(playable)
        return [n for n in sorted(C.MAP_PADS) if n in playable or n > top]

    def _open_map(self, prev=None):
        """地図を出す。prev（前の面の番号）から、いまの面（stage.number）まで、道を歩く。prev が無ければ、歩かずに、そこに立つ"""
        self.map_on, self.map_t, self.map_to = True, 0, self.stage.number
        self.map_from = prev if prev is not None and prev < self.map_to else None
        pts = self._map_route(self.map_from, self.map_to) if self.map_from else [C.MAP_PADS[self.map_to]]
        self.map_path = pts
        self.map_len = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))

    def _map_pos(self):
        """地図の上の、駒の位置（足元）と、右向きか、着いたか。歩いた距離から、道の上の点を求める"""
        d = min(max(0.0, (self.map_t - C.MAP_WAIT) * C.MAP_WALK_SPEED), self.map_len)
        arrived = d >= self.map_len     # 道を進むうちに d を減らすので、着いたかは、先に決めておく
        pts = self.map_path
        if len(pts) < 2:
            return pts[0], True, True
        right = True
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            seg = math.dist(a, b)
            right = b[0] >= a[0]
            if d <= seg or i == len(pts) - 2:
                u = min(1.0, d / seg) if seg else 1.0
                return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), right, arrived
            d -= seg
        return pts[-1], right, True

    def _step_map(self, pressed):
        self.map_t += 1
        walk = math.ceil(self.map_len / C.MAP_WALK_SPEED)
        if (self.map_t >= C.MAP_SKIP_WAIT and {"restart", "attack", "jump"} & pressed) or self.map_t >= C.MAP_WAIT + walk + C.MAP_HOLD:
            self.map_on = False

    def _begin_stage(self):
        self.dango = 0
        self.intro_t = 0        # 面の名前を出してからのフレーム数（遊び始めてから数える）
        self.taken = set()          # 取ったアイテム（配置表の番号）
        self.toro_broken = set()    # 壊した石灯籠（配置表の番号）。やられて再開しても、壊れたまま
        self.one_up_given = False
        self.checkpoint = Checkpoint(*self.stage.checkpoint, self.a)
        self.cp_state = None        # 中間地点を通ったときの (スコア, 団子の数, 取ったもの)
        self.boss_state = None      # ボスの場所に入ったときの (スコア, 団子の数, 取ったもの)。入り直すと、出てくる場面が短くなる
        self.boss_arena_i = 0       # boss_state を取ったのは、何番目のボスの間か
        self.arena_i = 0            # いま、次に戦うボスの間（面の途中の影のボスの間 → 最後の間）
        self.gate_cp = None         # 影のボスを倒した所の (スコア, 団子の数, 取ったもの, 再開の x)
        self.cam_ease = False       # 影を倒したあと、画面を、ゆっくり主役に戻している
        self.frames = 0             # 遊んだ時間（フレーム数。クリア画面に出す）
        self.cleared = False
        self.clear_t = 0            # クリアしてからの経過フレーム
        self._start(60, self._floor_at(60))

    def respawn(self):
        """やられて、残機が残っているとき: 中間地点（なければ最初）から、体力満タンで再開する。
        再開した場所の近くの敵は置かない。ボスまで進んでいたら、ボスの場所の入口から（ザコ敵は置かない）"""
        gate_x = self.gate_cp[3] if self.gate_cp else -1
        cp_ahead = bool(self.cp_state) and self.checkpoint.x > gate_x     # 鳥居のほうが、影を倒した所より先なら、鳥居から
        if self.boss_state:
            self.score, self.dango, taken = self.boss_state
            self.taken = set(taken)
            ax = self.stage.arenas[self.boss_arena_i]["x0"] + 100
            self._start(ax, float(self.terrain.height_at(ax) or C.FLOOR_Y), C.RESPAWN_CLEAR)
            self.enemies = [e for e in self.enemies if e.cx > ax + C.BASE_W + 60]   # ボスの間の先の敵は、いるまま
        elif self.gate_cp and not cp_ahead:
            self.score, self.dango, taken, gx = self.gate_cp
            self.taken = set(taken)
            self._start(gx, float(self.terrain.height_at(gx) or C.FLOOR_Y), C.RESPAWN_CLEAR)
        elif self.cp_state:
            self.score, self.dango, taken = self.cp_state
            self.taken = set(taken)
            self._start(self.checkpoint.x, float(self.checkpoint.y), C.RESPAWN_CLEAR)
        else:
            self.score, self.dango, self.taken = 0, 0, set()
            self._start(60, self._floor_at(60), C.RESPAWN_CLEAR)

    def _start(self, x, y, clear=0):
        """clear を渡すと（再開のとき）、その距離までの敵は置かず、少しのあいだ無敵にする"""
        self.player = Player(x, self.a)
        self.player.py = y
        self.player.safe_x, self.player.safe_y = float(x), y
        if clear:
            self.player.invincible = C.INVINCIBLE_FRAMES
        self.player.ammo = self.L["ammo"]
        keep = round(self.L["keep"] * 10)       # 難しさ「やさしい」: 敵を間引く（何番目の敵を抜くかは、いつも同じ）
        self.enemies = [make_enemy(kind, ex, self.a, self.terrain) for i, (kind, ex) in enumerate(self.stage.spawns)
                        if abs(ex - x) > clear and (i * 7 + 3) % 10 < keep]
        for e in self.enemies:                  # 難しさ「むずかしい」: 体力2以上の敵が、硬くなる（狐火と烏は、1発のまま）
            if e.max_hp >= 2:
                e.max_hp = e.hp = e.max_hp + self.L["enemy_hp"]
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
        self.items = [Item(kind, ix, iy, self.a, n) for n, (kind, ix, iy) in enumerate(self.stage.items) if n not in self.taken]
        self.lanterns = [Lantern(kind, lx, self._floor_at(lx), self.a, n, broken=n in self.toro_broken)
                         for n, (kind, lx) in enumerate(() if self._terrain_fixed else self.stage.lanterns)]   # テスト用の地形には、置かない
        self.effects = []
        self.cam_x = max(0, min(int(x) - C.BASE_W // 2, self.stage.width - C.BASE_W))
        self.land_y = float(y)      # 最後に立っていた高さ（崖登りで、画面の高さを決める）
        self.cam_y = float(self._cam_y_target())
        self.over_t = 0   # やられてからの経過フレーム
        self.dead = False
        self.msg_t = 0    # 「1UP!」を出している残りフレーム

    def _cam_y_target(self):
        """画面の上端の高さ。崖登りの区画の中だけ、着地した高さに合わせて、上下に動く。手前は崖の下、先は崖の上で、動かない"""
        climb = self.terrain.climb
        if not climb:
            return 0
        x0, x1, h = climb
        p, K = self.player, C.CLIMB_CAM
        if p.px < x0:
            return h
        if p.px >= x1:
            return 0
        return max(0, min(h, self.land_y - K["feet"]))

    def _move_cam_y(self):
        climb = self.terrain.climb
        if not climb:
            return
        p, K = self.player, C.CLIMB_CAM
        if p.on_ground:
            self.land_y = p.py
        d = self._cam_y_target() - self.cam_y
        self.cam_y += max(-K["speed"], min(K["speed"], d))
        if climb[0] <= p.px < climb[1]:     # 落ちたとき・高く跳んだときは、足元が画面から出ないように、すぐ追いかける
            self.cam_y = max(p.py - K["bottom"], min(p.py - K["top"], self.cam_y))
            self.cam_y = max(0, min(climb[2], self.cam_y))

    # --- 1フレーム進める。held は押している間のキー、pressed はこのフレームに押したキー ---
    @property
    def can_pause(self):
        """ポーズできるのは、面を遊んでいる間だけ（スタート画面・語り・地図・寸劇・結果・やられた画面では、できない）"""
        return not (self.title or self.story or self.map_on or self.thanks or self.roll or self.ending_screen or self.cleared
                    or self.ending or self.player.hp <= 0)

    def _pick_items(self, p):
        """アイテムを拾う（step から呼ぶ）。"""
        for it in self.items:
            if it.alive and p.rect.colliderect(it.rect):
                it.alive = False
                self.taken.add(it.idx)
                if it.kind == "dango":
                    self.score += C.SCORE_DANGO      # 団子: 手裏剣を投げられる数が増える（持てる数まで）
                    if it.idx >= 0:      # 敵が落とした団子は、数えない（配置した数 = 分母と、合わせる）
                        self.dango += 1
                    p.ammo = min(C.AMMO["max"], p.ammo + C.AMMO["dango"])
                    self.sfx.append(C.SFX["dango"])
                elif it.kind == "onigiri":
                    self.sfx.append(C.SFX["heal"])
                    if p.hp < C.PLAYER_HP:
                        p.hp = min(C.PLAYER_HP, p.hp + C.HEAL_ONIGIRI)
                    else:
                        self.score += C.SCORE_FULL_HP
                elif it.kind == "leaf":
                    p.power = True
                    self.sfx.append(C.SFX["power"])
                elif it.kind == "triple":
                    p.triple = True
                    self.sfx.append(C.SFX["power"])
                else:
                    p.super_t = C.SUPER_FRAMES

    def step(self, held, pressed=()):
        # ポーズ: P キー・コントローラの START で、止める・再開する。窓が後ろに回ったとき（pause_on）も、止める
        if self.paused and not self.can_pause:
            self.paused = False
        if ("pause" in pressed and (self.paused or self.can_pause)) or ("pause_on" in pressed and self.can_pause and not self.paused):
            self.paused = not self.paused
            self.pause_t = 0
            self.sfx.append(C.SFX["select"])
            return
        if self.paused:
            self.pause_t += 1
            return
        p = self.player
        if self.map_on:     # ステージ選択の地図: 駒が歩いて、着いたら、少し待つ。Enter で飛ばせる
            self._step_map(set(pressed))
            return
        if self.story:      # 始まりの語り: 決定のキーを押すまで、続く。押すと、タヌキ侍が気づいて、右へ駆け抜けて、ゲームが始まる
            self._step_story(pressed)
            return
        if self.title:      # スタート画面: 止めておく。Enter（刀・ジャンプのキーでも）で、刀の音が鳴って始まる
            self._step_title(held, pressed)
            return
        if self.ending_screen:   # エンディング: 暗い所から明るくなる。しばらくして、Enter で、スタート画面へ戻る
            self.ending_t += 1
            if {"restart", "attack", "jump"} & set(pressed) and self.ending_t >= C.ENDING_SCREEN["wait"]:
                self.ending_screen = False
                self.reset()
                self._enter_title(self.use_title)
            return
        if self.roll:       # エンドロール
            self._step_roll(set(pressed))
            return
        if self.thanks:     # 姫を助ける場面: 歩いてきて、礼の文が出る。Enter で、文を全部出す → エンドロールへ
            self._step_thanks(pressed)
            return
        if self.cleared:    # クリア: 止めて、結果を出す。Enter で最初から（スタート画面があれば、そこへ戻る）
            self._step_cleared(pressed)
            return
        if p.hp <= 0:
            self._step_dead(p, pressed)
            return
        if self.ending:     # ボスを倒したあとの寸劇（動かせない。時間も止まる）
            self._step_ending(set(pressed))
            return
        self.frames += 1
        self.intro_t += 1
        if self.boss_intro:   # ボスが出てくる場面の間は、動かせない
            held, pressed = set(), set()
        self.terrain.move(self.intro_t)     # 動く足場を進める。乗っていたら、一緒に運ぶ
        carry = self.terrain.rider(p.px, p.py) if p.on_ground else None
        if carry:
            p.px += carry[0]
            p.py += carry[1]
        if "jump" in pressed:
            if "down" in held:
                p.drop(self.terrain)    # 浮き足場の上なら、降りる（地面の上なら、ふつうに跳ぶ）
            else:
                p.jump()
        if "jump_release" in pressed:
            p.cut_jump()
        if "attack" in pressed:
            p.attack()
        if "throw" in pressed:
            p.throw()
        p.update(held, self.stage.width, self.terrain)
        self._boss_area(p)
        self.terrain.tick(self.intro_t)     # 消える光の足場
        self._gimmicks(p)
        foes = self.enemies + ([self.boss] if self.boss else [])
        if p.release:   # 手裏剣（三方手裏剣なら、前・斜め上・斜め下の3つ）
            self.throw_n += 1
            for vy in (C.TRIPLE_VY if p.triple else (0.0,)):
                self.shurikens.append(Shuriken(*p.shuriken_spawn(), self.a, vy))
                self.shurikens[-1].throw_id = self.throw_n   # 同じ1投げの手裏剣（三方手裏剣の3つ）は、同じ番号
        if p.slash:
            self.slashes.append(SlashWave(*p.slash_spawn(), self.a))
        for e in foes:
            if self.boss_on and e is not self.boss and not e.dying:    # ボスと戦っている間、ザコ敵は、動かない（間の外から、狐火や矢が入ってこないように）
                continue
            e.update(p.rect, self.stage.width, self.terrain)
            spawned = e.spawned
            if spawned:
                self.waves.extend(spawned)
                spawned.clear()
        for w in self.waves:
            w.update(self.stage.width)
        for s in self.slashes:
            s.update(self.stage.width)
        for it in self.items:
            it.update(self.terrain)
        self.checkpoint.update()
        for s in self.shurikens:
            s.update(self.stage.width)
            if not -C.SHURIKEN_W <= s.px - self.cam_x <= C.BASE_W + C.SHURIKEN_W:     # 画面の端まで飛ぶ。画面の外の敵には、当たらない
                s.alive = False

        sword = p.sword_rect()
        self._hit_foes(p, foes, sword)
        self._hit_lanterns(sword)
        self._drop_items()
        self._pick_items(p)
        # 中間地点（鳥居）を通る
        if not self.checkpoint.active and p.rect.colliderect(self.checkpoint.rect):
            self.checkpoint.activate()
            self.sfx.append(C.SFX_CHECKPOINT)
            self.cp_state = (self.score, self.dango, frozenset(self.taken))
        if self.msg_t:
            self.msg_t -= 1
        self._hit_by_waves(p, sword)
        self._touch_foes(p, foes)

        self._boss_shake(p)
        self.bar_t = max(0, min(C.BOSS_INTRO["bar_frames"], self.bar_t + (1 if self.boss_intro else -1)))
        self.enemies = [e for e in self.enemies if e.alive]
        self._boss_defeated()
        self.shurikens = [s for s in self.shurikens if s.alive]
        self.waves = [w for w in self.waves if w.alive]
        self.slashes = [s for s in self.slashes if s.alive]
        self.items = [it for it in self.items if it.alive]
        for fx in self.effects:
            fx.update()
        self.effects = [fx for fx in self.effects if fx.alive]

        self._follow_cam(p)
        self._move_cam_y()

    def _step_story(self, pressed):
        """始まりの語りの場面（step から呼ぶ）。"""
        T = C.STORY_TANUKI
        self.story_t += 1
        if self.story_run:
            self.story_run += 1
            if self.story_run > self.story_wake:    # 気づいた（飛び起きた）あと、走り出す
                self.story_x += T["run_speed"]
            if self.story_x > C.BASE_W + T["head_x"]:
                self.story = False
                if self.use_map:
                    self._open_map()
        elif self.story_t > C.STORY_SKIP_WAIT and {"restart", "attack", "jump"} & set(pressed):
            self.story_wake = T["wake"] if self.story_asleep else T["notice"]
            self.story_woke = self.story_asleep     # 眠っていたか（飛び起きる動きにする）
            self.story_run = 1

    def _step_title(self, held, pressed):
        """スタート画面とメニュー（step から呼ぶ）。"""
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
        # 決定のキー（上キーは、ジャンプと同じキーなので、上を押している間のジャンプは、決定にしない）
        decide = bool({"restart", "attack"} & set(pressed)) or ("jump" in pressed and "up" not in held)
        lr = ("right" in held) - ("left" in held)
        ud = ("down" in held) - ("up" in held)
        step_lr, step_ud = (lr if lr != self._lr else 0), (ud if ud != self._ud else 0)   # 押した瞬間だけ
        self._lr, self._ud = lr, ud
        if self.howto:      # 操作説明: 決定で、メニューに戻る
            if decide:
                self.howto = False
                self.sfx.append(C.SFX["decide"])
            return
        if not self.menu_on:
            if decide:      # 1回目の決定: メニューを開く
                self.menu_on, self.menu_page, self.menu_i = True, "main", 0
                self.sfx.append(C.SFX["decide"])
                return
        else:
            rows, S = C.MENU["pages"][self.menu_page], C.MENU["steps"]
            if step_ud:     # 上下で、項目を選ぶ（選ぶ音）
                self.menu_i = (self.menu_i + step_ud) % len(rows)
                self.sfx.append(C.SFX["cursor"])
            row = rows[self.menu_i]
            turn = step_lr or (1 if decide and row == "level" else 0)     # LEVEL は、決定でも、次へ送れる（端まで行ったら、最初へ戻る）
            if turn and row == "level":
                order = C.LEVEL_ORDER
                i = order.index(self.level) + turn
                self.level = order[i % len(order) if not step_lr else max(0, min(i, len(order) - 1))]
                self.lives = self.L["lives"]
                self.sfx.append(C.SFX["cursor"])
            elif step_lr and row == "music":
                self.vol_bgm = max(0, min(S, self.vol_bgm + step_lr))
                self.sfx.append(C.SFX["cursor"])
            elif step_lr and row == "sound":
                self.vol_sfx = max(0, min(S, self.vol_sfx + step_lr))
                self.sfx.append(C.SFX["cursor"])       # 変えた音量で、鳴る（大きさを、耳で確かめられる）
            if decide and row == "story":           # 始める
                self.start_t = C.TITLE_START
                self.flash_t = 0
                self.sfx.append(C.SFX_SWORD)
                return
            if decide and row == "option":
                self.menu_page, self.menu_i = "option", 0
                self.sfx.append(C.SFX["decide"])
            elif decide and row == "disco":
                self.menu_page, self.menu_i = "disco", 0
                self.sfx.append(C.SFX["decide"])
            elif decide and self.menu_page == "disco" and row != "back":     # 曲を選んで決定: その曲を鳴らす（もう一度で、止める）
                song = C.DISCO[int(row[1:])][0]
                self.disco_song = None if self.disco_song == song else song
            elif decide and row == "back":
                came = "disco" if self.menu_page == "disco" else "option"
                self.menu_page, self.menu_i, self.disco_song = "main", C.MENU["pages"]["main"].index(came), None
                self.sfx.append(C.SFX["decide"])
            elif decide and row == "howto" and self.a.howto:
                self.howto = True
                self.sfx.append(C.SFX["decide"])
                return
        if self.title_t == self.thunder_at:                       # 稲光
            self.flash_t = C.TITLE_FLASH
        elif self.title_t == self.thunder_at + C.THUNDER_DELAY:   # 少し遅れて、雷鳴
            self.sfx.append(C.SFX_THUNDER)
            self.thunder_n += 1
            self.thunder_at += C.TITLE_THUNDER[self.thunder_n % len(C.TITLE_THUNDER)]

    def _step_thanks(self, pressed):
        """姫を助ける場面（step から呼ぶ）。"""
        self.thanks_t += 1
        n = self._thanks_shown()
        if 0 < n <= sum(len(s) for s in C.THANKS["lines"]) and self._thanks_typed != n and n % 2:
            self.sfx.append(C.SFX_TALK_HIGH)
        self._thanks_typed = n
        if self.thanks_t == self._thanks_at("hop"):
            self.sfx.append(C.SFX["heal"])
        if {"restart", "attack", "jump"} & set(pressed):
            if self.thanks_t < self._thanks_at("done"):
                self.thanks_t = self._thanks_at("done")     # 途中で押すと、文を全部出す
            elif self.thanks_t >= self._thanks_at("done") + C.THANKS["wait"]:
                self.thanks = False
                self._start_roll()

    def _step_cleared(self, pressed):
        """面をクリアしたあとの、結果の画面（step から呼ぶ）。"""
        self.clear_t += 1
        count_end = C.CLEAR_SCORE_AT + C.CLEAR_COUNT
        if C.CLEAR_SCORE_AT < self.clear_t < count_end and self.clear_t % 3 == 0:
            self.sfx.append(C.SFX["cursor"])    # 数字が増える間の「ピ」
        if "restart" in pressed and C.CLEAR_SCORE_AT <= self.clear_t < count_end:
            self.clear_t = count_end            # 増えている間に押すと、最終値へ飛ぶ
        elif "restart" in pressed and self.clear_t >= C.CLEAR_WAIT:
            if self.stage_i + 1 < len(STAGES):
                self.advance()
            elif self.use_title:    # 最後の面: 姫を助ける場面へ（そのあと、エンディングの絵）
                self.thanks, self.thanks_t, self._thanks_typed = True, 0, 0
            else:
                self.reset()
                self._enter_title(self.use_title)

    def _step_dead(self, p, pressed):
        """やられたあと: 残機があれば復活、なければゲームオーバー（step から呼ぶ）。"""
        if not self.dead:
            self.dead = True
            self.lives -= 1
            if self.lives <= 0:
                self.sfx.append(C.SFX["gameover"])
        self.over_t += 1
        p.defeat_t = self.over_t
        if self.lives > 0:
            if self.over_t >= C.RESPAWN_AT:
                self.respawn()
        elif "restart" in pressed and self.over_t >= C.GAMEOVER_WAIT:
            self.reset()               # ゲームオーバーは、スタート画面へ戻る（残機は戻る）
            self._enter_title(self.use_title)

    def _hit_foes(self, p, foes, sword):
        """主人公の攻撃（刀・手裏剣・光波）が、敵に当たる（step から呼ぶ）。"""
        # 刀 → 敵（1振りにつき、同じ敵に1回だけ）
        if sword:
            for e in foes:
                if e.active and e.last_swing != p.swing_id and sword.colliderect(e.rect):
                    e.last_swing = p.swing_id
                    e.hit(C.SWORD_DAMAGE)
        # 手裏剣・強化中の光波 → 敵（当たると、消える）
        for s in self.shurikens + self.slashes:
            for e in foes:
                if s.alive and e.active and s.rect.colliderect(e.rect):
                    s.alive = False
                    if s.throw_id is None or e.last_throw != s.throw_id:   # 手裏剣は、1投げにつき、同じ敵に当たるのは1つだけ（残りは、消えるだけ）
                        e.hit(s.damage)
                    if s.throw_id is not None:
                        e.last_throw = s.throw_id
                    self.effects.append(HitEffect(*s.rect.center, self.a))

    def _hit_lanterns(self, sword):
        """主人公の攻撃が、石灯籠に当たる（step から呼ぶ）。"""
        # 刀・手裏剣・光波 → 石灯籠（壊すと、中の物が出る）
        for lt in self.lanterns:
            lt.update()
            if not lt.active:
                continue
            broke = bool(sword and sword.colliderect(lt.rect))
            for s in self.shurikens + self.slashes:
                if not broke and s.alive and s.rect.colliderect(lt.rect):
                    s.alive = False
                    broke = True
            if broke and lt.hit():
                self.toro_broken.add(lt.idx)
                self.effects.append(HitEffect(*lt.rect.center, self.a))
                self.items.append(Item(lt.kind, lt.rect.centerx, lt.rect.centery, self.a, drop=True))

    def _drop_items(self):
        """倒した敵が、物を落とす（step から呼ぶ）。"""
        # 倒した敵が、物を落とす（ボスは落とさない）
        for e in self.enemies:
            if e.dying and not e.dropped:
                e.dropped = True
                kind = e.sure_drop or drop_kind(self.rng.random() / self.L["drops"])    # 必ず落とす敵（立ち往生）もいる
                if kind:
                    self.items.append(Item(kind, e.rect.centerx, e.rect.centery, self.a, drop=True))

    def _cut_effect(self, w):
        """斬られた・弾かれた弾が、あとに残す物を出す（矢は、折れて落ちる）。"""
        fx = w.cut_effect()
        if fx is not None:
            self.effects.append(fx)

    def _hit_by_waves(self, p, sword):
        """敵の弾（光波・矢・風）の当たり判定: 押し戻す・弾かれる・刀で斬る・主人公に当たる（step から呼ぶ）。"""
        # 扇の風: ダメージはなく、押し戻す（壁や、画面の端より先へは、押されない）
        for w in self.waves:
            if w.push and w.alive and p.rect.colliderect(w.rect):
                nx = self.terrain.push_x(p.px, p.px + w.dir * w.push, p.py, C.PLAYER_W / 2)
                p.px = max(C.PLAYER_W / 2, min(nx, self.stage.width - C.PLAYER_W / 2))
        # 立ち往生は、敵の矢や光波も、弾いて消す
        for e in self.enemies:
            if e.solid:
                for w in self.waves:
                    if w.alive and not w.push and w.rect.colliderect(e.rect):
                        w.alive = False
                        e.hit(0)
                        self._cut_effect(w)
        # 刀 → 光波（刀で斬ると消せる。手裏剣は通り抜ける）
        if sword:
            for w in self.waves:
                if w.alive and w.cuttable and sword.colliderect(w.rect.inflate(*w.cut_pad)):
                    w.alive = False
                    self.sfx.append(C.SFX["cut"])
                    self.effects.append(HitEffect(*w.rect.center, self.a))
                    self._cut_effect(w)
        # 光波 → 主人公（無敵のあいだは、すり抜ける）
        for w in self.waves:
            if w.alive and not w.push and not p.untouchable and p.rect.colliderect(w.rect):
                w.alive = False
                p.take_damage(w.px, w.damage)

    def _touch_foes(self, p, foes):
        """敵に触れたときの当たり判定（step から呼ぶ）。"""
        # 敵 → 主人公（踏んでも倒せない。触れるとダメージ）
        for e in foes:
            if e.clang:      # 立ち往生が、攻撃を弾いた
                e.clang = False
                self.sfx.append(C.SFX_CLANG)
            if e.solid:      # 立ち往生: ダメージは無い。来たほうへ、押し戻す（上に乗っても、横へ落とす）
                if p.rect.colliderect(e.rect):
                    half = (e.w + C.PLAYER_W) / 2
                    side = -1 if p.px < e.cx else 1
                    nx = self.terrain.push_x(p.px, e.cx + side * half, p.py, C.PLAYER_W / 2)
                    p.px, p.vx = max(C.PLAYER_W / 2, min(nx, self.stage.width - C.PLAYER_W / 2)), 0.0
                continue
            if e.active and p.rect.colliderect(e.rect):
                if p.super_t and e is not self.boss:    # スーパータヌキ: 触れたザコ敵を、倒す（ボスには効かない）
                    e.hit(e.hp)
                    self.effects.append(HitEffect(*e.rect.center, self.a))
                else:
                    p.take_damage(e.rect.centerx, e.P["touch"])

    def _boss_shake(self, p):
        """ボスの構え・着地で、画面を揺らす（step から呼ぶ）。"""
        if self.boss and self.boss.alert:     # ボスが構えに入った: 小さく揺らす
            self.boss.alert = False
            self.shake_t = max(self.shake_t, 3)
        if self.boss and self.boss.landed:   # ボスが着地した: 画面を揺らす（降ってきたときは、大きく）
            self.boss.landed = False
            self.shake_t = C.BOSS_INTRO["shake"] if self.boss_intro else C.LEAP_SHAKE
            self.sfx.append(C.SFX["thud"])
            if self.boss_intro:     # 降ってきたボスに、タヌキ侍が驚く
                self.sfx.append(C.SFX["startle"])
                p.startle_t = C.STARTLE
                p.facing = 1 if self.boss.cx > p.px else -1
        elif self.shake_t:
            self.shake_t -= 1

    def _boss_defeated(self):
        """ボス（面の途中の影も）を倒したあとの処理（step から呼ぶ）。"""
        if self.boss and self.boss.dying and self.boss.midway:    # 影を倒した: 倒れて消えたら、先へ進める
            if not self.boss.shadow_done:
                self.boss.shadow_done = True
                self.waves, self.shurikens, self.slashes = [], [], []
                self.score += C.SCORE_SHADOW
            if not self.boss.alive:
                self._gate_cleared()
        elif self.boss and self.boss.dying:   # ボスを倒した: すぐ寸劇へ（ボスは吹っ飛んで、倒れたまま残る）
            self.waves, self.shurikens, self.slashes = [], [], []
            self.score += C.SCORE_BOSS
            self.ending = 1

    def _follow_cam(self, p):
        """画面を、主人公に合わせて、横に動かす（step から呼ぶ）。"""
        if not self.boss_on:   # ボスと戦っている間は、画面を動かさない（入ったときだけ、右端まで流す）
            target = max(0, min(p.rect.centerx - C.BASE_W // 2, self.stage.width - C.BASE_W))
            if self.cam_ease and abs(target - self.cam_x) > C.BOSS_CAM_SPEED:     # 影を倒したあとは、ゆっくり戻す
                self.cam_x += C.BOSS_CAM_SPEED if target > self.cam_x else -C.BOSS_CAM_SPEED
            else:
                self.cam_x, self.cam_ease = target, False
        elif self.cam_x < self._arena()["x0"]:
            self.cam_x = min(self._arena()["x0"], self.cam_x + C.BOSS_CAM_SPEED)

    def _end_phase(self):
        """寸劇の、いまの場面と、その場面に入ってからのフレーム数。
        wait（間） → boss（ボスのひとこと） → fade（光になって消える） → reply（タヌキ侍が返す） → run（右へ駆け抜ける）"""
        t = self.ending - 1
        for name in ("wait", "boss", "fade", "reply"):
            n = self._end_len(name)
            if t < n:
                return name, t
            t -= n
        return "run", t

    def _end_len(self, name):
        """エンディングの各場面の長さ"""
        n = C.ENDING[name]
        if name == "reply" and self.stage.thought:
            n = max(n, self._talk_cells(name) * C.ENDING["type"] + C.THOUGHT["hold"])
        return n

    def _talk_cells(self, name):
        if name != "boss" and self.stage.thought:      # 返事の代わりに、食べ物を思い浮かべる: 物の数 + 吹き出しがふくらむ分
            return len(self.stage.thought) * C.THOUGHT["per"] + C.THOUGHT["grow"]
        img = self.a.talk_boss if name == "boss" else self.a.talk_tanuki
        return img.get_width() // C.TALK_CELL

    def _talk_shown(self, name, t):
        """せりふが出始めてから t フレームで、何文字出ているか（途中に、間が入ることがある）"""
        at, wait = C.TALK_PAUSE.get(name, (0, 0))
        if name != "boss" and self.stage.thought:
            wait = 0
        k = t // C.ENDING["type"] + 1
        if wait and k > at:
            k = max(at, (t - wait) // C.ENDING["type"] + 1)
        return min(k, self._talk_cells(name))

    def _step_ending(self, pressed):
        E = C.ENDING
        p = self.player
        if self.boss:
            self.boss.update(p.rect, self.stage.width, self.terrain)
            if self.boss.landed:    # 吹っ飛んだボスが落ちた: 画面を揺らす
                self.boss.landed = False
                self.shake_t = C.LEAP_SHAKE
        if not self.end_ready:      # ボスが倒れきって、タヌキ侍が話す場所に着くまで、待つ
            self.end_wait += 1
            dx = self.stage.end_tanuki_x - p.px
            near = abs(dx) <= C.MAX_SPEED
            p.update(set() if near else {"right" if dx > 0 else "left"}, self.stage.width, self.terrain)
            p.rest_t = 0
            if near and p.on_ground:
                p.px, p.vx, p.facing = float(self.stage.end_tanuki_x), 0.0, 1
            arrived = near and p.on_ground and not self.boss.alive
            if arrived or self.end_wait >= C.END_BLOW["limit"]:
                self.end_ready = True
            self._end_common()
            return
        name, t = self._end_phase()
        talk = {"boss": C.SFX_TALK_LOW, "reply": C.SFX_TALK_HIGH}
        if name in talk and t >= E["skip"] and pressed & {"attack", "jump", "restart"}:
            thinking = name == "reply" and bool(self.stage.thought)
            typed = self._talk_cells(name) * E["type"] + (0 if thinking else C.TALK_PAUSE.get(name, (0, 0))[1])
            # キーを押すと、字が出ている途中なら全部出す。出きっていれば、次へ送る
            self.ending += (typed - t - 1) if t < typed - 1 else (self._end_len(name) - t - 1)
        self.ending += 1
        name, t = self._end_phase()
        more = name in talk and (t == 0 or self._talk_shown(name, t) > self._talk_shown(name, t - 1))
        if name == "reply" and self.stage.thought:     # 考えごと: 食べ物が浮かぶたびに、ポンと鳴らす（字の音は、鳴らさない）
            k = self._talk_shown(name, t) - C.THOUGHT["grow"] - 1
            if more and k >= 0 and k % C.THOUGHT["per"] == 0:
                self.sfx.append(C.SFX["dango"])
        elif more:
            self.sfx.append(talk[name])    # 字が1文字出るたびに、ピッと鳴らす
        if name == "fade" and t == 0:
            self.sfx.append(C.SFX_CHECKPOINT)
        if name in ("reply", "run"):
            self.boss = None
        if name == "run":      # 面の端の先まで走って、画面から出たら、結果へ
            p.update({"right"}, self.stage.width + 120, self.terrain)
            if p.px - self.cam_x >= C.BASE_W + E["exit"]:
                self.cleared = True
                self.sfx.append(C.SFX["clear"])
        else:
            p.update(set(), self.stage.width, self.terrain)
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

    def _trap_spots(self, trap):
        x0, x1, gap, _ = trap
        return [x for x in range(x0, x1 + 1, gap) if self.terrain.height_at(x) is not None]

    def _gimmicks(self, p):
        """面の仕掛け（山おろし・光の柱の廊下）。主人公が近くにいる間だけ動く。ボスと戦っている間は、止まる"""
        if self.boss_on or p.hp <= 0:
            return
        t = self.intro_t
        for x0, x1, period in self.stage.winds:
            if x0 - C.WIND["near"] <= p.px <= x1 and t % period == 0:
                self.waves.append(HillGust(x1 - 10, -1, self.a, self.terrain, x1 - x0))
        for trap in self.stage.traps:
            x0, x1, _, period = trap
            if x0 - C.TRAP["near"] <= p.px <= x1 + 60:
                for k, x in enumerate(self._trap_spots(trap)):
                    if t % period == k * C.TRAP["stagger"] % period:
                        self.waves.append(Pillar(x, self.terrain.height_at(x), self.a, quiet=k > 0))     # 予告の音は、一巡りに1回だけ

    def _draw_traps(self, screen, cam):
        """光の柱が落ちる場所の、床の印（いつも見える。金の輪）"""
        for trap in self.stage.traps:
            for x in self._trap_spots(trap):
                sx, y = x - cam, round(self.terrain.height_at(x))
                if -20 < sx < C.BASE_W + 20:
                    pygame.draw.ellipse(screen, (60, 36, 8), (sx - 12, y - 4, 24, 7))
                    pygame.draw.ellipse(screen, (255, 244, 170), (sx - 10, y - 3, 20, 5), 1)

    @property
    def L(self):
        """いまの難しさの数字（config.LEVELS）"""
        return C.LEVELS[self.level]

    def _arena(self):
        """いま、戦っている（次に戦う）ボスの間"""
        arenas = self.stage.arenas
        return arenas[min(self.arena_i, len(arenas) - 1)]

    def _boss_area(self, p):
        """ボスの間に少し入ったら、ボスが出る（画面は、ボスの間の右端まで流れて止まる。ボスと、離れて向き合う）。
        そこからは、左へ戻れない（面の途中の影のボスの間は、右にも出られない）。最後の間は、面の端"""
        if not self.boss_on:    # 確認用に先へ飛んだときなど、通り過ぎたボスの間は、飛ばす
            while self.arena_i < len(self.stage.arenas) - 1 and p.px > self.stage.arenas[self.arena_i]["x1"] + 60:
                self.arena_i += 1
        ar = self._arena()
        if not self.boss_on and p.hp > 0 and p.px >= ar["x0"] + C.BOSS_TRIGGER:
            self.boss_on = True
            self.cam_x = max(0, min(p.rect.centerx - C.BASE_W // 2, ar["x0"]))   # ここから、右端まで流す
            cls = self._boss_class(ar["kind"])
            final = not ar["shadow"]
            pattern = self.stage.boss_pattern if final else {"boss3": C.BOSS3_PATTERN, "benkei": C.BENKEI_PATTERN}.get(ar["kind"])
            self.boss = cls(ar["boss_x"], self.a, self.terrain.height_at(ar["boss_x"]), ar["x0"], ar["x1"],
                            quick=self.boss_state is not None or not final, end_x=ar["boss_x"], pattern=pattern)
            self.boss.max_hp = self.boss.hp = max(1, round(self.boss.max_hp * self.L["boss_hp"]))
            if not final:
                self.boss.midway = True     # 面の途中の相手（影のボス・中ボス）: 倒すと、先へ進める
                if ar["kind"] != "benkei":
                    self.boss.make_shadow()
            self.boss_state = (self.score, self.dango, frozenset(self.taken))
            self.boss_arena_i = self.arena_i
            if final:
                self.enemies = []   # 最後のボスの間では、ザコ敵は、ここですべて消える
            else:                   # 影の間では、その間と、まわりの敵だけが消える（先の敵は、そのまま。戦っている間は、動かない）
                self.enemies = [e for e in self.enemies if not (ar["x0"] - 120 <= e.cx <= ar["x1"] + 60)]
            self.waves = []
        if self.boss_on and p.px < ar["x0"] + C.PLAYER_W / 2:
            p.px = ar["x0"] + C.PLAYER_W / 2
            p.vx = 0.0
        if self.boss_on and ar["shadow"] and p.px > ar["x1"] - C.PLAYER_W / 2:
            p.px = ar["x1"] - C.PLAYER_W / 2
            p.vx = 0.0

    def _boss_class(self, kind):
        return {"boss2": Boss2 if self.a.boss2 else Boss, "boss3": Boss3, "boss4": Boss4, "benkei": Benkei}.get(kind, Boss)

    def _gate_cleared(self):
        """影を倒して、光になって消えた: 先へ進める。おにぎりが出て、やられたら、ここから再開する"""
        ar = self._arena()
        self.boss, self.boss_on = None, False
        self.arena_i += 1
        self.boss_state = None
        self.cam_ease = True
        fx = ar["boss_x"] - 70
        self.items.append(Item("onigiri", fx, float(self.terrain.height_at(fx) or C.FLOOR_Y) - 40, self.a, drop=True))
        rx = ar["x1"] + 60
        self.gate_cp = (self.score, self.dango, frozenset(self.taken), rx)
        self.sfx.append(C.SFX_CHECKPOINT)

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
        story = C.BGM_STORY if self.story_bgm else None
        if self.ending_screen or self.thanks or self.roll:
            return self._song(C.BGM_ENDING) or story
        if self.title:
            return self.disco_song or self._song(C.BGM_TITLE)
        if self.player.hp <= 0 or self.cleared or self.ending:
            return None
        if self.map_on:
            return self._song(C.BGM_MAP) or story
        if self.story:
            return story
        if self.boss and self.boss.state in ("wait", "drop"):
            return None
        n = self.stage.number
        if self.boss_on:
            mid = self.boss.midway
            return self._song(C.BGM_MIDBOSS if mid else C.BGM_BOSS_N % n) or self.stage.bgm_boss
        if self.player.super_t and self.super_bgm:
            return C.BGM_SUPER
        return self._song(C.BGM_STAGE_N % n) or self.stage.bgm

    def _song(self, name):
        """曲のファイルがあれば、その名前。無ければ None（あるかどうかは、一度だけ調べる）"""
        if name not in self._songs:
            self._songs[name] = os.path.exists(os.path.join(AUDIO_DIR, name))
        return name if self._songs[name] else None

    # --- 描画 ---
    def draw(self, screen, font):
        self._font = font
        if self.thanks:
            self._draw_thanks(screen, font)
            return
        if self.roll:
            self._draw_roll(screen)
            return
        if self.ending_screen:
            self._draw_ending_screen(screen)
            return
        if self.map_on:
            self._draw_map(screen)
            return
        if self.story:
            self._draw_story(screen)
            return
        if self.title and self.a.title_bg:   # スタート画面の絵があれば、それだけを出す
            screen.blit(self.a.title_bg, (0, 0))
            self._draw_title(screen, dim=False)
            return
        cam, cy = self.cam_x, round(self.cam_y) if self._world else 0
        world = self._world or screen       # 崖登りのある面は、縦に長い絵に描く（cy が、見えている範囲の上端）
        world.set_clip(pygame.Rect(0, cy, C.BASE_W, C.BASE_H))
        span = self.stage.width - C.BASE_W
        # 奥の層ほどゆっくり動く（画像の余りの幅をカメラの移動量に割り振る）
        sky_x = round(cam * (self.a.sky.get_width() - C.BASE_W) / span)
        mid_x = round(cam * (self.a.mid.get_width() - C.BASE_W) / span)
        climb = self.terrain.climb if self._world else None
        extra = self.a.sky.get_height() - C.BASE_H      # 縦に長い空: 崖の下では、絵の下の端を見せ、登るにつれて、上へ移る
        world.blit(self.a.sky, (-sky_x, cy - (round(extra * cy / climb[2]) if climb and extra > 0 else extra)))
        if climb:   # 中景は、画面より遅く動く。崖の下の中景は、登ると下へ沈み、崖の上の中景は、崖より右にだけ、上から降りてくる
            f = C.CLIMB_BG["mid"] if self.stage.mid_follow is None else self.stage.mid_follow
            wall = max(0, min(C.BASE_W, self._wall_x - cam))
            band = C.CLIMB_BG["overhang"]       # 縁のまわりで、2つの中景を、だんだん入れ替える幅（切れ目が、すっぱり出ないように）
            off_down, off_up = round((climb[2] - cy) * f), -round(cy * f)
            if wall < C.BASE_W:
                self._blit_mid(world, 0, wall, mid_x, off_down, cy, "out", min(band, wall))         # 崖の下: 縁へ向かって、薄くなる
                self._blit_mid(world, wall, C.BASE_W, mid_x, off_up, cy, "in", min(band, C.BASE_W - wall))    # 崖の上: 縁（より右）から、濃くなる。崖の外には、出さない
            else:
                self._blit_mid(world, 0, C.BASE_W, mid_x, off_down, cy, None, 0)
        else:
            world.blit(self.a.mid, (-mid_x, cy))
        self._draw_ground(world, cam)
        self._draw_stele(world, cam)
        self._draw_traps(world, cam)
        for lt in self.lanterns:
            lt.draw(world, cam)
        for e in self.enemies:
            e.draw(world, cam)
        end = self._end_phase() if self.end_ready else ("", 0)
        if self.boss and end[0] == "fade":
            self._draw_boss_fade(world, cam, end[1])
        elif self.boss:
            self.boss.draw(world, cam)
        for s in self.shurikens:
            s.draw(world, cam)
        for w in self.waves:
            w.draw(world, cam)
        for s in self.slashes:
            s.draw(world, cam)
        for it in self.items:
            it.draw(world, cam)
        self.checkpoint.draw(world, cam)
        self.player.draw(world, cam)
        for fx in self.effects:
            fx.draw(world, cam)
        self.checkpoint.draw_fx(world, cam)
        world.set_clip(None)
        if world is not screen:
            screen.blit(world, (0, -cy))
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
            self._draw_bubble(screen, self.a.talk_boss, r.centerx - cam, self._boss_tail_y(r) - cy, self._talk_shown(*end))
        elif end[0] == "reply":
            r = self.player.rect
            if self.stage.thought:
                self._draw_thought(screen, r.centerx - cam, r.top - cy - 2, self._talk_shown(*end))
            else:
                self._draw_bubble(screen, self.a.talk_tanuki, r.centerx - cam, r.top - cy - 4, self._talk_shown(*end))
        self._draw_hud(screen, font)
        self._draw_stage_title(screen)
        if self.player.hp <= 0:
            self._draw_gameover_text(screen, font)
        if self.cleared:
            self._draw_clear(screen, font)
        if self.paused:
            self._draw_pause(screen, font)

    def _draw_pause(self, screen, font):
        """ポーズ: 画面を暗くして、真ん中に「PAUSE」。下に、再開のしかた（点滅）"""
        dim = pygame.Surface((C.BASE_W, C.BASE_H))
        dim.set_alpha(120)
        screen.blit(dim, (0, 0))
        for text, y, scale, blink in (("PAUSE", C.BASE_H // 2 - 24, 2, False), ("P KEY / START BUTTON", C.BASE_H // 2 + 14, 1, True)):
            if blink and (self.pause_t // 30) % 2:      # 再開のしかたは、点滅。「PAUSE」は、出したまま
                continue
            for color, off in ((C.BLACK, scale), (C.WHITE if blink else (255, 236, 150), 0)):
                img = font.render(text, False, color)
                if scale > 1:
                    img = pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))
                screen.blit(img, (C.BASE_W // 2 - img.get_width() // 2 + off, y + off))

    def _draw_ground(self, screen, cam):
        tiles = self.a.tiles
        top = tiles[1]
        view = screen.get_clip()    # 見えている範囲（崖登りのある面では、縦に長い絵の一部）
        # 穴の底は暗くしておく（地面のない所は、ここが見える）
        if self.a.water:   # 池の水面（穴の中。地面は、このあとで上から描くので、すき間にだけ見える）
            self._draw_water(screen, cam)
        else:
            # 穴の所だけを塗る（前は、画面の幅いっぱいに塗っていて、いちばん低い地面の、草の葉先のすき間から、穴の色が、線になって見えた）。
            # 崖登りのある面は、崖の手前と先とで、穴の底の高さが違う（手前は、崖の高さぶん、低い）
            g = self.terrain.ground
            for (_, a, _), (b, _, _) in zip(g, g[1:]):
                bx0, bx1 = max(0, a - cam), min(C.BASE_W, b - cam)
                if bx1 <= bx0:
                    continue
                y0 = C.GROUND_Y + self.terrain.depth_at(a)
                pygame.draw.rect(screen, self.stage.pit_deep or self.stage.pit, (bx0, y0, bx1 - bx0, max(0, view.bottom - y0)))
                deep = self.stage.pit_deep
                n = (C.BASE_H - C.GROUND_Y + 7) // 8
                for k in range(n if deep else 0):    # 下へ行くほど、深い色にする（8ドットごとの段）。明るい霞の谷が、のっぺりした白い帯に見えないように
                    u = (k + 1) / n
                    color = tuple(round(a + (b - a) * u) for a, b in zip(self.stage.pit, deep))
                    pygame.draw.rect(screen, color, (bx0, y0 + k * 8, bx1 - bx0, 8))
            self._draw_pit_haze(screen, cam)
        for x0, x1, top_y in self.terrain.ground:
            sx0, sx1 = max(x0 - cam, 0), min(x1 - cam, C.BASE_W)
            if sx1 <= sx0:
                continue
            tile_y = top_y - (C.FLOOR_Y - C.GROUND_Y)   # 地面の上端のタイルの高さ
            screen.set_clip(pygame.Rect(sx0, view.y, sx1 - sx0, view.h))   # 区間の端で、タイルを切る
            for i in range(max(x0, cam) // 32, (min(x1, cam + C.BASE_W) - 1) // 32 + 1):
                x = i * 32 - cam
                screen.blit(top, (x, tile_y))
                y = tile_y + top.get_height()
                row = max(0, (view.y - y) // 32)       # 見えている所より上の段は、飛ばす（高い崖は、縦に長い）
                y += row * 32
                while y < view.bottom:
                    if self.a.cliff and row >= C.CLIMB_BG["cliff_rows"]:       # 高い崖の壁は、岩肌のタイルで埋める
                        screen.blit(self.a.cliff[C.CLIFF_PATTERN[(i * 7 + row * 5) % len(C.CLIFF_PATTERN)] % len(self.a.cliff)], (x, y))
                    elif self.stage.fill_rows:      # 段ごとに、決まったタイル（堂の中の床: 朱の帯の下に、黒漆）
                        screen.blit(tiles[self.stage.fill_rows[min(row, len(self.stage.fill_rows) - 1)]], (x, y))
                    else:
                        screen.blit(tiles[FILL_PATTERN[(i * 7 + row * 5) % len(FILL_PATTERN)]], (x, y))
                    y += 32
                    row += 1
        screen.set_clip(view)
        # 浮き足場（絵があれば、礎石などの絵。無ければ、地面の上端のタイルを横に並べる）
        def platform(n, x0, x1, top_y):
            ledge = self.a.ledges.get(x1 - x0 + C.STONE_PAD * 2)
            if ledge:       # 幅に合わせて作ってある、足場の絵（草の上の面に、足が少し沈む）
                screen.blit(ledge, (x0 - C.STONE_PAD - cam, top_y - C.LEDGE_SINK))
                return
            if self.a.stones:
                img = self._stone(n, x1 - x0 + C.STONE_PAD * 2)
                screen.blit(img, (x0 - C.STONE_PAD - cam, top_y - 3))
                return
            screen.set_clip(pygame.Rect(x0 - cam, view.y, x1 - x0, view.h))
            for tx in range(x0, x1, 32):
                screen.blit(top, (tx - cam, top_y - (C.FLOOR_Y - C.GROUND_Y)))
            screen.set_clip(view)
        for n, (x0, x1, top_y) in enumerate(self.terrain.platforms):
            platform(n, x0, x1, top_y)
        screen.set_clip(view)
        # 動く足場: 動く道すじに、細い点線を引いて（どこを動くかが、分かるように）、いまの位置に、ふつうの足場の絵を出す
        for n, (m, (x0, x1, top_y)) in enumerate(zip(self.terrain.movers, self.terrain.mover_now)):
            ax, ay, bx, by, w = m[:5]
            if max(ax, bx) + w - cam < 0 or min(ax, bx) - cam > C.BASE_W:
                continue
            for i in range(0, 21):
                px_, py_ = ax + w // 2 + (bx - ax) * i // 20 - cam, ay + (by - ay) * i // 20 + 5
                if i % 2 == 0:
                    screen.fill((236, 226, 196), (px_, py_, 2, 1))
            platform(100 + n, x0, x1, top_y)        # ふつうの足場と、同じ絵
        # 消える光の足場: 乗れる間は、明るい金の板。消える前は、点滅。消えている間も、うすい枠を出す（どこに出るかが、分かるように）
        for n, b in enumerate(self.terrain.blinks):
            x0, x1, top_y = b[:3]
            r = pygame.Rect(x0 - C.STONE_PAD - cam, top_y - 3, x1 - x0 + C.STONE_PAD * 2, 11)
            if r.right < 0 or r.left > C.BASE_W:
                continue
            state = self.terrain.blink_state(b, self.intro_t)
            if state == "off" or (state == "warn" and (self.intro_t // 4) % 2):
                pygame.draw.rect(screen, (120, 86, 24), r, 1)
                continue
            pygame.draw.rect(screen, (96, 60, 8), r.inflate(2, 2))
            pygame.draw.rect(screen, (255, 214, 96), r)
            pygame.draw.rect(screen, (255, 250, 214), (r.x + 1, r.y + 1, r.w - 2, 3))
            pygame.draw.rect(screen, (214, 150, 40), (r.x + 1, r.bottom - 3, r.w - 2, 2))

    def _stone(self, n, width):
        """n 番目の足場の、礎石の絵（足場の幅に合わせて、横に伸ばす。一度作ったら、使い回す）"""
        key = (self.stage_i, n)
        img = self._stone_cache.get(key)
        if img is None:
            src = self.a.stones[n % len(self.a.stones)]
            img = pygame.transform.scale(src, (width, round(src.get_height() * width / src.get_width())))
            self._stone_cache[key] = img
        return img

    def _draw_stele(self, screen, cam):
        """面の入口の石碑（地名が彫ってある）"""
        img = self.a.stele
        if not img:
            return
        x = self.stage.stele_x
        h = self.terrain.height_at(x)
        if h is None:
            return
        screen.blit(img, (x - img.get_width() // 2 - cam, h - img.get_height() + C.STELE_Y))

    def _draw_stage_title(self, screen):
        """面の始まりに、縦書きの名前を、現れて消える"""
        img = self.a.stage_title
        T = C.STAGE_TITLE
        t = self.intro_t - T["wait"]
        if not img or t < 0 or t >= T["fade_in"] + T["hold"] + T["fade_out"]:
            return
        if t < T["fade_in"]:
            alpha = 255 * t // T["fade_in"]
        elif t < T["fade_in"] + T["hold"]:
            alpha = 255
        else:
            alpha = 255 * (T["fade_in"] + T["hold"] + T["fade_out"] - t) // T["fade_out"]
        img.set_alpha(alpha)
        screen.blit(img, (C.BASE_W // 2 - img.get_width() // 2, C.BASE_H // 2 - img.get_height() // 2 - 8))

    def _blit_mid(self, world, x0, x1, mid_x, off, cy, ramp, band):
        """中景を、x0〜x1 の範囲だけ描く（崖登りの面: 崖の下と上で、動きが違う中景を、縁で入れ替える）。
        ramp が "out" なら、右の端の band ドットが、だんだん薄くなる。"in" なら、左の端の band ドットが、だんだん濃くなる"""
        w = x1 - x0
        if w <= 0 or abs(off) >= C.BASE_H:
            return
        part = pygame.Surface((w, C.BASE_H), pygame.SRCALPHA)
        part.blit(self.a.mid, (-mid_x - x0, off))
        if ramp and band > 0:
            key = (w, ramp, band)
            grad = self._fade_cache.get(key)
            if grad is None:
                line = pygame.Surface((w, 1), pygame.SRCALPHA)
                for x in range(w):
                    t = 1.0 if ramp == "out" and x < w - band or ramp == "in" and x >= band else (
                        (w - 1 - x) / band if ramp == "out" else x / band) if band else 1.0
                    line.set_at((x, 0), (255, 255, 255, round(255 * max(0.0, min(1.0, t)))))
                grad = pygame.transform.scale(line, (w, C.BASE_H))
                self._fade_cache[key] = grad
            part.blit(grad, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        world.blit(part, (x0, cy))

    def _draw_pit_haze(self, screen, cam):
        """穴の上に、底の色の「もや」を、下ほど濃く重ねる。奥の絵（松・灯籠・柵）の足元を沈めて、そこに地面があるように見せない。
        2ドットごとの段にして、ドット絵の粗さに合わせる"""
        H = dict(C.PIT_HAZE, h=self.stage.haze or C.PIT_HAZE["h"])
        key = (self.stage.pit, H["h"])
        haze = self._stone_cache.get(key)
        if haze is None:
            haze = pygame.Surface((C.BASE_W, H["h"]), pygame.SRCALPHA)
            for y in range(0, H["h"], H["step"]):
                k = (y + H["step"]) / H["h"]
                haze.fill(self.stage.pit + (min(255, round(255 * k ** H["curve"])),), (0, y, C.BASE_W, H["step"]))
            self._stone_cache[key] = haze
        g = self.terrain.ground
        for (_, a, _), (b, _, _) in zip(g, g[1:]):
            if b <= a or b - cam <= 0 or a - cam >= C.BASE_W:
                continue
            y, e = C.GROUND_Y + self.terrain.depth_at(a) - H["h"], H["edge"]
            # 穴の両端は、外へ向かって、2段で薄くする（となりの地面が低いと、もやの切れ目が、縦の線に見えるため）
            for x0, x1, alpha in ((a - 2 * e, a - e, 70), (a - e, a, 150), (a, b, 255), (b, b + e, 150), (b + e, b + 2 * e, 70)):
                sx0, sx1 = max(x0 - cam, 0), min(x1 - cam, C.BASE_W)
                if sx1 > sx0:
                    haze.set_alpha(alpha)
                    screen.blit(haze, (sx0, y), (0, 0, sx1 - sx0, H["h"]))
            haze.set_alpha(255)

    def _draw_water(self, screen, cam):
        top0, top1, fill = self.a.water
        top = top0 if (self.frames // C.WATER_TICKS) % 2 == 0 else top1
        y0 = C.GROUND_Y + C.WATER_DEPTH            # 水面の高さ（穴の上端より、少し下）
        x0 = -(cam % 32)
        for x in range(x0, C.BASE_W, 32):
            screen.blit(top, (x, y0))
            y = y0 + top.get_height()
            while y < C.BASE_H:
                screen.blit(fill, (x, y))
                y += fill.get_height()

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
        # 腹ペコゲージ（手裏剣を投げられる数）。左端は、団子。体力の赤い四角とは、形と色を変える（串に刺さった、丸い団子）
        icon = self.a.dango_straight
        w, h = icon.get_size()
        k = min(14 / w, 14 / h)
        icon = pygame.transform.scale(icon, (max(1, round(w * k)), max(1, round(h * k))))
        screen.blit(icon, (9 - icon.get_width() // 2 + 2, 29 - icon.get_height() // 2))
        p = self.player
        warn = p.empty_t and (p.empty_t // 4) % 2      # 無いのに投げようとした: 赤く点滅
        pygame.draw.rect(screen, C.BLACK, (17, 28, C.AMMO["max"] * 7 + 3, 3))             # 串
        pygame.draw.rect(screen, (200, 60, 60) if warn else (200, 170, 110), (18, 29, C.AMMO["max"] * 7 + 1, 1))
        for i in range(C.AMMO["max"]):
            cx = 22 + i * 7
            have = i < p.ammo
            pygame.draw.circle(screen, (200, 40, 40) if warn else C.BLACK, (cx, 29), 4)
            color = ((248, 150, 180), (252, 244, 232), (150, 200, 110))[i % 3] if have else (56, 50, 64)   # 桃・白・緑の三色団子
            pygame.draw.circle(screen, color, (cx, 29), 3 if have else 2)
        screen.blit(font.render("LIFE x%d" % max(self.lives, 0), False, C.TEXT), (C.BASE_W - 64, 24))
        if self.boss and self.boss.active and self.boss.intro_done:
            self._draw_boss_hp(screen, font)
        if self.boss and self.boss.state == "pose" and not self.boss.midway:   # ボスの二つ名と名前（ゆっくり出て、ゆっくり消える）
            t, total, fade = self.boss.st, self.boss.intro["pose"], C.BOSS_INTRO["name_fade"]
            delay = C.BOSS_NAME_DELAY if total > C.BOSS_NAME_DELAY * 3 else 0   # 短いときは、一度に出す
            for img, y, start in ((self.a.boss_title, C.BOSS_TITLE_Y, 0), (self.a.boss_name, C.BOSS_NAME_Y, delay)):
                img.set_alpha(max(0, min(255, (t - start) * 255 // fade, (total - t) * 255 // fade)))
                screen.blit(img, (C.BASE_W // 2 - img.get_width() // 2, y))
        if self.msg_t:   # 団子を全部取った
            screen.blit(self.a.oneup, (self.player.rect.centerx - self.cam_x - self.a.oneup.get_width() // 2,
                                       self.player.rect.top - (round(self.cam_y) if self._world else 0) - 28 - (90 - self.msg_t) // 4))

    def _draw_story(self, screen):
        """始まりの語り: 暗い画面の上を、文章が下から上へ流れ（1回だけ）、下にタヌキ侍がいる"""
        T = C.STORY_TANUKI
        screen.fill(C.BLACK)
        if self.a.story_bg:
            screen.blit(self.a.story_bg, (0, 0))
        # 文章: 決まった範囲の中だけを流す。上下の端では、暗がりに消える
        img = self.a.story
        y = C.STORY_WINDOW - self.story_t * C.STORY_SPEED
        if y > -img.get_height():
            if self.story_fade is None:     # 文字だけを、上下の端で透けさせる（背景は、そのまま見える）
                m = pygame.Surface((C.BASE_W, C.STORY_WINDOW), pygame.SRCALPHA)
                for i in range(C.STORY_WINDOW):
                    a = 255 * min(1.0, i / C.STORY_FADE, (C.STORY_WINDOW - 1 - i) / C.STORY_FADE)
                    pygame.draw.line(m, (255, 255, 255, int(a)), (0, i), (C.BASE_W, i))
                self.story_fade = m
            win = pygame.Surface((C.BASE_W, C.STORY_WINDOW), pygame.SRCALPHA)
            img.set_alpha(max(0, 255 - self.story_run * 16))    # 決定したら、文章は、すっと消える
            win.blit(img, (C.BASE_W // 2 - img.get_width() // 2, round(y)))
            win.blit(self.story_fade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(win, (0, 0))
        # 地面の線
        if not self.a.story_bg:
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
            o = self.a.item[self.a.foods[((t - T["dream_at"]) // C.FOOD_SWAP) % len(self.a.foods)]]       # 食べ物が、次々に浮かぶ（いつも腹ペコ）
            screen.blit(o, (bx - o.get_width() // 2, by - o.get_height() // 2 + round(math.sin(t / 22) * 1.5)))
            if (t // 24) % 3 == 0:      # きらり
                sx, sy = bx + 10, by - 8
                pygame.draw.rect(screen, (252, 208, 40), (sx - 2, sy, 5, 1))
                pygame.draw.rect(screen, (252, 208, 40), (sx, sy - 2, 1, 5))

    def _map_dots(self, pts):
        """道（点の並び）の上に、点線の点を、一定の間隔で並べる。各点の（位置, 道のはじめからの距離）"""
        out, carry, k = [], 0.0, 0
        for a, b in zip(pts, pts[1:]):
            seg = math.dist(a, b)
            d = carry
            while d < seg:
                u = d / seg
                out.append(((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), k * C.MAP_DOT_GAP))
                d += C.MAP_DOT_GAP
                k += 1
            carry = d - seg
        return out

    def _map_dot_kinds(self):
        """地図の道の、点線の点（位置, 種類）。種類は gold（通った道）・white（これからの道）・dim（まだ無い面への道）。
        分かれ道と高館の間は、行きと帰りで、同じ道を通る。通った道の上には、これからの道の点を、打たない（金の上に、白が重ならないように）"""
        playable = {st.number for st in STAGES}
        arrived = self._map_pos()[2]
        base = self.map_from or self.map_to
        walk_d = max(0.0, (self.map_t - C.MAP_WAIT) * C.MAP_WALK_SPEED)   # 駒が歩いた距離
        chain = self._map_chain()
        dots = []
        for na, nb in zip(chain, chain[1:]):
            for pos, dist in self._map_dots(self._map_route(na, nb)):
                if nb <= base or (arrived and nb <= self.map_to):
                    kind = "gold"
                elif na == base and nb == self.map_to and dist <= walk_d:
                    kind = "gold"        # 駒が通った所から、金に変わる
                elif nb in playable:
                    kind = "white"
                else:
                    kind = "dim"
                dots.append((pos, kind))
        walked = [pos for pos, kind in dots if kind == "gold"]
        near = C.MAP_DOT_GAP * 0.6      # 同じ道の上なら、いちばん近い金の点は、間隔の半分より近い
        rest = [(pos, kind) for pos, kind in dots if kind != "gold" and not any(math.dist(pos, w) < near for w in walked)]
        return rest + [(pos, "gold") for pos in walked]

    def _thanks_at(self, what):
        """姫を助ける場面の、区切りのフレーム: arrive（着く）・hop（姫が跳ねる）・type（文が出始める）・done（文が出きる）"""
        K = C.THANKS
        arrive = round((K["stop_x"] + 24) / K["walk"])
        hop = arrive + 16
        start = hop + K["hop"] * 2 + 10
        if what == "arrive":
            return arrive
        if what == "hop":
            return hop
        if what == "type":
            return start
        return start + sum(len(s) for s in K["lines"]) * K["type"] + K["gap"] * (len(K["lines"]) - 1)

    def _thanks_shown(self):
        """いままでに出した字の数（行の変わり目では、少し止まる）"""
        K = C.THANKS
        t, n = self.thanks_t - self._thanks_at("type"), 0
        for s in K["lines"]:
            if t <= 0:
                break
            n += min(len(s), t // K["type"])
            t -= len(s) * K["type"] + K["gap"]
        return n

    def _draw_thanks(self, screen, font):
        """姫を助ける場面。暗い堂の中に、金の床。左から、タヌキ侍が歩いてくる。右に、姫。礼の文が、上に出る"""
        K, t = C.THANKS, self.thanks_t
        screen.fill((6, 4, 10))
        if self.a.thanks_bg:        # 夜明けの参道（真っ黒だと、怖いので）。地面ごと描いた絵なので、床のタイルは敷かない
            screen.blit(self.a.thanks_bg, (0, 0))
        tile = self.a.tiles[1]
        for x in range(0, C.BASE_W if not self.a.thanks_bg else 0, tile.get_width()):
            screen.blit(tile, (x, K["floor"]))
        # タヌキ侍: 歩いてきて、止まる
        x = min(K["stop_x"], -24 + t * K["walk"])
        walking = x < K["stop_x"]
        img = self.a.player[True][C.WALK[(t // C.WALK_TICKS) % len(C.WALK)] if walking else C.IDLE[0]]
        screen.blit(img, (round(x) - img.get_width() // 2, K["floor"] - img.get_height()))
        # 姫: 待っている。タヌキ侍が着くと、2回跳ねて喜ぶ
        u = t - self._thanks_at("hop")
        dy = round(14 * abs(math.sin(u / K["hop"] * math.pi))) if 0 <= u < K["hop"] * 2 else 0
        hime = self.a.hime[1 if dy else 0]
        screen.blit(hime, (K["hime_x"] - hime.get_width() // 2, K["floor"] - hime.get_height() - dy))
        # 礼の文（大きい字。1文字ずつ）
        left = self._thanks_shown()
        for s, y in zip(K["lines"], K["text_y"]):
            part, left = s[:left], max(0, left - len(s))
            if not part:
                continue
            full = font.render(s, False, C.WHITE)
            for color, off in ((C.BLACK, 2), ((255, 236, 150), 0)):
                img = font.render(part, False, color)
                img = pygame.transform.scale(img, (img.get_width() * 2, img.get_height() * 2))
                screen.blit(img, (C.BASE_W // 2 - full.get_width() + off, y + off))
        done = self._thanks_at("done")
        if t >= done + K["dream"]:      # 礼を言われている間も、タヌキ侍は、食べ物のことを考えている（おにぎりと団子が、かわるがわる浮かぶ）
            # 頭のてっぺんの高さから、上へ置く（前は、ここで、礼の文の絵の高さを使っていて、雲が、頭に重なっていた）
            u = t - done - K["dream"]
            grow = min(1.0, u / 12)
            bx, by = self._cloud(screen, round(x), K["floor"] - C.THOUGHT["head"], K["cloud"][0] * grow, K["cloud"][1] * grow)
            rows = [self.a.foods[i:i + K["cols"]] for i in range(0, len(self.a.foods), K["cols"])]
            shown = max(0, (u - 12) // K["food_every"] + 1)     # 食べ物が、1つずつ浮かぶ
            n = 0
            for r, row in enumerate(rows):
                for c, kind in enumerate(row):
                    n += 1
                    if n > shown:
                        break
                    img = self.a.item[kind]
                    fx = bx + round((c - (len(row) - 1) / 2) * K["food_dx"])
                    fy = by + round((r - (len(rows) - 1) / 2) * K["food_dy"]) + round(math.sin((t + n * 20) / 14) * 1.5)
                    screen.blit(img, (fx - img.get_width() // 2, fy - img.get_height() // 2))
            h = u - K["heart_after"]
            if h > 0:       # 姫は、ハートを浮かべる（ドキドキと、ふくらむ）
                hw, hh = K["heart_cloud"]
                g = min(1.0, h / 12)
                hx, hy = self._cloud(screen, K["hime_x"] - 6, K["floor"] - hime.get_height(), hw * g, hh * g)
                if g >= 1.0:
                    self._heart(screen, hx, hy, 1 + (h // 10) % 2)
        if t >= done + 10 and self.a.thanks_sub:
            sub = self.a.thanks_sub
            screen.blit(sub, (C.BASE_W // 2 - sub.get_width() // 2, K["sub_y"]))
        if t >= done + K["wait"] and ((t - done) // 30) % 2 == 0:
            hint = self.a.title_prompt
            screen.blit(hint, (C.BASE_W // 2 - hint.get_width() // 2, C.BASE_H - 22))

    # ---------------------------------------------------------------- エンドロール
    def _start_roll(self):
        self.roll, self.roll_t = True, 0
        self.roll_x = 0.0           # 景色が流れた距離
        self.roll_state = "walk"    # walk（歩く）/ stop（止まって、車を待つ）/ look（右・左を見る）/ cross（渡る）
        self.roll_st = 0            # いまの動きに入ってからのフレーム数
        self.roll_side = 0          # いま、どちらの歩道にいるか（0 = 奥 / 1 = 手前）
        self.roll_n = 0             # 渡った回数
        self.roll_car = None        # 走っている車: [x, 向き, 絵の番号]

    def _roll_done(self):
        """文字が、流れきったか"""
        R = C.ROLL
        h = self.a.credits.get_height() if self.a.credits else 0
        return self.roll_t * R["scroll"] >= h + R["window"][1] - R["window"][0]

    def _end_roll(self):
        self.roll = False
        if self.a.ending_image:
            self.ending_screen, self.ending_t = True, 0
        else:
            self.reset()
            self._enter_title(self.use_title)

    def _step_roll(self, pressed):
        R = C.ROLL
        self.roll_t += 1
        self.roll_st += 1
        if {"restart", "attack", "jump"} & pressed and self.roll_t >= R["skip"]:    # 決定のキーで、飛ばせる
            self._end_roll()
            return
        car = self.roll_car
        if car:
            car[0] += car[1] * R["car_speed"]
            if not -60 < car[0] < R["view_w"] + 60:
                self.roll_car = None
        st = self.roll_state
        if st == "walk":
            self.roll_x += R["speed"]
            if self._roll_done() and self.roll_st >= R["tail"]:     # 文字が流れきったら、歩いている所で、絵に替わる
                self._end_roll()
            elif self.roll_x + R["x"] >= (self.roll_n + 1) * R["every"] and not self._roll_done():
                self.roll_state, self.roll_st = "stop", 0           # 横断歩道に着いた: 止まる
        elif st == "stop":
            if self.roll_st == R["car_wait"]:                       # 車が来る（1回ごとに、右から・左から）
                d = -1 if self.roll_n % 2 == 0 else 1
                self.roll_car = [float(R["view_w"] + 50 if d < 0 else -50), d, self.roll_n]
            elif self.roll_st > R["car_wait"] and self.roll_car is None:
                self.roll_state, self.roll_st = "look", 0           # 車が通りすぎた: 右・左を見る
        elif st == "look":
            if self.roll_st >= R["look"] * 3:
                self.roll_state, self.roll_st = "cross", 0
                self.sfx.append(C.SFX["decide"])
        elif st == "cross":
            if self.roll_st >= R["cross"]:
                self.roll_side ^= 1
                self.roll_n += 1
                self.roll_state, self.roll_st = "walk", 0

    def _draw_roll(self, full):
        """左半分の枠に、二人が歩く場面。右半分の暗い地に、エンドロールの文字"""
        R, t = C.ROLL, self.roll_t
        VW = R["view_w"]
        screen = full.subsurface((0, 0, VW, C.BASE_H))      # 左の枠（この中だけに描かれる）
        top, bottom = R["road"]
        scroll = round(self.roll_x)
        # 景色（絵があれば、横にくり返して流す。無ければ、空と山と、金色堂の影を、図形で描く）
        bg = self.a.roll_bg
        if bg:
            x = -(scroll // 2) % bg.get_width() - bg.get_width()
            while x < VW:
                screen.blit(bg, (x, top - 22 - bg.get_height()))
                x += bg.get_width()
            screen.fill((120, 190, 240), (0, 0, VW, max(0, top - 22 - bg.get_height())))
        else:
            screen.fill((120, 190, 240))
            for k in range(-1, 4):      # 遠くの山
                hx = k * 220 - (scroll // 4) % 220
                pygame.draw.polygon(screen, (92, 150, 110), [(hx, top - 22), (hx + 110, top - 92), (hx + 220, top - 22)])
            for k in range(-1, 3):      # 堂の影（ゆっくり流れる）
                hx = k * 300 - (scroll // 2) % 300 + 60
                pygame.draw.rect(screen, (150, 120, 60), (hx, top - 62, 70, 40))
                pygame.draw.polygon(screen, (110, 84, 40), [(hx - 12, top - 62), (hx + 35, top - 86), (hx + 82, top - 62)])
        # 奥の歩道・車道・手前の歩道
        road = self.a.roll_road
        if road:        # 絵（歩道・縁石・車道・中央線）を、横にくり返して流す
            x = -(scroll % road.get_width())
            while x < VW:
                screen.blit(road, (x, top - 22))
                x += road.get_width()
        else:
            screen.fill((196, 196, 188), (0, top - 22, VW, 22))
            screen.fill((150, 150, 144), (0, top - 3, VW, 3))
            screen.fill((74, 76, 86), (0, top, VW, bottom - top))
            screen.fill((196, 196, 188), (0, bottom, VW, C.BASE_H - bottom))
            screen.fill((228, 228, 220), (0, bottom, VW, 3))
        mid = (top + bottom) // 2
        if not road:        # 車道の真ん中の線（絵が無いときだけ。絵の帯には、線が入っている）
            for x in range(-(scroll % 48), VW, 48):
                screen.fill((226, 226, 200), (x, mid - 1, 24, 2))
        for n in range(self.roll_n - 1, self.roll_n + 3):   # 横断歩道（白い帯を、車道の幅いっぱいに並べる）
            zx = (n + 1) * R["every"] - scroll - R["zebra"] // 2 + (R["hime_dx"] // 2)
            if -R["zebra"] < zx < VW:
                if self.a.roll_zebra:
                    screen.blit(self.a.roll_zebra, (zx, top - 22))      # 帯と同じ高さの絵（白線だけ）
                    continue
                screen.fill((74, 76, 86), (zx, mid - 2, R["zebra"], 4))
                for y in range(top + 3, bottom - 4, 9):
                    screen.fill((238, 238, 232), (zx, y, R["zebra"], 5))
        # 二人の位置と向き
        st, k = self.roll_state, self.roll_st
        ya, yb = (R["far"], R["near"]) if self.roll_side == 0 else (R["near"], R["far"])
        feet = ya + (yb - ya) * min(1.0, k / R["cross"]) if st == "cross" else ya
        walking = st in ("walk", "cross")
        right = True
        if st == "look":        # 右 → 左 → 右、と見る
            right = (k // R["look"]) % 2 == 0
        frame = C.WALK[(t // C.WALK_TICKS) % len(C.WALK)] if walking else C.IDLE[0]
        tanuki = self.a.player[right][frame]
        if self.a.hime_walk and walking:        # 歩く絵（タヌキ侍と、同じ速さ）。立っている間は、立ち絵
            hime = self.a.hime_walk[(t // C.WALK_TICKS) % len(self.a.hime_walk)]
        else:
            hime = self.a.hime[0]
        if st == "cross":       # 道を渡る間は、手を挙げて歩く（車に、渡ることを知らせる）
            if self.a.tanuki_raise:
                tanuki = self.a.tanuki_raise[(t // C.WALK_TICKS) % len(self.a.tanuki_raise)]
            if self.a.hime_raise:
                hime = self.a.hime_raise[(t // (C.WALK_TICKS * 6 // len(self.a.hime_raise))) % len(self.a.hime_raise)]    # コマ数が違っても、一巡りの長さは、タヌキ侍と同じ
        hime = pygame.transform.flip(hime, True, False) if right else hime       # 姫の絵は、左向き
        bob = 1 if walking and not self.a.hime_walk and (t // 8) % 2 else 0     # 歩く絵が無い間は、小さく上下させる
        things = [(feet, tanuki, R["x"] - tanuki.get_width() // 2, 0), (feet, hime, R["x"] + R["hime_dx"] - hime.get_width() // 2, bob)]
        car = self.roll_car
        if car:
            cy = mid + 12 if car[1] < 0 else mid + 22        # 車の足元（左へ走る車は、奥の車線）
            img = self.a.roll_cars[car[2] % len(self.a.roll_cars)] if self.a.roll_cars else None
            if img:
                img = img if car[1] < 0 else pygame.transform.flip(img, True, False)    # 車の絵は、左向き
            else:           # 絵が無い間の、仮の車
                img = pygame.Surface((64, 30), pygame.SRCALPHA)
                body = ((214, 70, 60), (70, 130, 214), (240, 240, 240))[car[2] % 3]
                pygame.draw.rect(img, (20, 20, 28), (0, 8, 64, 18))
                pygame.draw.rect(img, body, (1, 9, 62, 16))
                pygame.draw.rect(img, (20, 20, 28), (12, 0, 38, 12))
                pygame.draw.rect(img, (170, 214, 240), (14, 2, 34, 9))
                for wx in (14, 50):
                    pygame.draw.circle(img, (20, 20, 28), (wx, 25), 5)
                    pygame.draw.circle(img, (150, 150, 150), (wx, 25), 2)
            things.append((cy, img, round(car[0]) - img.get_width() // 2, 0))
        for fy, img, x, up in sorted(things, key=lambda th: th[0]):     # 奥の物から描く
            screen.blit(img, (x, round(fy) - img.get_height() - up))
        fade = self._roll_fade                      # 右の端（文字の暗い地との境）を、暗くぼかす（横断歩道・車が、端からいきなり出てこないように）
        if fade is None:
            fade = self._roll_fade = pygame.Surface((R["edge"], C.BASE_H), pygame.SRCALPHA)
            for x in range(R["edge"]):
                fade.fill((10, 8, 22, round(255 * (x / (R["edge"] - 1)) ** 1.6)), (x, 0, 1, C.BASE_H))
        screen.blit(fade, (VW - R["edge"], 0))
        # 右半分: 暗い地に、エンドロールの文字（下から上へ）
        full.fill((10, 8, 22), (VW, 0, C.BASE_W - VW, C.BASE_H))
        full.fill((214, 168, 72), (VW, 0, 1, C.BASE_H))
        full.fill((60, 44, 20), (VW + 1, 0, 1, C.BASE_H))
        if self.a.credits:
            w0, w1 = R["window"]
            full.set_clip(pygame.Rect(VW + 2, w0, C.BASE_W - VW - 2, w1 - w0))
            cx, cy = VW + (C.BASE_W - VW - self.a.credits.get_width()) // 2 + 1, w1 - round(t * R["scroll"])
            full.blit(self.a.credits, (cx, cy))
            if self.a.roll_bosses:      # 「しゅつえん」: ボスの絵（待機の動き）を、空き場所に重ねる（足元をそろえ、中央に）
                for sy, frames in zip(self.a.credits_slots, self.a.roll_bosses):
                    if cy + sy < w1 and cy + sy + R["slot_h"] > w0:
                        img = frames[(t // R["boss_tick"]) % len(frames)]
                        bob = round(math.sin(t / 22)) if len(frames) == 1 else 0       # 1コマだけの像は、ゆっくり浮き沈みする
                        full.blit(img, (cx + (self.a.credits.get_width() - img.get_width()) // 2, cy + sy + R["slot_h"] - 3 - img.get_height() + bob))
            full.set_clip(None)
        if t < 40:      # 暗い所から、明るくなる
            fade = pygame.Surface((C.BASE_W, C.BASE_H))
            fade.set_alpha(255 - 255 * t // 40)
            full.blit(fade, (0, 0))

    def _draw_ending_screen(self, screen):
        """エンディング: 暗い所から、ゆっくり明るくなる。しばらくして、「PUSH ENTER KEY」が点滅する"""
        E = C.ENDING_SCREEN
        screen.blit(self.a.ending_image, (0, 0))
        if self.ending_t < E["fade"]:
            fade = pygame.Surface((C.BASE_W, C.BASE_H))
            fade.set_alpha(255 - 255 * self.ending_t // E["fade"])
            screen.blit(fade, (0, 0))
        elif self.ending_t >= E["wait"] and ((self.ending_t - E["wait"]) // 30) % 2 == 0:
            hint = self.a.title_prompt
            screen.blit(hint, (C.BASE_W - hint.get_width() - 8, 6))

    def _draw_map(self, screen):
        """ステージ選択の地図。道の上に、マリオワールドのような点線を引く（通った所は金、これからは白、まだ無い面は暗い）。
        通った場所は金の丸、いまいる場所は金の輪（脈打つ）、行き先は白い輪（点滅）。駒が歩いて、着いたら「第N面 地名」"""
        a = self.a
        screen.blit(a.map_image, (0, 0))
        screen.blit(a.map_vignette, (0, 0))      # 周りを暗くして、道と場所を浮かび上がらせる
        playable = {st.number for st in STAGES}
        (x, y), right, arrived = self._map_pos()
        gold, white, dim, dark = (252, 208, 40), (240, 240, 250), (84, 88, 120), (10, 8, 16)
        colors = dict(gold=gold, white=white, dim=dim)
        for (dx, dy), kind in self._map_dot_kinds():
            pygame.draw.rect(screen, dark, (round(dx) - 1, round(dy) - 1, 4, 4))
            pygame.draw.rect(screen, colors[kind], (round(dx), round(dy), 2, 2))
        for n, (px, py) in C.MAP_PADS.items():
            if n == self.map_to:
                continue
            if n not in playable:
                pygame.draw.circle(screen, dark, (px, py - 2), 5)
                pygame.draw.circle(screen, dim, (px, py - 2), 4, 2)
            elif n < self.map_to or n == self.map_from:    # 通った場所: 金の丸
                pygame.draw.circle(screen, dark, (px, py - 2), 6)
                pygame.draw.circle(screen, gold, (px, py - 2), 5)
            else:                                           # これから行く場所: 白い輪
                pygame.draw.circle(screen, dark, (px, py - 2), 5)
                pygame.draw.circle(screen, white, (px, py - 2), 4, 2)
        tx, ty = C.MAP_PADS[self.map_to]
        if arrived:     # いまいる場所: 金の輪が、ゆっくり脈打つ
            r = 9 + round(2 * math.sin(self.map_t * 0.12))
            pygame.draw.ellipse(screen, dark, (tx - r - 1, ty - r // 2 - 3, r * 2 + 2, r + 2), 3)
            pygame.draw.ellipse(screen, gold, (tx - r, ty - r // 2 - 2, r * 2, r), 2)
        elif (self.map_t // 8) % 2 == 0:    # 行き先: 白い輪が、点滅する
            pygame.draw.ellipse(screen, dark, (tx - 8, ty - 7, 16, 8), 3)
            pygame.draw.ellipse(screen, white, (tx - 7, ty - 6, 14, 6), 2)
        walking = self.map_t > C.MAP_WAIT and not arrived
        frame = C.WALK[(self.map_t // C.WALK_TICKS) % len(C.WALK)] if walking else C.IDLE[0]
        piece = a.map_piece(right, frame)
        screen.blit(piece, (round(x) - piece.get_width() // 2, round(y) - piece.get_height()))
        if arrived:
            label = a.map_label[self.map_to]
            u = min(1.0, max(0.0, (self.map_t - C.MAP_WAIT - self.map_len / C.MAP_WALK_SPEED) / 12))
            strip = pygame.Surface((C.BASE_W, label.get_height() + 10), pygame.SRCALPHA)
            strip.fill((8, 6, 16, int(150 * u)))
            by = C.BASE_H - strip.get_height() - 6
            screen.blit(strip, (0, by))
            label.set_alpha(int(255 * u))
            screen.blit(label, ((C.BASE_W - label.get_width()) // 2, by + 5))
        if self.map_t < 16:      # 出だしは、暗い画面から、すっと明るくなる
            fade = pygame.Surface((C.BASE_W, C.BASE_H))
            fade.set_alpha(255 - self.map_t * 16)
            screen.blit(fade, (0, 0))

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
        landed = self.title_t - C.TITLE_DROP_WAIT - C.TITLE_DROP    # 着いてからのフレーム数（負なら、まだ下りている）
        if self.start_t:        # 決定したら、その場で定位置に着く
            landed = max(landed, 0)
        k = min(1.0, max(0.0, (self.title_t - C.TITLE_DROP_WAIT) / C.TITLE_DROP)) if landed < 0 else 1.0
        y = -logo.get_height() + (C.TITLE_LOGO[1] + logo.get_height()) * (1 - (1 - k) ** 3)   # 最後に減速
        screen.blit(logo, (C.TITLE_LOGO[0] - logo.get_width() // 2, round(C.TITLE_LOGO[1] if landed >= 0 else y)))
        font = getattr(self, "_font", None)
        if self.howto and self.a.howto:
            img = self.a.howto
            screen.blit(img, ((C.BASE_W - img.get_width()) // 2, (C.BASE_H - img.get_height()) // 2))
        elif self.menu_on and font:
            self._draw_menu(screen, font)
        elif landed >= 0 and (landed // 30) % 2 == 0:   # 着いてから点滅
            img = self.a.title_prompt
            screen.blit(img, (C.TITLE_PROMPT[0] - img.get_width() // 2, C.TITLE_PROMPT[1]))

    def _draw_menu(self, screen, font):
        """スタート画面のメニュー。main = STORY / OPTION / HOW TO PLAY。option = LEVEL（難しさ）/ MUSIC・SOUND（音量）/ BACK。
        どの行も、題名と同じ中心（cx）に、中央ぞろえで出す（右の大きなタヌキ侍に、掛からない幅）。選んでいる行は、金色で、左右に印"""
        M = C.MENU
        gold, grey = (255, 236, 150), (176, 176, 190)
        option = self.menu_page == "option"

        def text(s, x, y, color):
            edge = font.render(s, False, C.BLACK)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                screen.blit(edge, (x + dx, y + dy))
            screen.blit(font.render(s, False, color), (x, y))

        if option:      # 画面の見出し
            head = "- OPTION -"
            text(head, M["cx"] - font.size(head)[0] // 2, M["y"] - M["head"], (214, 168, 72))
        rows = M["pages"][self.menu_page]
        gap = M["row"] if self.menu_page == "main" else M["row_option"]
        top = M["y"] - max(0, len(rows) - 4) * gap       # 行が多いページは、上へ伸ばす（画面の下に出ないように）
        if self.menu_page == "disco":
            head = "- DISCOGRAPHY -"
            text(head, M["cx"] - font.size(head)[0] // 2, top - M["head"], (214, 168, 72))
        for n, row in enumerate(rows):
            y = top + n * gap
            on = n == self.menu_i
            color = gold if on else grey
            if on and row == "story" and self.start_t and (self.start_t // 4) % 2:      # 決定したあとは、STORY が速く点滅する
                continue
            label, value, boxes = M["label"][row], "", None
            if self.menu_page == "disco" and row != "back" and C.DISCO[int(row[1:])][0] == self.disco_song:
                label += " *"        # いま鳴っている曲
            if row == "level":
                i = C.LEVEL_ORDER.index(self.level)
                value = ("< " if i > 0 else "  ") + self.L["label"] + (" >" if i < len(C.LEVEL_ORDER) - 1 else "  ")
            elif row in ("music", "sound"):
                boxes = self.vol_bgm if row == "music" else self.vol_sfx
            lw = font.size(label)[0]
            vw = font.size(value)[0] if value else (M["steps"] * 10 - 2 if boxes is not None else 0)
            w = lw + (M["gap"] + vw if vw else 0)
            x = M["cx"] - w // 2
            text(label, x, y, color)
            if value:
                text(value, x + lw + M["gap"], y, color)
            elif boxes is not None:     # 音量は、四角の数で出す
                for k in range(M["steps"]):
                    r = pygame.Rect(x + lw + M["gap"] + k * 10, y + 2, 8, 9)
                    pygame.draw.rect(screen, C.BLACK, r.inflate(2, 2))
                    pygame.draw.rect(screen, color if k < boxes else (56, 56, 64), r)
            if on:      # 選んでいる印（行の左右に、三角。少し、揺れる）
                d = (self.title_t // 12) % 2
                for px, sgn in ((x - 8 - d, 1), (x + w + 7 + d, -1)):
                    pts = [(px - 3 * sgn, y + 2), (px - 3 * sgn, y + 10), (px + 2 * sgn, y + 6)]
                    pygame.draw.polygon(screen, C.BLACK, [(a + dx, b2 + dy) for (a, b2), (dx, dy) in zip(pts, ((-sgn, -1), (-sgn, 1), (sgn, 0)))])
                    pygame.draw.polygon(screen, gold, pts)

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

    def _boss_tail_y(self, r):
        """ボスの吹き出しの、しっぽの先の高さ（世界の座標）。倒れたボスの絵の、いちばん上より、少し上にする（絵が背の高いボスや、台座に座るボスに、かぶらないように）。
        どのボスも、足元から TALK_BOSS_Y より低くはしない"""
        tip = r.bottom - C.TALK_BOSS_Y
        img = self.boss.image() if self.a else None
        if img is not None:
            art = C.ENEMY_ART[self.boss.KIND]
            top = r.bottom - art["h"] if art["mode"] == "bottom" else r.centery - art["ay"]
            tip = min(tip, top + img.get_bounding_rect().top - 6)
        return tip

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

    def _draw_thought(self, screen, x, y, shown):
        """考えごとの吹き出し（返事の代わり）。頭の上に、小さな丸が2つ出て、その先に雲がふくらみ、中に、食べ物が1つずつ浮かぶ。
        ボスが何を言っても、タヌキ侍は、おにぎりや団子のことを考えている"""
        H, foods = C.THOUGHT, self.stage.thought
        g = min(1.0, max(0.0, (shown - 4) / max(1, H["grow"] - 4)))
        bx, by = self._cloud(screen, x, y - 6, (22 + 22 * len(foods)) * g, 30 * g, dots=min(2, (shown + 1) // 2))
        if g <= 0:
            return
        for i, kind in enumerate(foods):
            if shown >= H["grow"] + i * H["per"] + 1:
                img = self.a.item[kind]
                fx = bx + round((i - (len(foods) - 1) / 2) * 22)
                screen.blit(img, (fx - img.get_width() // 2, by - img.get_height() // 2 + round(math.sin((self.ending + i * 20) / 14) * 1.5)))

    def _heart(self, screen, cx, cy, size=1):
        """ハートを、ドットで描く（赤。縁は暗く）。size=2 で、少し大きい（鼓動）"""
        rows = ("0110110", "1111111", "1111111", "0111110", "0011100", "0001000")
        d = 2
        w, h = len(rows[0]) * d, len(rows) * d
        for color, pad in ((C.BLACK, 1), ((236, 64, 96), 0)):
            for j, row in enumerate(rows):
                for i, ch in enumerate(row):
                    if ch == "1":
                        pygame.draw.rect(screen, color, (cx - w // 2 + i * d - pad, cy - h // 2 + j * d - pad - (size - 1), d + 2 * pad, d + 2 * pad))

    def _cloud(self, screen, x, top, w, h, dots=2):
        """雲形の吹き出し（考えごと）。(x, top) は、頭のてっぺん。そこから上へ、小さな丸が2つ、その先に、もこもこした雲（幅 w・高さ h）。
        雲は、頭に重ならない高さに置く。雲の中心 (bx, by) を返す（中に、物を描くため）"""
        white, edge = (244, 244, 252), (16, 10, 24)
        w, h = round(w), round(h)
        bx = max(w // 2 + 8, min(x + 12, C.BASE_W - w // 2 - 8))
        by = top - C.THOUGHT["lift"] - h // 2
        circles = [(x + 5, top - 2, 1), (x + 8, top - 7, 2)][:dots]
        if w >= 8 and h >= 8:
            r = h * 0.34                                # こぶの半径
            n = max(2, round((w - 2 * r) / (r * 1.5)) + 1)
            for k in range(n):                          # 上と下に、こぶを並べる（上と下で、半分ずらす）
                u = k / (n - 1)
                circles.append((bx - w / 2 + r + (w - 2 * r) * u, by - h * 0.18, r))
                if k < n - 1:
                    circles.append((bx - w / 2 + r + (w - 2 * r) * (u + 0.5 / (n - 1)), by + h * 0.2, r * 0.92))
            circles += [(bx - w / 2 + r * 0.8, by + h * 0.04, r * 0.9), (bx + w / 2 - r * 0.8, by + h * 0.04, r * 0.9)]
        for color, pad in ((edge, 2), (white, 0)):
            for cx, cy, r in circles:
                pygame.draw.circle(screen, color, (round(cx), round(cy)), max(1, round(r)) + pad)
            if pad == 0 and w >= 8 and h >= 8:           # こぶの間の、すき間を埋める
                pygame.draw.ellipse(screen, white, (bx - w // 2 + 3, by - h // 3, w - 6, h * 2 // 3))
        return bx, by

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
        t, cx = self.clear_t, C.BASE_W // 2
        shown = int(self.score * min(1, max(0, t - C.CLEAR_SCORE_AT) / C.CLEAR_COUNT))   # 0 から最終値まで増える
        rows = [("SCORE", "%06d" % shown, C.CLEAR_SCORE_AT),
                ("FOOD", "%d/%d" % (self.dango, self.stage.dango_total), C.CLEAR_SCORE_AT + C.CLEAR_COUNT + 20),
                ("TIME", "%d:%02d" % (sec // 60, sec % 60), C.CLEAR_SCORE_AT + C.CLEAR_COUNT + 40)]
        def draw(text, x, y, right=False):
            img = font.render(text, False, C.TEXT)
            screen.blit(img, (x - img.get_width() if right else x, y))
        img = font.render("STAGE CLEAR", False, C.TEXT)
        screen.blit(img, (cx - img.get_width() // 2, 70))
        width = font.size("SCORE  000000")[0]     # 表の幅（ラベルは左揃え、数字は右揃え）
        for i, (label, value, at) in enumerate(rows):
            if t >= at:
                draw(label, cx - width // 2, 106 + i * 18)
                draw(value, cx + width // 2, 106 + i * 18, right=True)
        if t >= C.CLEAR_WAIT and (t // 30) % 2 == 0:
            img = font.render("PRESS ENTER", False, C.TEXT)
            screen.blit(img, (cx - img.get_width() // 2, 106 + 4 * 18))

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
    if keys[pygame.K_UP]:
        held.add("up")      # メニューの項目選びに使う（遊んでいる間は、ジャンプ）
    return held


KEYDOWN_MAP = {
    pygame.K_SPACE: "jump", pygame.K_UP: "jump", pygame.K_z: "attack",
    pygame.K_x: "throw", pygame.K_RETURN: "restart", pygame.K_p: "pause",
}


async def main():
    pygame.init()
    # パソコン版は、窓の端をつかんで大きさを変えられる（ブラウザ版は、ページの側で広げる）
    flags = 0 if sys.platform == "emscripten" else pygame.RESIZABLE
    window = pygame.display.set_mode((C.BASE_W * C.SCALE, C.BASE_H * C.SCALE), flags)
    pygame.display.set_caption(C.TITLE)
    if sys.platform == "emscripten":
        # 画面の大きさを決めたあとに、ページの側の大きさ合わせを呼ぶ（呼ばないと、決める前の正方形の縦横比のままで、画面が小さくなる）
        import platform
        platform.window.window_resize()
    screen = pygame.Surface((C.BASE_W, C.BASE_H))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 20)
    start = [int(a[1:]) for a in sys.argv[1:] if a in ("s2", "s3", "s4")]
    for a in sys.argv[1:]:       # 確認用: python main.py easy（hard）で、その難しさで始める
        if a in C.LEVELS:
            C.LEVEL = a
    game = Game(title=not (start or {"boss", "cp"} & set(sys.argv[1:])))
    if "roll" in sys.argv[1:]:   # 確認用: python main.py roll で、エンドロールから始める
        game.title = False
        game._start_roll()
    if "thanks" in sys.argv[1:]:  # 確認用: python main.py thanks で、姫を助ける場面から始める
        game.title = False
        game.thanks, game.thanks_t, game._thanks_typed = True, 0, 0
    if start:     # 確認用: python main.py s2（s3・s4）で、その面から始める（スタート画面は出さない）
        game.reset(start[0] - 1)
    if "cp" in sys.argv[1:]:     # 確認用: python main.py cp で、中間地点の手前から始める（スタート画面は出さない）
        game.player.px, game.player.py = float(game.stage.checkpoint[0] - 70), float(game.stage.checkpoint[1])
        game.enemies = [e for e in game.enemies if abs(e.cx - game.stage.checkpoint[0]) > 200]
    if "boss" in sys.argv[1:]:   # 確認用: python main.py boss で、ボスの場所の手前から始める（スタート画面は出さない）
        game.player.px = float(game.stage.arena_x0 + 100)
        game.enemies = []
    audio = Audio()
    audio.preload(sorted(f for f in os.listdir(AUDIO_DIR) if f.startswith("sfx_")))    # 効果音は先に読んでおく
    pad = Pad()   # コントローラ（挿すと、すぐ使える）
    touch = Touch()   # スマホのタッチ（一度触ると、左右の帯にボタンが出る）
    # 起動したときの会社のロゴ（確認用の起動 s2・boss・cp などでは出さない）
    splash = None if (start or {"boss", "cp", "roll", "thanks"} & set(sys.argv[1:])) else Splash()
    # 重さの計測（ブラウザ版: アドレスの末尾に ?perf=1 を付けると、1秒ごとに、フレームの時間を window.perflog に溜める。ふだんは何もしない）
    perf = False
    if sys.platform == "emscripten":
        import platform
        perf = "perf=1" in str(platform.window.location.search)
    perf_ms, perf_t, perf_parts, perf_step, perf_blit = [], 0, {}, 0, 0
    if perf:        # 描く処理を、部品ごとに測る（_draw・_blit で始まるもの）
        def _timed(f, name):
            def wrapper(*a, **k):
                t0 = pygame.time.get_ticks()
                r = f(*a, **k)
                perf_parts[name] = perf_parts.get(name, 0) + pygame.time.get_ticks() - t0
                return r
            return wrapper
        for name in dir(Game):
            if name.startswith(("_draw", "_blit")):
                setattr(game, name, _timed(getattr(game, name), name))

    def fit_to_page():
        """ブラウザ版: 窓の縦横比を、ページ（スマホの画面）に合わせる。ずれていたら、作り直す（向きを持ち替えたときも）。
        縦向き（縦のほうが長い）のときは、何もしない（ページの側で「横向きに」と出す）"""
        import platform
        pw, ph = float(platform.window.innerWidth), float(platform.window.innerHeight)
        ww, wh = pygame.display.get_surface().get_size()
        if ph <= 0 or pw <= ph or abs(pw / ph - ww / wh) < 0.02:
            return
        pygame.display.set_mode((round(C.BASE_H * C.SCALE * pw / ph), C.BASE_H * C.SCALE))
        platform.window.window_resize()

    while True:
        pressed = set()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                return
            if splash and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN, getattr(pygame, "CONTROLLERBUTTONDOWN", -1), pygame.JOYBUTTONDOWN):
                splash.skip()       # 何かを押すと、ロゴを飛ばす（そのキーは、ゲームには渡さない）
                continue
            if event.type == pygame.KEYDOWN and event.key in KEYDOWN_MAP:
                pressed.add(KEYDOWN_MAP[event.key])
            if event.type == pygame.KEYUP and event.key in (pygame.K_SPACE, pygame.K_UP):
                pressed.add("jump_release")
            if event.type == getattr(pygame, "WINDOWFOCUSLOST", -1):     # 窓が後ろに回ったら、止める
                pressed.add("pause_on")
            pressed |= pad.handle(event)
            got = touch.handle(event, pygame.display.get_surface().get_size())
            if got & {"jump", "attack", "throw", "pause"} and sys.platform == "emscripten":
                try:        # 押した手応え: 短く振動させる（Android。iPhone のブラウザは、振動できないので、何もしない）
                    import platform
                    platform.window.navigator.vibrate(C.TOUCH["vibrate"])
                except Exception:
                    pass
            pressed |= got
        if touch.active and C.COYOTE != C.TOUCH["coyote"]:     # タッチで遊ぶ人は、ジャンプを受け付ける時間を、少し長く
            C.COYOTE, C.JUMP_BUFFER = C.TOUCH["coyote"], C.TOUCH["jump_buffer"]
        if touch.active and sys.platform == "emscripten":
            fit_to_page()       # タッチ: 窓の横幅を、スマホの画面の縦横比に合わせる（左右の帯にボタンを置くため）
        if splash:      # ロゴ画面の間は、ゲームを動かさない
            if splash.done:
                splash = None
            else:
                splash.step()
                splash.draw(pygame.display.get_surface())
                pygame.display.flip()
                clock.tick(C.FPS)
                await asyncio.sleep(0)
                continue
        t_step = pygame.time.get_ticks()
        game.step(keys_to_input(pygame.key.get_pressed()) | pad.held() | touch.held(), pressed)
        perf_step += pygame.time.get_ticks() - t_step
        audio.set_gain(game.vol_bgm / C.MENU["steps"], game.vol_sfx / C.MENU["steps"])    # 音を鳴らす前に（変えた音量で、鳴るように）
        for name in dict.fromkeys(game.sfx + sprites.SOUNDS):     # 同じ音は、1フレームに1回だけ
            audio.play_sfx(name)
        game.sfx.clear()
        sprites.SOUNDS.clear()
        audio.set_paused(game.paused)
        if game.bgm:
            audio.play_bgm(game.bgm)        # ボスの場所に入ると、曲が変わる
            audio.keep_playing()            # 曲が終わっていたら、かけ直す（ブラウザ版）
        else:
            audio.fade_out(C.BGM_FADE_MS)   # やられたら（クリアしたら）、曲を消していく。再開すると、また始まる
        t_draw = pygame.time.get_ticks()
        game.draw(screen, font)
        draw_ms = pygame.time.get_ticks() - t_draw
        t_blit = pygame.time.get_ticks()
        window = pygame.display.get_surface()
        ww, wh = window.get_size()
        k = min(ww / C.BASE_W, wh / C.BASE_H)   # 16:9 を保って、余白は黒
        w, h = round(C.BASE_W * k), round(C.BASE_H * k)
        if touch.active:            # タッチ: ゲームの絵は、左右の帯を除いた所に。帯には、ボタン
            r = Touch.game_rect(ww, wh)
            window.fill((0, 0, 0))
            pygame.transform.scale(screen, r.size, window.subsurface(r))
            touch.draw(window)
        elif (w, h) == (ww, wh):      # 窓の大きさぴったり（ブラウザ版は、いつもこう）: 作り直さずに、窓へ直接引き伸ばす（毎フレームの、大きな絵の作成を省く）
            pygame.transform.scale(screen, (w, h), window)
        else:
            window.fill((0, 0, 0))
            window.blit(pygame.transform.scale(screen, (w, h)), ((ww - w) // 2, (wh - h) // 2))
        pygame.display.flip()
        perf_blit += pygame.time.get_ticks() - t_blit
        clock.tick(C.FPS)
        if perf:
            perf_ms.append((clock.get_rawtime(), draw_ms))
            perf_t += 1
            if perf_t >= 60:
                raw = sorted(r for r, _ in perf_ms)
                draws = sorted(d for _, d in perf_ms)
                top = sorted(perf_parts.items(), key=lambda kv: -kv[1])[:5]
                line = "stage=%d boss=%s | per1s: step=%d draw=%d scale+flip=%d | draw median=%d max=%d | over16=%d | %s" % (
                    game.stage_i, bool(game.boss), perf_step, sum(draws), perf_blit, draws[len(draws) // 2], draws[-1],
                    sum(r > 16 for r in raw), " ".join("%s=%d" % kv for kv in top))
                perf_parts, perf_step, perf_blit = {}, 0, 0
                platform.window.perflog = str(platform.window.perflog or "") + line + "\n"      # ページの変数に溜める（console.log へは出ないため）
                perf_ms, perf_t = [], 0
        await asyncio.sleep(0)   # ブラウザ版では、毎フレームここで制御をブラウザに返す


if __name__ == "__main__":
    asyncio.run(main())
