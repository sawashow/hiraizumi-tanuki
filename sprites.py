"""絵の読み込みと、主人公・敵・手裏剣・命中エフェクトのクラス"""
import math
import os

import pygame

import config as C
from stage import STAGE1

IMG = os.path.join(os.path.dirname(__file__), "assets", "images")


def _load(name):
    return pygame.image.load(os.path.join(IMG, name)).convert_alpha()


def _rimmed(img, color=(252, 252, 252)):
    """絵のまわりに、明るい縁取りを1ドット付ける（小さくて暗い飛び道具を、どの背景でも見えるようにする）"""
    w, h = img.get_size()
    out = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
    edge = pygame.mask.from_surface(img).to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))
    for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
        out.blit(edge, (dx, dy))
    out.blit(img, (1, 1))
    return out


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


def _gilt(img):
    """石の小物を、金に塗り替えた絵を返す。明るさをそのまま、暗い金 → 金 → 明るい金に置き換える。火（明るい橙・黄）は、変えない"""
    ramp = ((0, (40, 24, 8)), (90, (130, 88, 24)), (160, (212, 164, 56)), (255, (255, 232, 140)))
    out = img.copy()
    for y in range(out.get_height()):
        for x in range(out.get_width()):
            r, g, b, a = out.get_at((x, y))
            if not a or (r >= 200 and r - b >= 70):
                continue
            lum = (r + g + b) / 3
            for (l0, c0), (l1, c1) in zip(ramp, ramp[1:]):
                if lum <= l1:
                    k = (lum - l0) / (l1 - l0)
                    out.set_at((x, y), tuple(round(c0[i] + (c1[i] - c0[i]) * k) for i in range(3)) + (a,))
                    break
    return out


WORLD_H = C.BASE_H   # いまの面の絵の高さ（崖登りのある面は、画面より高い。Game が、面を替えるたびに入れる）
SOUNDS = []     # このフレームに鳴らす効果音（キャラクターの側から足す。メインループが鳴らして、空にする）


def _tinted(img, color):
    """絵を、灰色にしてから、1色に塗り替える（絵がまだ無い敵の、代わりの絵）"""
    out = pygame.transform.grayscale(img)
    out.fill((60, 60, 60, 0), special_flags=pygame.BLEND_RGB_ADD)
    out.fill(tuple(color) + (255,), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def snd(key):
    """効果音を鳴らす（名前は config.SFX_GAME の鍵）"""
    if len(SOUNDS) < 32:
        SOUNDS.append(C.SFX[key])


class Assets:
    """絵をまとめて読み込む。左向き用は反転して持つ"""

    def __init__(self, stage=None):
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
            src, tint = kind, None
            if kind in C.ENEMY_STANDIN and not os.path.exists(os.path.join(IMG, "enemies", "%s_%s_0.png" % (kind, next(iter(anims))))):
                src, tint = C.ENEMY_STANDIN[kind]      # 絵がまだ無い: ほかの敵の絵を、塗り替えて借りる
            for anim, n in anims.items():
                right = [_load(f"enemies/{src}_{anim}_{i}.png") for i in range(n)]
                if tint:
                    right = [_tinted(f, tint) for f in right]
                self.enemy[kind][anim] = {True: right,
                                          False: [pygame.transform.flip(f, True, False) for f in right]}
        # 基衡の絵（右向きで描いてある。左向きは、反転して持つ）。絵が無ければ、持たない
        self.boss2 = {}
        try:
            for name in C.BOSS2_FRAMES:
                left = _load(f"enemies/boss2_{name}.png")
                # 絵は、右を向いて描いてある（霧が、うしろの左へ流れる）。左向きは、反転して持つ
                self.boss2[name] = {True: left, False: pygame.transform.flip(left, True, False)}
        except (FileNotFoundError, pygame.error):
            self.boss2 = {}
        wave = [_load(f"enemies/wave_{i}.png") for i in range(C.WAVE_FRAMES)]
        self.wave = {True: wave, False: [pygame.transform.flip(f, True, False) for f in wave]}   # True=右向き
        gust = [_load(f"gust_{i}.png") for i in range(4)] if os.path.exists(os.path.join(IMG, "gust_0.png")) else []
        self.gust = {True: gust, False: [pygame.transform.flip(f, True, False) for f in gust]}   # 風（基衡の扇・山おろし）。絵が無ければ、線で描く
        for frames in self.gust.values():
            for f in frames:
                f.set_alpha(C.GUST["alpha"])    # 薄くして、風のうしろの敵や地形が見えるように
        slash = [_load(f"slash_{i}.png") for i in range(C.SLASH_FRAMES)]
        self.slash = {True: slash, False: [pygame.transform.flip(f, True, False) for f in slash]}
        self.item = {k: _load(f"items/{k}.png") for k in ("dango", "onigiri", "leaf")}
        for k in C.FOODS[2:]:       # 頭の中の食べ物（あれば）
            if os.path.exists(os.path.join(IMG, "items", f"food_{k}.png")):
                self.item[k] = _load(f"items/food_{k}.png")
        self.foods = [k for k in C.FOODS if k in self.item]      # 夢の吹き出しに、順に浮かべる食べ物
        self.snacks = [k for k in self.foods if k != "onigiri"]      # 拾うと、手裏剣が増える食べ物（おにぎりは、回復なので入れない）
        self.dango_straight = self.item["dango"]      # 団子のゲージ（左上）は、縦の絵のまま
        if os.path.exists(os.path.join(IMG, "items", "dango_tilt.png")):       # 拾える団子・吹き出しの団子は、斜めの絵（tools/make_dango_tilt.py）
            self.item["dango"] = _load("items/dango_tilt.png")
        # 三方手裏剣・スーパータヌキの絵（仮）: 手裏剣の絵を縮めたものと、図形で描いた星。絵ができたら、差し替える
        self.item["triple"] = _triple_icon(self.shuriken[0])
        self.item["super"] = _star_icon()
        # 弓兵の矢（右向き）と、折れた矢。細くて暗いので、白い縁取りを付ける
        arrow, broken = _rimmed(_load("enemies/yumihei_arrow.png")), _rimmed(_load("enemies/yumihei_arrow_broken.png"))
        self.arrow = {True: arrow, False: pygame.transform.flip(arrow, True, False)}
        self.arrow_broken = {True: broken, False: pygame.transform.flip(broken, True, False)}
        self.toro = {"lit": [_load(f"items/toro_lit_{i}.png") for i in range(3)],        # 石灯籠（火がゆらぐ）
                     "break": [_load(f"items/toro_break_{i}.png") for i in range(3)],    # 壊れる
                     "broken": _load("items/toro_broken.png"),                           # 壊れたあと
                     "shard": [_load(f"items/toro_shard_{i}.png") for i in range(3)]}    # 飛び散るかけら
        self.toro_stone, self.toro_gilt = self.toro, None      # 石の灯籠と、金に塗り替えた灯籠（堂の中の面で、初めて作る）
        self.cp_text = _load("checkpoint_text.png")   # 「中間地点」
        self.life_text = {n: _load(f"life_{n}.png") for n in (1, 2, 3, 4)}   # 「のこり 2」など
        self.oneup = _load("oneup.png")
        self.torii = {False: _load("items/torii_off.png"), True: _load("items/torii_on.png")}   # 中間地点（通る前・通った後）
        self.howto = _load("howto.png") if os.path.exists(os.path.join(IMG, "howto.png")) else None     # 操作説明（メニューから開く）
        self.title_logo = _load("title_logo.png")       # 題名「平泉 タヌキ侍」（昔のゲームのロゴ風）
        self.title_prompt = _load("title_prompt.png")   # 「PUSH ENTER KEY」
        # スタート画面の絵（無ければ、1面の景色で代わりにする）
        self.title_bg = _load(C.TITLE_BG) if os.path.exists(os.path.join(IMG, C.TITLE_BG)) else None
        # ステージ選択の地図、駒、「第N面 地名」
        self.map_image = _load(C.MAP_IMAGE).convert()
        self.map_label = {n: _load(f"map_label_{n}.png") for n in C.MAP_PADS}
        self._map_pieces = {}
        # 周りを暗くする膜（周辺減光）。小さく作って、引き伸ばす
        vw, vh = 60, 34
        vig = pygame.Surface((vw, vh), pygame.SRCALPHA)
        for yy in range(vh):
            for xx in range(vw):
                d = math.hypot((xx + 0.5) / vw - 0.5, (yy + 0.5) / vh - 0.5) / 0.7071   # 中心 0 → 角 1
                vig.set_at((xx, yy), (6, 4, 14, round(C.MAP_VIGNETTE * max(0.0, d - 0.45) / 0.55)))
        self.map_vignette = pygame.transform.smoothscale(vig, (C.BASE_W, C.BASE_H))
        self.ending_image = _load(C.ENDING_IMAGE).convert() if os.path.exists(os.path.join(IMG, C.ENDING_IMAGE)) else None
        self.story = _load("story_intro.png")           # 始まりの語り（縦に長い1枚）
        trail = _sword_trail()
        self.sword_trail = {True: trail, False: pygame.transform.flip(trail, True, False)}   # True=右向き
        self.story_tanuki = [_load(f"story/tanuki_{i:02d}.png") for i in range(11)]   # 語りの画面のタヌキ侍（居眠りは、ゲーム中にも使う）
        self.story_tanuki_left = [pygame.transform.flip(f, True, False) for f in self.story_tanuki]
        self.gameover = _load("gameover.png")             # 「無念…」（ドット風フォントで書き出した絵）
        self.gameover_prompt = _load("gameover_prompt.png")  # 「Enterキーで再開」
        self.thanks_sub = _load(C.THANKS_SUB) if os.path.exists(os.path.join(IMG, C.THANKS_SUB)) else None

        def opt(name):      # あれば読む（エンドロールの絵は、無くても、図形で代わりにする）
            return _load(name) if os.path.exists(os.path.join(IMG, name)) else None
        R = C.ROLL_IMAGES
        self.roll_bg, self.credits = opt(R["bg"]), opt(R["credits"])
        self.roll_cars = [c for c in (opt(n) for n in R["cars"]) if c]
        self.roll_road, self.roll_zebra = opt(R["road"]), opt(R["zebra"])
        self.thanks_bg = opt(C.THANKS_BG)
        self.story_bg = opt(C.STORY_BG)
        self.roll_bosses = [[opt(n) for n in names] for names in C.ROLL_BOSSES]       # 「しゅつえん」のボス（動く）。1つでも絵が無ければ、出さない
        if not all(all(f) for f in self.roll_bosses):
            self.roll_bosses = []
        # 文字の絵の、ボスの空き場所（左端の画素に打った、見えない目印。tools/make_credits.py）
        self.credits_slots = [y for y in range(self.credits.get_height()) if tuple(self.credits.get_at((0, y))) == (255, 0, 255, 3)] if self.credits else []
        self.hime_walk = [opt(n) for n in R["hime_walk"]] if all(opt(n) for n in R["hime_walk"]) else []
        self.tanuki_raise = [opt(n) for n in R["tanuki_raise"]] if all(opt(n) for n in R["tanuki_raise"]) else []    # 道を渡る間の、手を挙げて歩く絵
        self.hime_raise = [opt(n) for n in R["hime_raise"]] if all(opt(n) for n in R["hime_raise"]) else []
        if all(os.path.exists(os.path.join(IMG, n)) for n in C.HIME_IMAGES):
            self.hime = [_load(n) for n in C.HIME_IMAGES]
        else:       # 姫の絵が、まだ無い: タヌキ侍（左向き）を、桃色に染めて、代わりにする
            self.hime = []
            for f in (0, 8):
                img = self.player[False][min(f, len(self.player[False]) - 1)].copy()
                img.fill((255, 170, 205, 255), special_flags=pygame.BLEND_RGBA_MULT)
                img.fill((40, 0, 24, 0), special_flags=pygame.BLEND_RGB_ADD)
                self.hime.append(img)
        self.stage = None
        self.load_stage(stage or STAGE1)

    def map_piece(self, right, frame):
        """地図の上の駒（タヌキ侍の絵を、小さくしたもの）"""
        key = (right, frame)
        if key not in self._map_pieces:
            img = self.player[right][frame]
            self._map_pieces[key] = pygame.transform.scale(
                img, (round(img.get_width() * C.MAP_PIECE_SCALE), round(img.get_height() * C.MAP_PIECE_SCALE)))
        return self._map_pieces[key]

    def load_stage(self, stage):
        """面ごとの絵（背景・タイル・ボスの名前・寸劇のせりふ）を読み込む。無ければ、1面の絵で代わりにする"""
        if self.stage is stage:
            return
        self.stage = stage
        if getattr(stage, "gilt", False):       # 堂の中の面: 苔むした石の灯籠を、金の灯籠に塗り替える（火の色は、そのまま）
            if self.toro_gilt is None:
                self.toro_gilt = {k: [_gilt(i) for i in v] if isinstance(v, list) else _gilt(v) for k, v in self.toro_stone.items()}
            self.toro = self.toro_gilt
        else:
            self.toro = self.toro_stone
        def pick(name, fallback):
            return _load(name) if os.path.exists(os.path.join(IMG, name)) else _load(fallback)
        self.sky = pick(stage.sky, STAGE1.sky)
        self.mid = pick(stage.mid, STAGE1.mid)
        d = stage.tiles
        # 崖登りのある面: 縦に長い空と、崖の岩肌のタイル（あれば、使う）
        tall = stage.sky.replace(".png", "_tall.png")
        if getattr(stage, "climb", None) and os.path.exists(os.path.join(IMG, tall)):
            self.sky = _load(tall)
        self.cliff = []
        while getattr(stage, "climb", None) and os.path.exists(os.path.join(IMG, f"{d}cliff_{len(self.cliff)}.png")):
            self.cliff.append(_load(f"{d}cliff_{len(self.cliff)}.png"))
        self.tiles = [pick(f"{d}tile_{i:02d}.png", f"tile_{i:02d}.png") for i in range(6)]
        self.stage_title = _load(f"stage_title_{stage.number}.png") if os.path.exists(os.path.join(IMG, f"stage_title_{stage.number}.png")) else None
        self.stele = _load(f"stele_{stage.number}.png") if os.path.exists(os.path.join(IMG, f"stele_{stage.number}.png")) else None
        stones = [f"{d}stone_{i}.png" for i in range(3)]   # 足場の絵（礎石など）。無ければ、タイルの上端で代わりにする
        self.stones = [_load(n) for n in stones] if all(os.path.exists(os.path.join(IMG, n)) for n in stones) else None
        # 足場の絵（幅ごとに作ってある。ledge_050.png = 幅50）。あれば、これを使う（引き伸ばさない）
        self.ledges = {}
        folder = os.path.join(IMG, d) if d else IMG
        for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else ():
            if name.startswith("ledge_") and name.endswith(".png"):
                self.ledges[int(name[6:-4])] = _load(f"{d}{name}")
        names = [f"{d}water_top_0.png", f"{d}water_top_1.png", f"{d}water_fill.png"]   # 池の水面（2コマ）と、水の中
        have = all(os.path.exists(os.path.join(IMG, n)) for n in names)
        self.water = [_load(n) for n in names] if have else None   # 無ければ、穴は暗い四角のまま
        self.boss_title = pick(stage.boss_title, STAGE1.boss_title)
        self.boss_name = pick(stage.boss_name, STAGE1.boss_name)
        self.talk_boss = pick(stage.talk_boss, STAGE1.talk_boss)       # 寸劇のせりふ（吹き出しの中の字）
        self.talk_tanuki = pick(stage.talk_tanuki, STAGE1.talk_tanuki)


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
        self.sword_cool = 0     # 次の刀を振れるようになるまでの残りフレーム
        self.ammo = C.AMMO["start"]    # 手裏剣を投げられる数（団子）
        self.empty_t = 0        # 団子が無いのに投げようとした（ゲージを点滅させる残りフレーム）
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
            snd("jump")
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
        if self.sword_cool and not self.attack_t:   # 振り終わってすぐは、次の刀を振れない（覚えておいて、振れるようになったら出す）
            self.queued, self.queue_t = "attack", C.INPUT_BUFFER
            return
        if self.throw_t:        # 手裏剣の隙は、刀で打ち切れる（刀の隙は、刀では打ち切れない）
            self._cancel()
        if not self.busy and self.hp > 0:
            self.attack_t = 1
            snd("swing")
            self.sword_cool = sum(n for _, n in C.SWORD_SEQ) + C.SWORD_COOLDOWN
            self.swing_id += 1
            self.crouch_act = self.crouch
            self.queued = None
        elif self.attack_t or self.throw_t:    # 前の動作の途中で押した: 覚えておいて、終わったらすぐ出す
            self.queued, self.queue_t = "attack", C.INPUT_BUFFER

    def throw(self):
        if self.ammo < C.AMMO["cost"]:      # 団子が無い: 投げられない（ゲージを点滅させて、知らせる）
            if not (self.attack_t or self.throw_t or self.hurt_t) and self.hp > 0:
                if not self.empty_t:
                    snd("empty")
                self.empty_t = C.AMMO["empty"]
            return
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
        snd("dead" if self.hp <= 0 else "hurt")
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
        self.sword_cool = max(0, self.sword_cool - 1)
        self.empty_t = max(0, self.empty_t - 1)
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
        if self.py > C.FALL_Y + (terrain.depth_at(self.px) if terrain else 0) and self.hp > 0:
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
                snd("throw")
                self.release = True
                self.ammo = max(0, self.ammo - C.AMMO["cost"])     # 手を離れた瞬間に、団子を1つ使う
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
        snd("fall")
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

    # 種類によって違う性質の、既定値（持つ種類だけが、上書きする）。Game は、どの敵にも、これをそのまま読む
    spawned = None      # 出した弾（光波・矢）。出す種類は、__init__ で、リストにする（Game が受け取って動かす）
    sure_drop = None    # 倒すと、必ず落とす物（立ち往生）
    solid = False       # 通り抜けられず、敵の弾も弾く（立ち往生）
    clang = False       # このフレームに、攻撃を弾いた（立ち往生。Game が、音を鳴らす）
    dropped = False     # 倒されて、物を落とした（1回だけ）
    last_throw = None   # 最後に当たった手裏剣の、投げの番号（1投げにつき、当たるのは1つだけ）
    shadow = False      # 影のボス（暗く、青みがかった色で描く）
    chain = False       # いまの構えは、続けて撃つ2発目以降（構えが短くなる）

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
        big = isinstance(self, Boss)
        if damage:
            snd("boss_hit" if big else "hit")
        if self.hp <= 0:
            self.dying = True
            self.dead_t = 0
            snd("boss_die" if big else "die")

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
        if self.shadow:   # 影のボス: 暗く、青みがかった色にする
            img = self._shadow_image(img)
        if self.flash:   # 攻撃を受けた直後は、白いシルエットにする
            img = pygame.mask.from_surface(img).to_surface(setcolor=C.WHITE, unsetcolor=(0, 0, 0, 0))
        art = C.ENEMY_ART[self.KIND]
        y = r.bottom - art["h"] if art["mode"] == "bottom" else r.centery - art["ay"]
        surface.blit(img, (r.centerx - art["ax"], y))

    def _frames(self, anim):
        return self.a.enemy[self.KIND][anim][self.facing > 0]

    def _ready_len(self):
        """構えの長さ（続けて撃つときの2発目からは、短い）"""
        return self.P.get("combo_ready", self.P["ready_frames"]) if self.chain else self.P["ready_frames"]

    def _opt(self, anim):
        """あれば使う動きの絵（無ければ None）"""
        dirs = self.a.enemy[self.KIND].get(anim)
        return dirs[self.facing > 0] if dirs else None

    _SHADOW_CACHE = {}

    @classmethod
    def _shadow_image(cls, img):
        """影の絵（暗く、青みがかる）。一度作ったら、使い回す"""
        key = id(img)
        out = cls._SHADOW_CACHE.get(key)
        if out is None or out[0] is not img:
            dark = img.copy()
            dark.fill(C.SHADOW_MULT, special_flags=pygame.BLEND_RGB_MULT)
            dark.fill(C.SHADOW_ADD, special_flags=pygame.BLEND_RGB_ADD)
            cls._SHADOW_CACHE[key] = out = (img, dark)
        return out[1]


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
                snd("wave")
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


class Miira(Ochimusha):
    """ミイラ（亡者）: 地面を、ゆっくり歩いて近づくだけ。攻撃はしない（触れると、ダメージ）。穴や段差の手前で、折り返す。体力1"""
    P = C.MIIRA
    KIND = "miira"

    def __init__(self, x, assets=None, floor=None):
        super().__init__(x, assets, floor)
        self.cy = self.floor - self.P["h"] / 2

    def image(self):
        if self.dying:
            f = self._frames("death")
            return f[min(self.dead_t // self.DEATH_TICKS, len(f) - 1)]
        f = self._frames("walk")
        return f[(self.t // 14) % len(f)]


class Tengu(Enemy):
    """天狗: 地面を、ぴょんぴょん跳んで近づく。「待つ → かがむ（予告）→ 跳ぶ」をくり返す。体力2。
    着地する先に、同じ高さの地面が無いとき（穴・段差）は、跳ばずに、向きを変える"""
    P = C.TENGU
    KIND = "tengu"
    DEATH_TICKS = 8

    def __init__(self, x, assets=None, floor=None):
        self.floor = float(floor if floor is not None else C.FLOOR_Y)
        super().__init__(x, y=self.floor - C.TENGU["h"] / 2, assets=assets)
        self.vy = 0.0
        self.air = False
        self.crouch_t = 0
        self.rest_t = self.P["rest"]
        self.dir = -1

    def _land_ok(self, x, terrain):
        """x の地面が、いま立っている高さと同じか"""
        if not terrain:
            return True
        h = terrain.height_at(x)
        return h is not None and abs(h - self.floor) <= 1

    def think(self, pr, stage_w, terrain=None):
        P = self.P
        if self.air:
            self.vy += C.GRAVITY
            self.cx += self.dir * P["hop_vx"]
            self.cy += self.vy
            if self.vy > 0 and self.cy >= self.floor - P["h"] / 2:
                self.cy = self.floor - P["h"] / 2
                self.air = False
                self.rest_t = P["rest"]
            return
        dx = pr.centerx - self.cx
        if abs(dx) > P["active"] and not self.crouch_t:
            return
        if self.crouch_t:
            self.crouch_t -= 1
            if not self.crouch_t:       # 跳ぶ
                self.air, self.vy = True, -P["hop_vy"]
                snd("jump")
            return
        self.facing = self.dir = 1 if dx > 0 else -1
        if self.rest_t:
            self.rest_t -= 1
            return
        reach = 2 * P["hop_vx"] * P["hop_vy"] / C.GRAVITY        # 着地までに進む距離
        if self._land_ok(self.cx + self.dir * reach, terrain) and 0 < self.cx + self.dir * reach < stage_w:
            self.crouch_t = P["crouch"]
        else:
            self.rest_t = P["rest"]      # 先が穴: 跳ばずに、また待つ

    def image(self):
        if self.dying:
            f = self._frames("death")
            return f[min(self.dead_t // self.DEATH_TICKS, len(f) - 1)]
        f = self._frames("walk")
        if self.air:
            return f[1]
        return f[2] if self.crouch_t else f[0]


class Archer(Enemy):
    """弓兵: その場から動かない。主人公が近づくと、弓を引いて（予告）、主人公をねらって、矢をまっすぐ撃つ。
    矢は、刀で斬ると消せる。撃ったあとは、しばらく撃たない（近づいて斬る隙）。体力2"""
    P = C.YUMI
    KIND = "yumihei"
    DEATH_TICKS = 9

    def __init__(self, x, assets=None, floor=None):
        self.floor = float(floor if floor is not None else C.FLOOR_Y)
        super().__init__(x, y=self.floor - C.YUMI["h"] / 2, assets=assets)
        self.draw_t = 0     # 弓を引いている残りフレーム
        self.shoot_t = 0    # 放ったあとの動きの残りフレーム
        self.cool = C.YUMI["first_wait"]
        self.spawned = []   # 撃った矢（Game が受け取って動かす）

    def think(self, pr, stage_w, terrain=None):
        P = self.P
        dx = pr.centerx - self.cx
        if not self.shoot_t:
            self.facing = 1 if dx > 0 else -1
        if self.cool:
            self.cool -= 1
        if self.draw_t:
            self.draw_t -= 1
            if not self.draw_t:     # 放つ: いま主人公がいる所を、ねらう
                bow = (self.cx + self.facing * 12, self.floor - P["bow_y"])
                snd("arrow")
                self.spawned.append(Arrow(*bow, pr.centerx, pr.centery, self.facing, self.a))
                self.shoot_t = P["shoot_frames"]
            return
        if self.shoot_t:
            self.shoot_t -= 1
            return
        if abs(dx) <= P["active"] and abs(pr.centery - self.cy) <= P["reach_y"] and not self.cool:
            snd("draw")
            self.draw_t = P["draw_frames"]
            self.cool = P["cooldown"]

    def image(self):
        P = self.P
        if self.dying:
            f = self._frames("death")
            return f[min(self.dead_t // self.DEATH_TICKS, len(f) - 1)]
        if self.draw_t:
            f = self._frames("draw")
            return f[min((P["draw_frames"] - self.draw_t) * len(f) // P["draw_frames"], len(f) - 1)]
        if self.shoot_t:
            f = self._frames("shoot")
            return f[0 if self.shoot_t > P["shoot_frames"] // 2 else 1]
        f = self._frames("idle")
        return f[(self.t // 30) % len(f)]


class Tachiojo(Enemy):
    """立ち往生（弁慶の亡霊）: 動かない。向きも変えない（来る側 = 左を、にらんでいる）。ダメージは与えない。
    **正面からの攻撃は、すべて弾く。跳び越えて、うしろから斬ると、倒せる**（倒すと、おにぎりを落とす）。
    触れると、来たほうへ押し戻される。上には乗れない。敵の矢や光波も、弾く"""
    P = C.TACHIOJO
    KIND = "tachiojo"

    def __init__(self, x, assets=None, floor=None):
        self.floor = float(floor if floor is not None else C.FLOOR_Y)
        super().__init__(x, y=self.floor - C.TACHIOJO["h"] / 2, assets=assets)
        self.facing = -1        # 左（主人公が来る側）を向いたまま、動かない
        self.clang = False      # このフレームに、弾いた（Game が、音を鳴らす）
        self.behind = False     # 主人公が、うしろ側にいる（Game が、攻撃の前に書く）
        self.sure_drop = C.TACHIOJO["drop"]     # 倒すと、必ず落とす物

    def think(self, pr, stage_w, terrain=None):
        self.behind = (pr.centerx - self.cx) * self.facing < 0

    def hit(self, damage=1):
        """正面からは、白く光って、弾く。うしろからは、効く"""
        if self.dying:
            return
        if damage and self.behind:
            self.hp -= damage
            self.flash = C.HIT_FLASH
            if self.hp <= 0:
                self.dying, self.dead_t = True, 0
            return
        if not self.flash:
            self.clang = True
        self.flash = self.P["flash"]

    def update(self, player_rect, stage_w, terrain=None):
        self.t += 1
        if self.dying:          # 光になって、消える
            self.dead_t += 1
            if self.dead_t >= self.P["fade"]:
                self.alive = False
            return
        if self.flash:
            self.flash -= 1
        self.think(player_rect, stage_w, terrain)

    @property
    def solid(self):
        """倒れるまでは、通れない（Game は、これを見て、ダメージの代わりに、押し戻す）"""
        return not self.dying

    def image(self):
        f = self._frames("stand")
        return f[(self.t // self.P["breath"]) % len(f)]

    def draw(self, surface, cam_x):
        if not self.dying or not self.a:
            super().draw(surface, cam_x)
            return
        img = pygame.mask.from_surface(self.image()).to_surface(setcolor=(255, 248, 200, 255), unsetcolor=(0, 0, 0, 0))
        img.set_alpha(max(0, 255 - 255 * self.dead_t // self.P["fade"]))
        r = self.rect.move(-cam_x, 0)
        art = C.ENEMY_ART[self.KIND]
        surface.blit(img, (r.centerx - art["ax"], r.bottom - art["h"] - self.dead_t // 3))


class Shot:
    """敵の弾（光波・矢・数珠の玉・光の柱・風・扇・花びら）の、共通の性質。動きと絵は、種類ごとに作る。
    Game は、どの弾にも、これをそのまま読む（違う種類だけが、上書きする）"""
    push = 0                      # 当たると、押し戻す強さ（0 なら、押さない。押す弾は、ダメージを与えない）
    cuttable = True               # 刀で斬って、消せる
    damage = C.WAVE["damage"]     # 当たったときのダメージ
    cut_pad = (0, 0)              # 刀で斬る判定を、広げる幅（横・縦）

    def cut_effect(self):
        """斬られた・弾かれたときに、あとに残す物（無ければ None。矢は、折れて落ちる）"""
        return None


class Arrow(Shot):
    """弓兵の矢。撃った瞬間に主人公がいた所へ向けて、まっすぐ飛ぶ（角度には限りがある）。刀で斬ると、折れて消える"""
    cuttable = True
    _turned = {}    # 向きごとに回した絵（使い回す）

    def __init__(self, x, y, tx, ty, direction, assets):
        A = C.ARROW
        self.a = assets
        self.px, self.py = float(x), float(y)
        self.dir = direction
        limit = math.radians(C.YUMI["max_angle"])
        ang = math.atan2(ty - y, abs(tx - x) or 1.0)
        ang = max(-limit, min(limit, ang))
        self.vx, self.vy = direction * math.cos(ang) * A["speed"], math.sin(ang) * A["speed"]
        self.deg = round(math.degrees(ang) / 5) * 5      # 絵の向き（5度きざみ）
        self.damage = A["damage"]
        self.travel = 0.0
        self.alive = True

    @property
    def rect(self):
        A = C.ARROW
        return pygame.Rect(round(self.px - A["w"] / 2), round(self.py - A["h"] / 2), A["w"], A["h"])

    def update(self, stage_w):
        self.px += self.vx
        self.py += self.vy
        self.travel += C.ARROW["speed"]
        if self.travel > C.ARROW["range"] or not (0 <= self.px <= stage_w) or self.py > WORLD_H + 20:
            self.alive = False

    def cut_effect(self):
        snd("snap")
        return ArrowBreak(self.px, self.py, self.dir, self.a)

    def draw(self, surface, cam_x):
        base = getattr(self.a, "arrow", None) if self.a else None
        if not base:
            pygame.draw.rect(surface, C.WHITE, self.rect.move(-cam_x, 0))
            return
        x, y = round(self.px) - cam_x, round(self.py)
        for i, alpha in ((1, 150), (2, 90), (3, 40)):   # うしろに、短い光の尾（飛んでいる向きが、分かる）
            tx, ty = x - self.vx * i * 4, y - self.vy * i * 4
            dot = pygame.Surface((3, 3), pygame.SRCALPHA)
            dot.fill((252, 252, 252, alpha))
            surface.blit(dot, (round(tx) - 1, round(ty) - 1))
        key = (self.dir, self.deg)
        img = Arrow._turned.get(key)
        if img is None:
            img = pygame.transform.rotate(base[self.dir > 0], -self.deg * self.dir)
            Arrow._turned[key] = img
        surface.blit(img, (round(self.px) - img.get_width() // 2 - cam_x, round(self.py) - img.get_height() // 2))


class ArrowBreak:
    """斬られた矢: 折れて、少し落ちて消える（見た目だけ）"""

    def __init__(self, x, y, direction, assets):
        self.a = assets
        self.x, self.y, self.dir = x, y, direction
        self.t = 0
        self.alive = True

    def update(self):
        self.t += 1
        if self.t >= C.ARROW["break_frames"]:
            self.alive = False

    def draw(self, surface, cam_x):
        imgs = getattr(self.a, "arrow_broken", None) if self.a else None
        if not imgs:
            return
        img = imgs[self.dir > 0]
        if self.t > C.ARROW["break_frames"] // 2 and (self.t // 2) % 2:
            return      # 消える前は、点滅
        y = self.y + 0.12 * self.t * self.t
        surface.blit(img, (round(self.x - self.dir * self.t * 0.6) - img.get_width() // 2 - cam_x, round(y) - img.get_height() // 2))


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
                snd("caw")
                self.state = "telegraph"
                self.t = 0
        elif self.state == "telegraph":
            self.facing = 1 if dx > 0 else -1
            if self.t >= P["telegraph"]:
                # 降りる深さは、いつも同じ（主人公の高さは、見ない。足場の上や真下にいても、同じ形で飛ぶ）。
                # 横は、この瞬間の主人公の位置へ。真下に近いときも、min_dx ぶんは横へ進む（まっすぐ落ちない）
                tx = max(abs(dx), P["min_dx"]) * (1 if dx > 0 else -1)
                n = math.hypot(tx, P["drop"])
                self.vx, self.vy = tx / n * P["speed"], P["drop"] / n * P["speed"]
                snd("dive")
                self.state = "dive"
        else:
            self.cx += self.vx
            self.cy += self.vy
            self.facing = 1 if self.vx > 0 else -1     # 地面は、すり抜けて、そのまま飛び去る（地面を滑らない）
            if self.cx < -60 or self.cx > stage_w + 60 or self.cy > WORLD_H + 40:
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

    # ボスによって違う性質の、既定値（持つボスだけが、変える）
    alert = False         # このフレームに、構えに入った（Game が見て、画面を小さく揺らす）
    midway = False        # 面の途中の相手（影のボス・中ボス）。倒すと、先へ進める
    shadow_done = False   # 影を倒したあとの後始末を、済ませた
    thrust = False        # いまの構えは、突き（突きを持つボスだけが、変える）

    def __init__(self, x, assets=None, floor=None, x_min=0.0, x_max=None, quick=False, end_x=None, pattern=None):
        self.floor = float(floor if floor is not None else C.FLOOR_Y)
        super().__init__(x, y=self.floor - C.FLOOR_Y - C.BOSS["h"], assets=assets)   # 画面の上から降ってくる（床が低い所では、そのぶん低い所から）
        self.end_x = float(end_x if end_x is not None else C.END_BOSS_X)   # 倒されて、吹っ飛んで落ちる場所
        self.pattern = pattern or C.BOSS_PATTERN                            # 光波の順番（L=低い / H=高い）
        half = self.w / 2
        self.x_min = x_min + half
        self.x_max = (x_max if x_max is not None else C.STAGE_W) - half
        self.intro = dict(C.BOSS_INTRO, **(C.BOSS_INTRO_QUICK if quick else {}))
        self.state = "wait"   # wait / drop / land / pose（ここまでが、出てくる場面） / walk / ready / swing / crouch / leap / recover
        self.landed = False   # このフレームに着地した（Game が見て、画面を揺らす）
        self.down_t = 0       # 倒されて、地面に落ちてからのフレーム数
        self.combo_left = 0   # 続けて撃つ光波の、残りの数
        self.chain = False    # いまの構えは、続けて撃つ2発目以降
        self.st = 0           # いまの動きに入ってからのフレーム数
        self.vx = self.vy = 0.0
        self.count = 0        # 攻撃の回数（3回に1回、跳びかかる）
        self.shots = 0        # 出した光波の数（高い・低いの順番を決める）
        self.spawned = []     # 出した光波（Game が受け取って動かす）

    @property
    def rage(self):
        return self.hp <= self.max_hp // 2

    def make_shadow(self):
        """影にする（面の途中のボスの間）: 体力は半分、見た目は暗く。ふつうの動きは、そのまま"""
        self.shadow = True
        self.max_hp = self.hp = max(C.SHADOW_MIN_HP, self.max_hp // 2)

    def update(self, player_rect, stage_w, terrain=None):
        self.t += 1
        if self.dying:      # 決まった場所へ、弧を描いて吹っ飛ぶ。落ちたら、倒れたまま残る
            B = C.END_BLOW
            self.flash = max(0, self.flash - 1)
            if self.dead_t == 0:
                self.vx, self.vy = (self.end_x - self.cx) / B["frames"], B["vy"]
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
                self.cx = self.end_x
                self.down_t = 1
                self.facing = -1    # 倒れたら、タヌキ侍（左で話す）のほうを向く
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
        if state == "ready" and self.KIND != "boss4":     # 構えに入る: 低い音と、小さな揺れで知らせる
            snd("charge")
            self.alert = True

    @property
    def high(self):
        """次の光波が、高いか（構えの絵も、これで変える）"""
        return self.pattern[self.shots % len(self.pattern)] == "H"

    def _wave(self, direction, tall=False):
        P = self.P
        y = self.floor - P["high_bottom"] - P["high_h"] / 2 if tall else self.floor + C.WAVE["dy"]
        snd("boss_wave")
        self.spawned.append(Wave(self.cx + direction * (self.w / 2 + 8), y, direction, self.a,
                                 P["wave_speed"], P["wave_range"], tall))

    def _choose(self, dx):
        """歩き終わって、次の攻撃が決まったあとの手入れ（ボスごとに、変える所）。dx は、主人公までの横の距離"""

    def _fire(self):
        """振って、光波を出す（ボスごとに、変える所）"""
        self._wave(self.facing, self.high)
        self.shots += 1

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
                self.combo_left = P.get("rage_combo" if self.rage else "combo", 1) - 1   # このあと、続けて撃つ数
                self.chain = False
                self._choose(dx)
        elif s == "ready":         # 構える（光波の予告）。続けて撃つときの2発目からは、短い
            if self.st >= self._ready_len():
                self._set("swing")
        elif s == "swing":
            if self.st == P["wave_at"]:
                self._fire()
            if self.st >= P["swing_frames"]:
                if self.combo_left > 0:     # 続けて、もう一度構える（高い・低いは、そのつど変わる）
                    self.combo_left -= 1
                    self.chain = True
                    self.facing = 1 if dx > 0 else -1
                    self._set("ready")
                else:
                    self._set("recover")
        elif s == "crouch":        # かがむ（跳びかかりの予告）。そのときの主人公の位置へ跳ぶ
            if self.st >= P["crouch_frames"]:
                frames = P["leap_frames"]
                target = max(self.x_min, min(float(pr.centerx), self.x_max))
                self.vx = (target - self.cx) / frames
                self.vy = -P["gravity"] * frames / 2
                snd("leap")
                self._set("leap")

    def image(self):
        if self.dying:
            return self._death()[1 if self.down_t else 0]    # 飛んでいる間は、のけぞる。落ちたら、倒れる
        s = self.state
        high, crouch, leap = self._opt("high"), self._opt("crouch"), self._opt("leap")   # 専用の絵（無いボスは、ほかの絵で代わりにする）
        if s == "swing":
            return self._frames("swing")[0 if self.st < self.P["wave_at"] else 1]
        if s in ("drop", "leap"):
            if leap:
                return leap[0 if s == "leap" and self.vy < 0 else 1]   # 跳び上がる / 太刀を振り上げて、落ちてくる
            return self._frames("swing")[0]
        if s == "ready" and self.high:      # 高い光波の構え: 刀を振り上げる
            if high:
                return high[min(self.st * len(high) // self._ready_len(), len(high) - 1)]
            return self._frames("swing")[0]
        if s == "land":
            return crouch[1] if crouch else self._frames("swing")[1]   # 着地して、かがんでいる
        if s == "pose":
            f = self._frames("stance")
            return f[(self.t // 22) % len(f)] if high else f[0]     # 専用の絵があれば、肩で息をする
        low = self._opt("low")
        if s == "ready" and low:            # 低い光波の構え: 腰を落として、得物を後ろへ引く
            return low[min(self.st * len(low) // self._ready_len(), len(low) - 1)]
        if s == "crouch" and crouch:
            return crouch[min(self.st * len(crouch) // self.P["crouch_frames"], len(crouch) - 1)]
        if s in ("ready", "crouch"):
            f = self._frames("stance")
            total = self._ready_len() if s == "ready" else self.P["crouch_frames"]
            return f[min(self.st * len(f) // total, len(f) - 1)]
        if s == "recover":
            return self._frames("swing")[1]   # 振り下ろしたまま（隙）
        f = self._frames("walk")
        return f[(self.t // 12) % len(f)]

    def _telegraph(self, surface, r, img, x, y):
        """構えの間の予告（矢印は使わない）: 体が白く脈打ち、足元に土ぼこりが立ち、攻撃が来る高さに細い光の筋が伸びる"""
        if self.state != "ready" or self.dying:
            return
        P, d = self.P, self.facing
        k = min(self.st, 30) / 30
        white = pygame.mask.from_surface(img).to_surface(setcolor=C.WHITE, unsetcolor=(0, 0, 0, 0))
        white.set_alpha(int(40 + 90 * abs(math.sin(self.st / 4))) * (1 if k else 0))
        surface.blit(white, (x, y))
        for i in range(3):      # 土ぼこり（足元から、左右へ散って昇る）
            t = (self.st * 2 + i * 9) % 27
            for sgn in (-1, 1):
                pygame.draw.circle(surface, (214, 196, 160), (r.centerx + sgn * (self.w // 3 + t // 2), r.bottom - 2 - t // 3), max(1, 3 - t // 10))
        if self.thrust:
            ly = r.bottom + C.WAVE["dy"]
        elif self.high and "high_bottom" in P:
            ly = r.bottom - P["high_bottom"] - P["high_h"] // 2
        else:
            ly = r.bottom + C.WAVE["dy"]
        x0 = r.centerx + d * (self.w // 2 + 4)
        L = int(70 * k)
        col = (255, 120, 90) if self.thrust else (255, 236, 120)
        pygame.draw.line(surface, col, (x0, ly), (x0 + d * L, ly), 1)
        pygame.draw.line(surface, col, (x0, ly - 1), (x0 + d * L // 2, ly - 1), 1)

    def draw(self, surface, cam_x):
        super().draw(surface, cam_x)
        if self.state == "ready" and not self.dying and self.a and self.KIND not in ("boss4", "tachiojo"):
            img = self.image()
            if img is not None:
                r = self.rect.move(-cam_x, 0)
                art = C.ENEMY_ART[self.KIND]
                self._telegraph(surface, r, img, r.centerx - (art["ax"] if self.facing < 0 else art["w"] - art["ax"]), r.bottom - art["h"])


class Boss3(Boss):
    """2面のボス（三代・秀衡）。体が大きく、体力が多く、薙刀の光波が速くて遠くまで届く。
    泰衡（Boss）と同じ型（歩く → 光波 / 跳びかかり）に、固有の攻撃「踏み込み突き」を足した（1面と2面が、似たボスにならないように）:
    主人公が近い（thrust_near より内側）と、光波ではなく、腰を落として構え（足元に赤い矢印の予告）→ 踏み込んで、速くて短い光波で突く。
    跳ぶか、下がれば、よけられる。突いたあとは隙になる"""
    P = C.BOSS3
    KIND = "boss3"

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.thrust = False     # いまの構えは、突き

    @property
    def high(self):
        return not self.thrust and super().high      # 突きの構えは、低い構え（腰を落として、得物を後ろへ引く）

    def _ready_len(self):
        return self.P["thrust_ready"] if self.thrust else super()._ready_len()

    def _choose(self, dx):
        self.thrust = self.state == "ready" and abs(dx) < self.P["thrust_near"]
        if self.thrust:
            self.combo_left = 0     # 突きは、1回だけ

    def _fire(self):
        if not self.thrust:
            return super()._fire()
        P = self.P
        snd("thrust")
        self.spawned.append(Wave(self.cx + self.facing * (self.w / 2 + 8), self.floor + C.WAVE["dy"], self.facing,
                                 self.a, P["thrust_speed"], P["thrust_range"], False))

    def think(self, pr, stage_w, terrain=None):
        super().think(pr, stage_w, terrain)
        P = self.P
        if self.state == "swing" and self.thrust and self.st <= P["thrust_dash_frames"]:       # 突きと一緒に、踏み込む
            self.cx = max(self.x_min, min(self.cx + self.facing * P["thrust_dash"] / P["thrust_dash_frames"], self.x_max))


class Benkei(Boss):
    """高館の中ボス（弁慶の亡霊「立ち往生」）。道の真ん中に立ったまま、動かない。どこから斬っても、効く。
    「にらむ → 構える（予告）→ 薙ぐ（光波）か、突く → 隙」を繰り返す。離れていると光波、近いと突き。
    降ってこない（最初から、立っている）。倒すと、光になって消える"""
    P = C.BENKEI
    KIND = "tachiojo"

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.cy = self.floor - self.h / 2    # 最初から、地面に立っている
        self.state = "pose"
        self.facing = -1
        self.thrust = False     # いまの構えは、突き

    def update(self, player_rect, stage_w, terrain=None):
        if self.dying:          # 吹っ飛ばない。その場で、光になって消える
            self.t += 1
            self.dead_t += 1
            self.flash = max(0, self.flash - 1)
            if self.dead_t >= self.P["fade"]:
                self.alive = False
            return
        super().update(player_rect, stage_w, terrain)

    def think(self, pr, stage_w, terrain=None):
        P = self.P
        self.st += 1
        s = self.state
        dx = pr.centerx - self.cx
        if s == "pose":            # 立って、にらむ
            self.facing = 1 if dx > 0 else -1
            if self.st >= self.intro["pose"]:
                self._set("walk")
        elif s == "recover":
            if self.st >= P["rage_recover_frames" if self.rage else "recover_frames"]:
                self._set("walk")
        elif s == "walk":          # 歩かない。向きだけ変えて、にらむ
            self.facing = 1 if dx > 0 else -1
            if self.st >= P["rage_walk_frames" if self.rage else "walk_frames"]:
                self.thrust = abs(dx) < P["near"]
                self.combo_left = 0 if self.thrust else P["rage_combo" if self.rage else "combo"] - 1
                self.chain = False
                self._set("ready")
        elif s == "ready":
            if self.st >= (P["thrust_ready"] if self.thrust else self._ready_len()):
                self._set("swing")
        elif s == "swing":
            if self.st == P["wave_at"]:
                if self.thrust:     # 突き: 速くて、短い
                    snd("thrust")
                    self.spawned.append(Wave(self.cx + self.facing * (self.w / 2 + 8), self.floor + C.WAVE["dy"], self.facing,
                                             self.a, P["thrust_speed"], P["thrust_range"], False))
                else:
                    self._wave(self.facing, self.high)
                    self.shots += 1
            if self.st >= P["swing_frames"]:
                if self.combo_left > 0:
                    self.combo_left -= 1
                    self.chain = True
                    self._set("ready")
                else:
                    self._set("recover")

    def image(self):
        f = self._frames("stand")
        return f[(self.t // self.P["breath"]) % len(f)]

    def _mark(self, surface, r, img, x, y):
        self._telegraph(surface, r, img, x, y)

    def draw(self, surface, cam_x):
        r = self.rect.move(-cam_x, 0)
        img = self.image() if self.a else None
        if img is None:
            pygame.draw.rect(surface, (168, 0, 32), r)
            return
        art = C.ENEMY_ART[self.KIND]
        x = r.centerx - (art["ax"] if self.facing < 0 else art["w"] - art["ax"])   # 絵は左向き。右を向くと、体の中心が、枠の右寄りになる
        y = r.bottom - art["h"]
        if self.dying:          # 光になって、昇って消える
            img = pygame.mask.from_surface(img).to_surface(setcolor=(255, 248, 200, 255), unsetcolor=(0, 0, 0, 0))
            img.set_alpha(max(0, 255 - 255 * self.dead_t // self.P["fade"]))
            surface.blit(img, (x, y - self.dead_t // 3))
            return
        if self.flash:
            img = pygame.mask.from_surface(img).to_surface(setcolor=C.WHITE, unsetcolor=(0, 0, 0, 0))
        surface.blit(img, (x, y))
        self._mark(surface, r, img, x, y)


class Boss4(Boss):
    """4面のボス（初代・清衡「金色坐仏」）。地面から少し浮いて、座ったまま動く。背中に、回る後光。上から降りてきて、
    「近づく → 予告 → 攻撃 → 隙」を繰り返す。攻撃は4つを、決まった順（config.BOSS4_CYCLE）で出す:
      beads  数珠の玉: 手を合わせて、玉を、高さを変えて、ひとつずつ飛ばす（跳ぶ・しゃがむ・斬る）
      pillar 光の柱: 床に、光る印が出て、そこへ、上から光の柱が落ちる（印の間に立つ）
      ring   数珠の輪: まわりに玉の輪が出て、八方へ飛ぶ（離れるか、しゃがむ）
      warp   転移: 光になって消え、主人公の反対側に現れて、すぐ次の攻撃に移る（現れる場所に、先に光の印）
    玉は刀で消せる（柱は消せない）。攻撃を受けても、ひるまない。
    体力が半分になると、後光が赤く大きくなり、画面が揺れて、玉と柱が増え、間が短くなる"""
    P = C.BOSS4
    KIND = "boss4"
    DEATH_TICKS = 16

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.floor -= self.P["hover"]       # 浮いている高さ（降りてきても、地面には着かない）
        self.volley = 0                      # 飛ばした回数（玉の高さの順番を決める）
        self.turn = 0                        # 出した攻撃の数（攻撃の順番を決める）
        self.dest = None                     # 転移で、現れる場所
        self.roared = False                  # 体力が半分になったときの、怒りの演出を、もう見せた

    def _volley(self):
        seq = C.BOSS4_RAGE_VOLLEYS if self.rage else C.BOSS4_VOLLEYS
        return seq[self.volley % len(seq)]

    def _next_attack(self, no_warp=False):
        seq = C.BOSS4_RAGE_CYCLE if self.rage else C.BOSS4_CYCLE
        kind = seq[self.turn % len(seq)]
        self.turn += 1
        if no_warp and kind == "warp":       # 転移のすぐあとに、また転移はしない
            return self._next_attack(True)
        return kind

    def _ground(self):
        return self.floor + self.P["hover"]

    def _begin(self, kind, pr):
        P = self.P
        self.facing = 1 if pr.centerx > self.cx else -1
        if kind == "beads":
            self._set("ready")
        elif kind == "ring":
            snd("charge")
            self._set("ring_ready")
        elif kind == "pillar":               # 主人公の足元と、その左右に、少しずつ遅らせて落とす
            L = C.PILLAR
            n = L["rage_count" if self.rage else "count"]
            lo, hi = self.x_min - self.w / 2 + 14, self.x_max + self.w / 2 - 14
            for k in range(n):
                x = pr.centerx + (k - n // 2) * L["spread"]
                if lo <= x <= hi:
                    self.spawned.append(Pillar(x, self._ground(), self.a, delay=abs(k - n // 2) * L["stagger"],
                                               warn=L["rage_warn" if self.rage else "warn"], quiet=k != n // 2))
            self._set("pillar_ready")
        else:                                # warp: 主人公をはさんで、反対側へ
            side = -1 if self.cx < pr.centerx else 1
            dest = max(self.x_min, min(pr.centerx - side * P["warp_dist"], self.x_max))
            if abs(dest - pr.centerx) < P["warp_min"]:      # 反対側が、壁で狭い: 部屋の端のうち、いまの場所から遠いほうへ
                ends = [x for x in (self.x_min, self.x_max) if abs(x - pr.centerx) >= P["warp_min"]]
                dest = max(ends, key=lambda x: abs(x - self.cx)) if ends else dest
            self.dest = dest
            snd("warp")
            self._set("warp_out")

    @property
    def warping(self):
        return self.state in ("warp_out", "warp_in")

    def hit(self, damage=1):
        if self.warping:        # 光になっている間は、攻撃が当たらない
            return
        super().hit(damage)

    def think(self, pr, stage_w, terrain=None):
        P = self.P
        s = self.state
        if s in self.INTRO or s == "drop":     # 出てくる場面は、1面のボスと同じ（降りてきて、止まる）
            return Boss.think(self, pr, stage_w, terrain)
        self.st += 1
        if s in ("walk", "recover"):
            self.facing = 1 if pr.centerx > self.cx else -1
        if s == "walk":
            if abs(pr.centerx - self.cx) > P["near"]:
                self.cx = max(self.x_min, min(self.cx + self.facing * P["speed"], self.x_max))
            if self.st >= P["rage_walk_frames" if self.rage else "walk_frames"]:
                if self.rage and not self.roared:      # 体力が半分になった: 怒る（後光が赤くなり、画面が揺れる）
                    self.roared = True
                    self.landed = True
                    snd("roar")
                    self._set("roar")
                else:
                    self._begin(self._next_attack(), pr)
        elif s == "roar":
            if self.st >= P["roar"]:
                self._begin("warp", pr)
        elif s == "ready":                     # 手を合わせる（予告）
            if self.st >= P["ready"]:
                self._set("cast")
        elif s == "cast":                      # 数珠を向けて、玉を、ひとつずつ飛ばす
            heights = self._volley()
            gap = P["rage_gap" if self.rage else "gap"]     # 玉と玉の間: 刀を振って、次を振れるまで（約38フレーム）に、ほぼ合わせる。続けて来ても、1つずつ斬れる
            k = (self.st - P["fire_at"]) // gap
            if self.st >= P["fire_at"] and (self.st - P["fire_at"]) % gap == 0 and 0 <= k < len(heights):
                B = C.BEAD
                y = self._ground() - B[{"L": "low", "M": "mid", "H": "high"}[heights[k]]]
                snd("bead")
                self.spawned.append(Bead(self.cx + self.facing * (self.w / 2 + 10), y, self.facing, self.a,
                                         B["rage_speed"] if self.rage else B["speed"]))
            if self.st >= P["cast_frames"] + gap * (len(heights) - 1):
                self.volley += 1
                self._set("recover")
        elif s == "ring_ready":                # まわりに、玉の輪が出る（予告）。終わりに、八方へ飛ぶ
            if self.st >= P["ring_ready"]:
                R = C.RING
                sp = R["rage_speed" if self.rage else "speed"]
                for k in range(R["count"]):
                    a = 2 * math.pi * k / R["count"]
                    snd("ring")
                    self.spawned.append(Bead(self.cx + math.cos(a) * R["radius"], self.cy + math.sin(a) * R["radius"], 1, self.a,
                                             math.cos(a) * sp, vy=math.sin(a) * sp, floor=self._ground(), reach=R["range"], ring=True))
                self._set("recover")
        elif s == "pillar_ready":              # 手を上げている間に、柱が落ちる
            if self.st >= P["pillar_frames"]:
                self._set("recover")
        elif s == "warp_out":                  # 光になって、消える
            if self.st >= P["warp_out"]:
                self.cx = self.dest
                self.facing = 1 if pr.centerx > self.cx else -1
                snd("warp_in")
                self._set("warp_in")
        elif s == "warp_in":                   # 現れて、すぐ次の攻撃へ（隙は無い）
            if self.st >= P["warp_in"]:
                self.dest = None
                self._begin(self._next_attack(True), pr)
        elif s == "recover":
            if self.st >= P["rage_recover_frames" if self.rage else "recover_frames"]:
                self._set("walk")

    def _halo(self, surface, x, y):
        """後光: 回る光の筋と、輪。予告の間は、明るく大きく。体力が半分になると、赤く、大きい"""
        H = C.HALO
        busy = self.state in ("ready", "ring_ready", "pillar_ready", "roar")
        r = H["rage_r" if self.rage else "r"] + (3 if busy and (self.t // 4) % 2 else 0)
        if self.state == "roar":
            r += self.st * H["roar_grow"] // self.P["roar"]
        col = H["rage_color" if self.rage else "color"]
        dark = tuple(c * 5 // 9 for c in col)
        for k in range(H["rays"]):
            a = self.t * H["spin"] + 2 * math.pi * k / H["rays"]
            n = r + (H["ray_long"] if k % 2 == 0 else H["ray_short"])
            p0 = (x + math.cos(a) * (r - 4), y + math.sin(a) * (r - 4))
            p1 = (x + math.cos(a) * n, y + math.sin(a) * n)
            pygame.draw.line(surface, dark, p0, p1, 3)
            pygame.draw.line(surface, col, p0, p1, 1)
        pygame.draw.circle(surface, dark, (x, y), r, 4)
        pygame.draw.circle(surface, col, (x, y), r - 1, 2)
        pygame.draw.circle(surface, (255, 250, 214), (x, y), r - 2, 1)

    def draw(self, surface, cam_x):
        r = self.rect.move(-cam_x, 0)
        P = self.P
        if self.dying or not self.a:
            super().draw(surface, cam_x)
            return
        if self.dest is not None:       # 転移: 現れる場所に、光の印（床の輪と、立ちのぼる光）
            dx, g = round(self.dest) - cam_x, round(self._ground())
            w = 26 + (self.t // 3) % 3 * 8
            pygame.draw.ellipse(surface, C.BLACK, (dx - w // 2 - 1, g - 6, w + 2, 11))
            pygame.draw.ellipse(surface, (255, 244, 170), (dx - w // 2, g - 5, w, 9), 2)
            for k in range(6):
                yy = g - 10 - ((self.t * 2 + k * 14) % 84)
                xx = dx + (k % 3 - 1) * 9
                pygame.draw.rect(surface, C.BLACK, (xx - 2, yy - 1, 4, 10))
                pygame.draw.rect(surface, (255, 236, 150), (xx - 1, yy, 2, 8))
        if self.warping:                # 光になって、薄くなる・濃くなる
            k = self.st / P["warp_out"] if self.state == "warp_out" else 1 - self.st / P["warp_in"]
            img = pygame.mask.from_surface(self.image()).to_surface(setcolor=(255, 244, 170, 255), unsetcolor=(0, 0, 0, 0))
            img.set_alpha(max(0, round(255 * (1 - k))))
            art = C.ENEMY_ART[self.KIND]
            surface.blit(img, (r.centerx - art["ax"], r.bottom - art["h"]))
            return
        bob = round(math.sin(self.t / 18) * P["bob"]) if self.intro_done else 0     # 浮いて、ゆっくり上下する（見た目だけ）
        self._halo(surface, r.centerx, r.centery - C.HALO["dy"] + bob)
        self.cy += bob
        super().draw(surface, cam_x)
        self.cy -= bob
        if self.state == "ready":       # 予告: これから飛ばす玉の高さに、光の点を並べる（飛ばす順に、手前から）
            B = C.BEAD
            for k, h in enumerate(self._volley()):
                y = round(self._ground() - B[{"L": "low", "M": "mid", "H": "high"}[h]])
                x = round(self.cx + self.facing * (self.w / 2 + 12 + k * 12)) - cam_x
                rr = 2 + (1 if (self.t // 5 + k) % 2 else 0)
                pygame.draw.circle(surface, (150, 96, 8), (x, y), rr + 1)
                pygame.draw.circle(surface, (255, 244, 170), (x, y), rr)
        elif self.state == "ring_ready":    # 予告: まわりに、玉の輪。飛ぶ向きへ、短い筋
            R = C.RING
            grow = R["radius"] * self.st / P["ring_ready"]
            for k in range(R["count"]):
                a = 2 * math.pi * k / R["count"]
                x, y = r.centerx + math.cos(a) * grow, r.centery + math.sin(a) * grow
                if (self.t // 4) % 2:
                    pygame.draw.line(surface, (255, 244, 170), (x, y), (x + math.cos(a) * 9, y + math.sin(a) * 9), 1)
                pygame.draw.circle(surface, (150, 96, 8), (x, y), 4)
                pygame.draw.circle(surface, (252, 212, 64), (x, y), 3)

    def image(self):
        if self.dying:
            return self._death()[1 if self.down_t else 0]
        s = self.state
        P = self.P
        if s == "ready":                        # 合掌（数珠の玉の予告）
            return self._frames("pray")[min(self.st * 2 // P["ready"], 1)]
        if s == "cast":                         # 数珠を向ける
            return self._frames("cast")[(self.st // 6) % 2]
        if s == "pillar_ready":                 # 6本の腕を広げる（光の柱）
            return self._frames("spread")[(self.st // 8) % 2]
        if s == "ring_ready":                   # 数珠を持つ（数珠の輪の予告）
            return self._frames("hold")[0]
        if s == "roar":                         # 怒る（口を開ける → 目が赤く光る）
            return self._frames("roar")[min(self.st * 2 // P["roar"], 1)]
        if self.rage and self.roared:           # 怒ったあとは、赤い目のまま
            return self._frames("roar")[1]
        return self._frames("idle")[0]


class Boss2(Boss):
    """2面のボス（二代・基衡）。上から降りてきて、「歩く → 構える → 扇の風 / 扇を投げる / 花びらの雨 → 隙」を繰り返す。
    攻撃を受けても、ひるまない。体力が半分になると、歩く時間と隙が短くなり、花びらの雨が入る。
    月見坂の本家だけ、大風（Gale）も使う。低い大風は、床が風で、足場の上は静か。高い大風は、足場の高さが風で、床は静か。
    風の帯が出る場所を見て、上と下を行き来する。風が吹いている間に、扇を投げてくる"""
    P = C.BOSS2
    KIND = "boss2"
    gale_high = False       # いま呼んでいる大風は、高い大風

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.pattern = kw.get("pattern") or C.BOSS2_PATTERN

    @property
    def move(self):
        """次の攻撃（W=風 / T=扇 / P=花びら / G=低い大風 / H=高い大風）"""
        rage = C.BOSS2_GALE_RAGE_PATTERN if set("GH") & set(self.pattern) else C.BOSS2_RAGE_PATTERN
        seq = rage if self.rage else self.pattern
        return seq[self.count % len(seq)]

    def _after_wind(self, pr):
        """風・大風のあと: 次が扇なら、すぐ投げる（連携）。そうでなければ、隙"""
        if self.move == "T":
            self.facing = 1 if pr.centerx > self.cx else -1
            self.chain = True
            self.count += 1
            self._set("throw_ready")
        else:
            self._set("recover")

    def think(self, pr, stage_w, terrain=None):
        P = self.P
        s = self.state
        if s in self.INTRO or s == "drop":     # 出てくる場面は、1面のボスと同じ
            return Boss.think(self, pr, stage_w, terrain)
        self.st += 1
        if s in ("walk", "recover"):
            self.facing = 1 if pr.centerx > self.cx else -1
        if s == "walk":
            if abs(pr.centerx - self.cx) > P["near"]:
                self.cx = max(self.x_min, min(self.cx + self.facing * P["speed"], self.x_max))
            if self.st >= P["rage_walk_frames" if self.rage else "walk_frames"]:
                self.gale_high = self.move == "H"
                self._set({"W": "wind_ready", "T": "throw_ready", "P": "petal_ready", "G": "gale_ready", "H": "gale_ready"}[self.move])
                self.count += 1
        elif s == "wind_ready":
            if self.st >= P["wind_ready"]:
                self._set("wind")
        elif s == "wind":
            if self.st == P["wind_at"]:
                snd("gust")
                self.spawned.append(Gust(self.cx + self.facing * (self.w / 2 + 12), self.floor - C.GUST["h"] / 2,
                                         self.facing, self.a))
            if self.st >= P["wind_frames"]:
                self._after_wind(pr)        # 風で押し戻して、すぐ、扇を投げる（連携）
        elif s == "gale_ready":     # 大風の予告: 扇を高く上げて、止まる。風の帯が、うすく現れる（低いか、高いかは、帯の場所で分かる。Gale が描く）
            if self.st == 1:
                snd("charge")
                self.spawned.append(Gale(self.x_min - self.w / 2, self.x_max + self.w / 2, self.floor, self.facing, self.a,
                                         high=self.gale_high))
            if self.st >= C.GALE["warn"]:
                self._set("gale")
        elif s == "gale":           # 扇を振り下ろす。風は、このあとも、吹き続ける
            if self.st >= P["gale_frames"]:
                self._after_wind(pr)
        elif s == "throw_ready":
            if self.st >= (P["throw_ready_chain"] if self.chain else P["throw_ready"]):
                self._set("throw")
        elif s == "throw":
            if self.st == P["throw_at"]:
                snd("fan")
                self.spawned.append(Fan(self.cx + self.facing * (self.w / 2 + 6), self.floor - C.FAN["y"],
                                        self.facing, self.a, self))
            if self.rage and self.st == P["throw_at"] + P["fan2_delay"]:      # 体力が半分以下: 2枚目（足元）
                snd("fan")
                self.spawned.append(Fan(self.cx + self.facing * (self.w / 2 + 6), self.floor - P["fan2_y"],
                                        self.facing, self.a, self))
            if self.st >= P["throw_frames"] + (P["fan2_delay"] if self.rage else 0):
                self.chain = False
                self._set("recover")
        elif s == "petal_ready":
            if self.st >= P["petal_ready"]:
                self._set("petal")
        elif s == "petal":
            if self.st == 1:
                self._rain(pr)
            if self.st >= P["petal_frames"]:
                self._set("recover")
        elif s == "recover":
            if self.st >= P["rage_recover_frames" if self.rage else "recover_frames"]:
                self._set("walk")

    def _rain(self, pr):
        """花びらの雨: 主人公の前後に、ずらして落とす（立ち止まっていると、当たる）"""
        K = C.PETAL
        for i in range(K["count"]):
            off = (i - (K["count"] - 1) / 2) * K["spread"]
            x = max(self.x_min - self.w / 2, min(pr.centerx + off, self.x_max + self.w / 2))
            snd("petal")
            self.spawned.append(Petal(x, self.floor, self.a, K["stagger"] * i))

    def image(self):
        f = self.a.boss2
        d = self.facing > 0
        if self.dying:
            return f["down" if self.down_t else "hurt"][d]
        s = self.state
        if s in ("drop", "wind_ready", "gale_ready"):
            name = "fan_up"
        elif s == "gale":
            name = "fan_swing"
        elif s == "wind":
            name = "fan_up" if self.st < self.P["wind_at"] else "fan_swing"
        elif s == "throw_ready":
            name = "throw_0"
        elif s == "throw":
            name = "throw_1"
        elif s in ("petal_ready", "petal", "pose"):
            name = "petal"
        elif s == "walk":
            name = "walk_%d" % ((self.t // 14) % 2)
        else:   # wait / land / recover
            name = "idle_%d" % (0, 1, 2, 1)[(self.t // 12) % 4]
        if self.flash and s in ("walk", "recover"):
            name = "hurt"
        return f[name][d]


class Bead(Shot):
    """数珠の玉: 決まった高さを、まっすぐ飛ぶ。刀で消せる。当たるとダメージ"""
    damage = C.BEAD["damage"]
    cut_pad = (C.BEAD["cut_pad"], 6)    # 小さいので、斬る判定を、少し広げる

    def __init__(self, x, y, direction, assets, speed=None, vy=0.0, floor=None, reach=None, ring=False):
        self.a = assets
        self.ring = ring                          # 数珠の輪の玉: 斬れない（よける）。まっすぐ飛ぶ玉は、斬れる（金色）
        self.cuttable = not ring
        self.px, self.py = float(x), float(y)
        self.dir = direction
        self.speed = speed or C.BEAD["speed"]     # 横の速さ（数珠の輪の玉は、負にもなる）
        self.vy = vy                              # 上下の速さ（数珠の輪の玉）
        self.floor = floor                        # 地面に届いたら、消える高さ（数珠の輪の玉）
        self.reach = reach or C.BEAD["range"]
        self.travel = 0.0
        self.t = 0
        self.alive = True

    @property
    def rect(self):
        w, h = C.BEAD["w"], C.BEAD["h"]
        return pygame.Rect(round(self.px - w / 2), round(self.py - h / 2), w, h)

    def update(self, stage_w):
        self.px += self.dir * self.speed
        self.py += self.vy
        self.travel += math.hypot(self.speed, self.vy)
        self.t += 1
        if self.travel > self.reach or not (0 <= self.px <= stage_w) or (self.floor is not None and self.py > self.floor - 2):
            self.alive = False

    def draw(self, surface, cam_x):
        x, y = round(self.px) - cam_x, round(self.py)
        pulse = (self.t // C.BEAD["ticks"]) % 2
        if self.ring:       # よける玉: 赤黒く、とげがある
            r = 4 + pulse
            for k in range(8):
                a = k * math.pi / 4 + self.t * 0.1
                pygame.draw.line(surface, (40, 8, 24), (x, y), (x + round(math.cos(a) * (r + 3)), y + round(math.sin(a) * (r + 3))), 2)
            pygame.draw.circle(surface, (24, 4, 16), (x, y), r + 1)
            pygame.draw.circle(surface, (196, 28, 56), (x, y), r)
            pygame.draw.circle(surface, (255, 150, 150), (x - 1, y - 1), 1)
            return
        r = 5 + pulse       # 斬る玉: 大きな金色。白い光の縁
        pygame.draw.circle(surface, (255, 252, 230), (x, y), r + 2, 1)
        pygame.draw.circle(surface, (150, 96, 8), (x, y), r + 1)
        pygame.draw.circle(surface, (252, 212, 64), (x, y), r)
        pygame.draw.circle(surface, (255, 250, 214), (x - 2, y - 2), 2)


class Pillar(Shot):
    """光の柱（清衡）: 落ちる場所に、柱と同じ太さの、うすい光と、床の印が出る（予告。だんだん濃くなり、落ちる直前は、速く点滅する）。
    そのあと、上から、太い光の柱が落ちる。刀では消せない。うすい光の間に立てば、当たらない"""
    cuttable = False
    damage = C.PILLAR["damage"]

    def __init__(self, x, floor, assets, delay=0, warn=None, quiet=False):
        self.a = assets
        self.quiet = quiet    # 予告の音を鳴らさない（何本も続けて落ちるとき、音が重なって、うるさいため。鳴らすのは、最初の1本だけ）
        self.px, self.floor = float(x), float(floor)
        self.warn = warn or C.PILLAR["warn"]
        self.t = -delay       # 0になるまで、まだ出ない
        self.alive = True
        self._glow = None     # 予告の、うすい光の絵（描くときに作って、使い回す）

    @property
    def active(self):
        return self.t >= self.warn

    @property
    def rect(self):
        if not self.active:
            return pygame.Rect(-100, -100, 0, 0)      # 落ちる前は、当たらない
        w = C.PILLAR["w"]
        return pygame.Rect(round(self.px - w / 2), 0, w, round(self.floor))

    def update(self, stage_w):
        self.t += 1
        if self.t == 1 and not self.quiet:
            snd("pillar_warn")
        elif self.t == self.warn:
            snd("beam")
        if self.t >= self.warn + C.PILLAR["beam"]:
            self.alive = False

    def draw(self, surface, cam_x):
        if self.t < 0:
            return
        L = C.PILLAR
        x, floor = round(self.px) - cam_x, round(self.floor)
        if not self.active:     # 予告: 柱と同じ太さの、うすい光（だんだん濃くなる。両端に、縁の線）と、床の印。落ちる直前は、速く点滅
            w, u = L["w"], self.t / self.warn
            last = self.warn - self.t <= L["flash"]
            blink = (self.t // (2 if last else 5)) % 2
            if self._glow is None:
                self._glow = pygame.Surface((w, floor), pygame.SRCALPHA)
            self._glow.fill((255, 226, 120, round(28 + 78 * u) + (50 if last and blink else 0)))
            edge = (255, 246, 196, round(110 + 120 * u))
            pygame.draw.rect(self._glow, edge, (0, 0, 1, floor))
            pygame.draw.rect(self._glow, edge, (w - 1, 0, 1, floor))
            surface.blit(self._glow, (x - w // 2, 0))
            col = (255, 250, 214) if blink else (255, 196, 64)
            pygame.draw.ellipse(surface, C.BLACK, (x - w // 2 - 3, floor - 5, w + 6, 9))
            pygame.draw.ellipse(surface, col, (x - w // 2 - 2, floor - 4, w + 4, 7))
            return
        k = self.t - self.warn
        w = L["w"] if k < L["beam"] - 4 else L["w"] // 2        # 終わりは、細くなって消える
        pygame.draw.rect(surface, (150, 96, 8), (x - w // 2 - 2, 0, w + 4, floor))
        pygame.draw.rect(surface, (255, 204, 72), (x - w // 2, 0, w, floor))
        pygame.draw.rect(surface, (255, 252, 226), (x - w // 4, 0, w // 2, floor))
        pygame.draw.ellipse(surface, (255, 252, 226), (x - w, floor - 6, w * 2, 10))


class Gust(Shot):
    """扇の風: 地面ぞいに、ゆっくり進む。ダメージはないが、当たると押し戻される。刀では消せない（ジャンプで越える）"""
    push = C.GUST["push"]
    cuttable = False

    def __init__(self, x, y, direction, assets):
        self.a = assets
        self.px, self.py = float(x), float(y)
        self.dir = direction
        self.reach = C.GUST["range"]
        self.travel = 0.0
        self.t = 0
        self.alive = True

    @property
    def rect(self):
        w, h = C.GUST["w"], C.GUST["h"]
        return pygame.Rect(round(self.px - w / 2), round(self.py - h / 2), w, h)

    def update(self, stage_w):
        self.px += self.dir * C.GUST["speed"]
        self.travel += C.GUST["speed"]
        self.t += 1
        if self.travel > self.reach or not (0 <= self.px <= stage_w):
            self.alive = False

    def draw(self, surface, cam_x):
        """突風: 先頭に、三日月の形の風の刃。うしろに、渦を巻く風の筋と、舞い上がる葉。終わりに近づくと、薄くなる"""
        K = C.GUST
        tail = min(60, self.reach * 0.4)       # 終わりの、薄くなっていく長さ
        fade = 1.0 if self.travel < self.reach - tail else max(0.25, (self.reach - self.travel) / tail)
        frames = self.a.gust[self.dir > 0] if self.a and getattr(self.a, "gust", None) else None
        if frames:      # 絵（tools/make_gust.py）: 先頭の渦を、当たり判定に合わせる。終わりは、点滅して消える
            if fade < 1.0 and (self.t // 3) % 2:
                return
            img = frames[(self.t // K["ticks"]) % len(frames)]
            r = self.rect.move(-cam_x, 0)
            x = r.right + K["lead"] - img.get_width() if self.dir > 0 else r.left - K["lead"]
            surface.blit(img, (x, r.bottom + K["sink"] - img.get_height()))
            return
        W, H = 78, K["h"] + 14
        img = pygame.Surface((W, H), pygame.SRCALPHA)
        a = lambda v: int(v * fade)     # noqa: E731
        front = W - 14      # 先頭（右向きで描いて、あとで向きを変える）
        # 先頭の、三日月の刃（暗い縁 → 白 → 内側を抜く）
        pygame.draw.ellipse(img, (40, 70, 110, a(230)), (front - 15, 1, 28, H - 2))
        pygame.draw.ellipse(img, (240, 252, 255, a(245)), (front - 13, 3, 24, H - 6))
        pygame.draw.ellipse(img, (0, 0, 0, 0), (front - 22, 0, 24, H))
        pygame.draw.ellipse(img, (170, 220, 250, a(150)), (front - 9, 9, 12, H - 18))
        pygame.draw.ellipse(img, (0, 0, 0, 0), (front - 16, 6, 14, H - 12))
        # 風の筋（うしろへ流れる。長さと位置が、波打つ）
        for i, (y, ln) in enumerate(((5, 30), (13, 46), (22, 38), (31, 50), (40, 28))):
            ph = (self.t // K["ticks"] + i * 2) % 4
            x1 = front - 12 - ph * 3
            wob = round(math.sin((self.t + i * 9) / 5) * 2)
            for k in range(3):      # うしろほど、薄く、細く
                seg = ln // 3
                xa = x1 - seg * (k + 1)
                pygame.draw.rect(img, (40, 70, 110, a(150 - k * 45)), (xa, y + wob + 2, seg, 1))
                pygame.draw.rect(img, (236, 250, 255, a(235 - k * 70)), (xa, y + wob, seg, 2 if k < 2 else 1))
        # 舞い上がる葉（3枚。回りながら、うしろへ）
        for i in range(3):
            u = (self.t * 2 + i * 23) % 48
            lx = front - 16 - u
            ly = H - 8 - round(abs(math.sin((u + i * 11) / 7)) * (H - 16))
            if lx > 2:
                pygame.draw.rect(img, (30, 60, 30, a(220)), (lx - 1, ly - 1, 5, 4))
                pygame.draw.rect(img, (150, 210, 110, a(255)), (lx, ly, 3, 2))
        if self.dir < 0:
            img = pygame.transform.flip(img, True, False)
        r = self.rect.move(-cam_x, 0)
        x = r.right + 14 - W if self.dir > 0 else r.left - 14
        surface.blit(img, (x, r.centery - H // 2))


class HillGust(Gust):
    """山おろし（月見坂の仕掛け）: 坂の上から、地面ぞいに、吹き下ろしてくる風。当たると、押し戻される（ダメージは無い）。跳んで越える。
    遠くから見えて、ゆっくり来る。段差では、地面の高さに合わせて、降りていく。穴の上は、そのままの高さで渡る"""

    def __init__(self, x, direction, assets, terrain, reach):
        h = terrain.height_at(x)
        super().__init__(x, (C.FLOOR_Y if h is None else h) - C.GUST["h"] / 2, direction, assets)
        self.terrain = terrain
        self.reach = reach
        snd("gust")

    def update(self, stage_w):
        super().update(stage_w)
        h = self.terrain.height_at(self.px)
        if h is not None:
            self.py = h - C.GUST["h"] / 2


class Gale(Shot):
    """大風（月見坂の基衡）: ボスの間の、端から端まで、横に吹く、強い風。ダメージは無いが、風の帯の中にいると、吹いている間、押され続ける。
    低い大風は、床ぞい（足場の上は、静か）。高い大風（high）は、足場の高さ（床は、静か。跳ぶと、流される）。
    吹く前に、うすい風の帯と、弱い風の筋と、木の葉が、現れる（予告。帯の場所で、低いか高いかが分かる）。刀では消せない"""
    cuttable = False

    def __init__(self, x0, x1, floor, direction, assets, high=False):
        K = C.GALE
        self.a = assets
        self.x0, self.x1, self.floor = round(x0), round(x1), round(floor)
        self.dir = direction
        self.high = high
        self.h = K["high_h"] if high else K["h"]                                  # 帯の高さ
        self.top = self.floor - (K["high_bottom"] + self.h if high else self.h)    # 帯の上の縁
        self.px, self.py = (x0 + x1) / 2, self.top + self.h / 2
        self.t = 0
        self.alive = True
        self._band = None       # 風の帯の絵（描くときに作って、使い回す）

    @property
    def blowing(self):
        return self.t >= C.GALE["warn"]

    @property
    def push(self):
        return C.GALE["push"] if self.blowing else 0

    @property
    def rect(self):
        if not self.blowing:
            return pygame.Rect(-100, -100, 0, 0)      # 予告の間は、当たらない
        return pygame.Rect(self.x0, self.top, self.x1 - self.x0, self.h)

    def update(self, stage_w):
        self.t += 1
        if self.t == C.GALE["warn"]:
            snd("gust")
        if self.t >= C.GALE["warn"] + C.GALE["blow"]:
            self.alive = False

    def draw(self, surface, cam_x):
        """風の帯（当たり判定と同じ場所）を、うすい白で塗って、風の筋と、木の葉を流す。縁に、波打つ線（帯の場所が、ひと目で分かる）。
        予告は、帯がだんだん濃くなり、筋は、少なく・短く・ゆっくり。吹いている間は、帯が濃く、筋は、多く・長く・速く"""
        K = C.GALE
        blow = self.blowing
        n, ln0, speed, leaves = ((K["streaks"], K["long"], K["speed"], K["leaves"]) if blow
                                 else (K["warn_streaks"], K["warn_long"], K["warn_speed"], K["warn_leaves"]))
        W, top, H = self.x1 - self.x0, self.top, self.h
        left, right = self.x0 - cam_x, self.x1 - cam_x
        if self._band is None:
            self._band = pygame.Surface((W, H), pygame.SRCALPHA)
        grow = 1.0 if blow else min(1.0, self.t / (K["warn"] * 0.6))      # 予告のはじめに、すっと現れる
        self._band.fill((214, 236, 255, round((K["alpha"] if blow else K["warn_alpha"]) * grow)))
        for x in range(0, W, 4):        # 縁: 波が、風下へ流れる（高い大風は、下の縁にも。低い大風の下は、床）
            wob = round(math.sin((x - self.dir * self.t * (speed * 0.6)) / 9) * 1.5)
            edge = (244, 252, 255, round((235 if blow else 170) * grow))
            pygame.draw.rect(self._band, edge, (x, 2 + wob, 4, 2))
            if self.high:
                pygame.draw.rect(self._band, edge, (x, H - 4 - wob, 4, 2))
        surface.blit(self._band, (left, top))

        def along(u):       # 風上の端からの距離 → 画面の x
            return left + u if self.dir > 0 else right - u

        for i in range(n):
            y = top + 7 + round((H - 14) * i / (n - 1))
            ln = ln0 + (i * 7) % 14
            head = (i * 97 + self.t * (speed + (i % 3) * 0.7)) % (W + ln)     # 筋の先頭（風下側）
            xa, xb = sorted((along(head - ln), along(head)))
            xa, xb = max(left, round(xa)), min(right, round(xb))
            if xb - xa >= 2:
                pygame.draw.rect(surface, (40, 70, 110), (xa, y + 2, xb - xa, 1))     # 暗い影（明るい背景でも、見える）
                pygame.draw.rect(surface, (236, 250, 255), (xa, y, xb - xa, 2))
        for i in range(leaves):     # 木の葉（回りながら、流れる）
            u = (i * 131 + self.t * (speed * 0.8 + (i % 2) * 0.5)) % W
            lx = round(along(u))
            ly = top + H - 9 - round(abs(math.sin((self.t + i * 13) / 6)) * (H - 18))
            pygame.draw.ellipse(surface, (24, 52, 24), (lx - 1, ly - 1, 9, 6))
            pygame.draw.ellipse(surface, (150, 210, 110), (lx, ly, 7, 4))
            pygame.draw.rect(surface, (214, 240, 150), (lx + 1 + (self.t // 4 + i) % 3, ly + 1, 2, 2))    # 葉の、光る面（回って見える）


class Fan(Shot):
    """投げた扇: ボスの向きに飛んで、距離まで行くと、その場で止まって白く光り（戻る予告）、ボスのところへ戻る。
    刀で消せる。当たるとダメージ"""
    cuttable = True
    damage = C.FAN["damage"]

    def __init__(self, x, y, direction, assets, owner):
        self.a = assets
        self.px, self.py = float(x), float(y)
        self.dir = direction
        self.owner = owner
        self.travel = 0.0
        self.back = False
        self.turn_t = 0     # 折り返す前に、止まっている残りフレーム（戻ってくる予告）
        self.t = 0
        self.alive = True

    @property
    def rect(self):
        w, h = C.FAN["w"], C.FAN["h"]
        return pygame.Rect(round(self.px - w / 2), round(self.py - h / 2), w, h)

    def update(self, stage_w):
        K = C.FAN
        self.t += 1
        if not self.back:
            self.px += self.dir * K["speed"]
            self.travel += K["speed"]
            if self.travel >= K["range"] or not (0 <= self.px <= stage_w):
                self.back = True
                self.turn_t = K["turn"]
        elif self.turn_t:       # 折り返す前に、止まって光る（うしろから戻ってくるので、先に知らせる）
            self.turn_t -= 1
        else:
            d = self.owner.cx - self.px
            if abs(d) <= K["speed"] + 4 or not self.owner.active:
                self.alive = False
                return
            self.px += K["speed"] if d > 0 else -K["speed"]

    def draw(self, surface, cam_x):
        if not (self.a and self.a.boss2):
            pygame.draw.rect(surface, C.WHITE, self.rect.move(-cam_x, 0))
            return
        spun = pygame.transform.rotate(self.a.boss2["fan"][True], -(self.t * C.FAN["spin"]) * self.dir % 360)
        if self.turn_t and (self.turn_t // 3) % 2:      # 戻る予告: 白く光る
            spun = pygame.mask.from_surface(spun).to_surface(setcolor=C.WHITE, unsetcolor=(0, 0, 0, 0))
        spun = _rimmed(spun)                            # 白い縁取り（どの背景でも、見えるように）
        x, y = round(self.px) - cam_x, round(self.py)
        surface.blit(spun, (x - spun.get_width() // 2, y - spun.get_height() // 2))
        if self.turn_t:                                 # 戻る向きの印（小さな三角）
            d = 1 if self.owner.cx > self.px else -1
            tip = x + d * 18
            pygame.draw.polygon(surface, C.BLACK, ((tip + d * 2, y), (tip - d * 5, y - 6), (tip - d * 5, y + 6)))
            pygame.draw.polygon(surface, (255, 236, 120), ((tip, y), (tip - d * 4, y - 4), (tip - d * 4, y + 4)))


class Petal(Shot):
    """花びら: 落ちる場所に、先に目印（地面の楕円と、落ちてくる筋道の点線）が出る。そのあと、上から落ちてくる。刀で消せる。当たるとダメージ"""
    cuttable = True
    damage = C.PETAL["damage"]

    def __init__(self, x, floor, assets, delay=0):
        self.a = assets
        self.px, self.floor = float(x), float(floor)
        self.py = self.floor - C.FLOOR_Y + C.PETAL["top"]     # 画面の上から（床が低い所では、そのぶん低い所から）
        self.t = -delay       # 0になるまで、まだ出ない
        self.alive = True

    @property
    def falling(self):
        return self.t >= C.PETAL["warn"]

    @property
    def rect(self):
        if not self.falling:
            return pygame.Rect(-100, -100, 0, 0)      # 落ちる前は、当たらない
        w, h = C.PETAL["w"], C.PETAL["h"]
        return pygame.Rect(round(self.px - w / 2), round(self.py - h / 2), w, h)

    def update(self, stage_w):
        self.t += 1
        if self.falling:
            self.py += C.PETAL["speed"]
            if self.py >= self.floor - C.PETAL["h"] / 2:
                self.alive = False

    def draw(self, surface, cam_x):
        if self.t < 0:
            return
        x = round(self.px) - cam_x
        floor = round(self.floor)
        if not self.falling:    # 目印: だんだん大きくなる楕円（点滅。黒い縁で、どの地面の上でも見える）と、落ちてくる筋道（点線）
            w = 10 + 12 * self.t // C.PETAL["warn"]
            col = (255, 236, 120) if (self.t // 4) % 2 else (255, 150, 180)
            pygame.draw.ellipse(surface, C.BLACK, (x - w // 2 - 1, floor - 4, w + 2, 7))
            pygame.draw.ellipse(surface, col, (x - w // 2, floor - 3, w, 5))
            if self.t * 2 >= C.PETAL["warn"]:           # 後半は、上から下へ、点線で筋道を見せる
                dash = pygame.Surface((2, 5), pygame.SRCALPHA)
                dash.fill((255, 236, 180, 130))
                for yy in range((self.t * 2) % 12, floor - 6, 12):
                    surface.blit(dash, (x - 1, yy))
            return
        y = round(self.py)
        tail = pygame.Surface((2, 14), pygame.SRCALPHA)     # 落ちてくる花びら: うしろ（上）に、光の尾
        tail.fill((255, 220, 230, 110))
        surface.blit(tail, (x - 1, y - 18))
        pygame.draw.rect(surface, C.BLACK, (x - 5, y - 4, 10, 9))             # 黒い縁
        pygame.draw.rect(surface, (252, 252, 252), (x - 4, y - 3, 8, 7))      # 白い縁取り
        pygame.draw.rect(surface, (240, 110, 150), (x - 3, y - 2, 6, 5))      # 花びら（ふちを濃く、中を薄く）
        pygame.draw.rect(surface, (255, 190, 208), (x - 2, y - 2, 4, 4))


def make_enemy(kind, x, assets=None, terrain=None):
    """配置表の名前から敵を作る（地上の敵は、そこにある地面の上に立つ）"""
    if kind == "ochimusha":
        return Ochimusha(x, assets, terrain.height_at(x) if terrain else None)
    if kind == "miira":
        return Miira(x, assets, terrain.height_at(x) if terrain else None)
    if kind in ("kitsunebi_low", "kitsunebi_high", "karasu"):     # 飛ぶ敵の高さは、そこの地面から測る（高い所で、地面に埋まらないように）
        e = Karasu(x, assets) if kind == "karasu" else Kitsunebi(x, kind.split("_")[1], assets)
        h = terrain.height_at(x) if terrain else None
        if h is not None:
            e.cy += h - C.FLOOR_Y
            if kind != "karasu":
                e.base_y = e.cy
        return e
    if kind == "tengu":
        return Tengu(x, assets, terrain.height_at(x) if terrain else None)
    if kind == "yumihei":
        return Archer(x, assets, terrain.height_at(x) if terrain else None)
    if kind == "tachiojo":
        return Tachiojo(x, assets, terrain.height_at(x) if terrain else None)
    raise ValueError(kind)


class Shuriken:
    damage = C.SHURIKEN_DAMAGE
    throw_id = None     # 何回目の投げか（Game が付ける。三方手裏剣の3つは、同じ番号。無ければ、1つずつ別の投げ）

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


class Wave(Shot):
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
    damage = C.SLASH["damage"]
    throw_id = None     # 投げの番号は、無い（当たれば、必ずダメージ）

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
        snacks = getattr(assets, "snacks", None) if assets else None
        # 手裏剣の元（dango）は、いろんな食べ物の絵で出る。置き場所で、食べ物が決まる（やり直しても、同じ）
        self.food = snacks[(idx if idx >= 0 else int(x) // 7) % len(snacks)] if kind == "dango" and snacks else kind

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
            if self.cy > C.FALL_Y + (terrain.depth_at(self.cx) if terrain else 0):     # 穴に落ちた
                self.alive = False

    def draw(self, surface, cam_x):
        if self.drop and self.life < 120 and (self.life // 5) % 2:
            return   # 消える前は、点滅
        x = round(self.cx) - cam_x
        y = round(self.cy + (math.sin(self.t / 18) * 2 if self.resting else 0))
        imgs = getattr(self.a, "item", None) if self.a else None
        if imgs and self.food in imgs:
            img = imgs[self.food]
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


class Lantern:
    """道ばたの石灯籠。刀・手裏剣・光波で壊すと、中の物（kind）が出る。壊したものは、やられて再開しても、壊れたまま。
    背景の灯籠（壊せない）と違い、火がともって、ゆらいでいる"""

    def __init__(self, kind, x, floor, assets=None, idx=-1, broken=False):
        self.kind = kind
        self.idx = idx      # 配置表の何番目か
        self.a = assets
        self.cx, self.floor = float(x), float(floor)
        self.t = 0
        self.broken = broken
        self.break_t = 9999 if broken else 0    # 壊れてからのフレーム数

    @property
    def active(self):
        """まだ壊れていない（攻撃が当たる）"""
        return not self.broken

    @property
    def rect(self):
        T = C.TORO
        return pygame.Rect(round(self.cx - T["w"] / 2), round(self.floor - T["h"]), T["w"], T["h"])

    def hit(self):
        """壊す。壊れたら True（中の物を出すのは、Game）"""
        if self.broken:
            return False
        self.broken, self.break_t = True, 0
        snd("break")
        return True

    def update(self):
        self.t += 1
        if self.broken:
            self.break_t += 1

    def draw(self, surface, cam_x):
        T = C.TORO
        imgs = getattr(self.a, "toro", None) if self.a else None
        x, y = round(self.cx) - cam_x, round(self.floor)
        if not imgs:        # 絵がないときの仮の図形
            color = (96, 92, 84) if self.broken else (160, 152, 136)
            r = self.rect.move(-cam_x, 0)
            pygame.draw.rect(surface, C.BLACK, r.inflate(2, 2))
            pygame.draw.rect(surface, color, r if not self.broken else (r.x, r.bottom - 12, r.w, 12))
            return
        if not self.broken:
            img = imgs["lit"][(self.t // T["flicker"]) % len(imgs["lit"])]
        elif self.break_t < T["break_ticks"] * len(imgs["break"]):
            img = imgs["break"][self.break_t // T["break_ticks"]]
        else:
            img = imgs["broken"]
        surface.blit(img, (x - T["ax"], y - img.get_height() + 2))
        if self.broken and self.break_t < T["shard_life"]:      # かけらが、弧を描いて飛び散る
            for i, shard in enumerate(imgs["shard"]):
                u = self.break_t
                vx = (i - 1) * T["shard_vx"] + (0.5 if i == 1 else 0)
                sx = x + vx * u
                sy = y - T["h"] * 0.6 + (T["shard_vy"] - i * 0.5) * u + 0.5 * C.DROP_GRAVITY * u * u
                if sy < y:
                    surface.blit(shard, (round(sx) - shard.get_width() // 2, round(sy) - shard.get_height() // 2))


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
