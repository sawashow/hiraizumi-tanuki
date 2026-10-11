"""1面（月見坂）の地形。地面は「高さのある区間」の並び（区間のすき間が穴）、足場は一方通行の浮き板。
区間の横の面は壁になる（ぶつかると止まる。ジャンプで上に乗る）"""
import config as C

T = C.FLOOR_Y   # いちばん低い地面の高さ。ここから16ずつ高くなる
# 地面の区間 (x0, x1, 上面の高さ)。区間と区間のすき間が穴
GROUND = (
    (0, 360, T),
    (360, 470, T - 16),        # 石段を登る
    (470, 640, T - 32),        # 高台
    (640, 760, T - 16),        # 石段を降りる
    (760, 1100, T),
    # 穴1: 1100〜1180（幅80）。全力ジャンプで越えられる
    (1180, 1280, T - 16),
    (1280, 1400, T - 32),      # 登りきった高台
    (1400, 1500, T),           # 谷。見下ろして戦う
    (1500, 1580, T - 150),     # 谷の右の、高い塔。足場を登って、てっぺんへ
    (1580, 1650, T - 32),      # 塔から、飛び降りる先
    # 穴2: 1650〜1780（幅130）。ジャンプでは届かない。足場を使う
    (1780, 1900, T - 16),
    (1900, 2020, T - 48),      # いちばん高い所
    (2020, 2140, T - 16),
    (2140, 2180, T),
    # 穴3: 2180〜2300（幅120）。同じく足場を使う
    (2300, 2520, T - 16),      # ひと息つける所
    (2520, 2640, T - 32),      # また登る
    (2640, 2700, T - 48),
    # 穴4: 2700〜2780（幅80）。高い所から、跳んで越える
    (2780, 2960, T - 16),      # 低い広場。上に足場
    (2960, 3040, T - 48),      # 石垣。跳んで登る
    # 穴5: 3040〜3170（幅130）。足場を使う
    (3170, 3330, T - 32),
    (3330, C.STAGE_W + 120, T),   # 最後の平地（敵が混ざって出る）。面の端の先は、クリアのときに走り抜ける分
)
# 浮き足場（一方通行）: (x0, x1, 上面の高さ)。ジャンプで下から突き抜けて乗れる
PLATFORMS = (
    # 序盤の上の道（石段の上を、足場でつないで登る）
    (420, 460, T - 70),
    (500, 540, T - 90),
    (580, 620, T - 70),
    (880, 944, T - 62),         # 地面の上に浮かぶ足場（高く跳ぶ練習）
    (1120, 1160, T - 50),       # 穴1の真ん中（越えるより、渡る道）
    # 谷の上の道（登っていくと、金の葉）
    (1410, 1445, T - 56),       # 谷の塔を登る足場（下から順に）
    (1455, 1490, T - 108),
    (1690, 1740, T - 46),       # 穴2の真ん中
    (1930, 1990, T - 110),      # いちばん高い所の、さらに上
    (2210, 2260, T - 40),       # 穴3の真ん中
    (2560, 2610, T - 96),       # 登り坂の上（団子）
    (2840, 2900, T - 72),       # 広場の上（おにぎり）
    (3080, 3130, T - 70),       # 穴5の真ん中
    (3440, 3500, T - 60),       # 最後の平地の上
)
# アイテム (種類, x, y)。x, y は中心。dango=スコア / onigiri=回復 / leaf=強化（光波）
ITEMS = (
    ("dango", 150, T - 14), ("dango", 180, T - 14), ("dango", 210, T - 14),
    ("dango", 440, T - 88), ("onigiri", 520, T - 108), ("dango", 600, T - 88),
    ("dango", 830, T - 14), ("dango", 860, T - 14),
    ("dango", 912, T - 80),
    ("dango", 1112, T - 40), ("dango", 1140, T - 68), ("dango", 1168, T - 40),
    ("onigiri", 1340, T - 46),                       # 中間地点のあと、高台の上
    ("dango", 1428, T - 74), ("dango", 1472, T - 126),
    ("dango", 1515, T - 168), ("leaf", 1540, T - 170), ("dango", 1565, T - 168),
    ("dango", 1702, T - 64), ("dango", 1715, T - 74), ("dango", 1728, T - 64),
    ("dango", 1945, T - 128), ("dango", 1960, T - 128), ("dango", 1975, T - 128),
    ("onigiri", 2080, T - 30),                       # 穴3の手前
    ("dango", 2225, T - 58), ("dango", 2245, T - 58),
    ("dango", 2330, T - 30), ("dango", 2360, T - 30),
    ("dango", 2440, T - 30), ("dango", 2470, T - 30),
    ("dango", 2572, T - 114), ("dango", 2598, T - 114),
    ("dango", 2725, T - 84), ("dango", 2755, T - 84),
    ("onigiri", 2870, T - 90),
    ("dango", 2985, T - 66), ("dango", 3015, T - 66),
    ("dango", 3092, T - 88), ("dango", 3118, T - 88),
    ("dango", 3220, T - 46), ("dango", 3250, T - 46), ("dango", 3280, T - 46),
    ("dango", 3455, T - 78), ("dango", 3485, T - 78),
    ("onigiri", 3585, T - 14),                       # ボスの場所の手前
)


class Terrain:
    FOOT = 6   # 足元の判定の、中心から左右への幅（端に少しかかっていれば立てる）

    def __init__(self, ground=GROUND, platforms=PLATFORMS):
        self.ground = [tuple(g) for g in ground]
        self.platforms = [tuple(p) for p in platforms]

    def height_at(self, x):
        """x にある地面の上面の高さ（一番高いもの）。地面がなければ None"""
        tops = [top for a, b, top in self.ground if a <= x < b]
        return min(tops) if tops else None

    def ground_at(self, x0, x1):
        """x0〜x1 に、地面が少しでもあるか"""
        return any(a < x1 and x0 < b for a, b, _ in self.ground)

    def support(self, px, prev_bottom, new_bottom):
        """下向きに動く足元が、このフレームで踏む面。(高さ, 地面か) の、一番高いもの。なければ None
        地面も足場も、上から降りてくるときだけ乗れる（下や横からは、通り抜ける・壁になる）"""
        x0, x1 = px - self.FOOT, px + self.FOOT
        best = None
        for a, b, top in self.ground:
            if a < x1 and x0 < b and prev_bottom <= top + 1 and new_bottom >= top:
                if best is None or top < best[0]:
                    best = (top, True)
        for a, b, top in self.platforms:
            if a < x1 and x0 < b and prev_bottom <= top + 1 and new_bottom >= top:
                if best is None or top < best[0]:
                    best = (top, False)
        return best

    def push_x(self, old_px, new_px, py, half):
        """横に動いた体が、地面の横の面（壁）にめり込んだら、押し戻した位置を返す。
        足元が、区間の上面より下にあるときだけ、その区間は壁になる（上を越えれば、壁ではない）。
        壁の中に入り込んでいたら、外へ押し出す"""
        px = new_px
        for a, b, top in self.ground:
            if top >= py - 0.5:
                continue
            if px - half < b and a < px + half:
                if old_px + half <= a + 0.01:
                    px = a - half
                elif old_px - half >= b - 0.01:
                    px = b + half
                else:
                    # すでに壁に入り込んでいる（角をかすめて落ちると、足は乗れないのに、体の端だけ区間に重なる）。
                    # そのままだと壁をすり抜けて、地面の下へ落ちるので、近い側へ押し出す
                    px = a - half if px < (a + b) / 2 else b + half
        return px

    def safe_spot(self, px, y, margin=24):
        """(px, y) が、区間の端から margin 以上離れた地面の上なら True（穴に落ちたときに戻る場所の候補）"""
        return any(a + margin <= px <= b - margin and abs(top - y) < 1 for a, b, top in self.ground)


# 中間地点（鳥居）: (x, 足元の高さ)。ここを通ると、やられたとき、ここから再開する
CHECKPOINT = (1230, T - 16)


# 敵の配置（種類, x）。序盤は落ち武者だけ→中盤に狐火→後半に烏→終盤は混ぜる
SPAWNS1 = (
    ("ochimusha", 520), ("ochimusha", 900),
    ("kitsunebi_low", 1250), ("kitsunebi_high", 1420), ("ochimusha", 1455),
    ("karasu", 1850), ("karasu", 2000),
    ("ochimusha", 2100), ("kitsunebi_high", 2200), ("karasu", 2300),
    ("ochimusha", 2460), ("karasu", 2620),
    ("ochimusha", 2880), ("kitsunebi_high", 3000), ("karasu", 3120),
    ("ochimusha", 3260), ("kitsunebi_low", 3400), ("ochimusha", 3480), ("karasu", 3540),
    # 月見坂は、敵が多い（参道の戦い）。坂を登るほど、押し寄せてくる
    ("ochimusha", 1010), ("karasu", 2420), ("kitsunebi_low", 2500), ("ochimusha", 2800), ("ochimusha", 3250),
)


class StageDef:
    """1つの面のデータ。地形・アイテム・敵・ボス・背景・曲を、1つにまとめる。
    絵は assets/images 以下の相対パス。面ごとの絵が無ければ、1面の絵で代わりにする"""

    def __init__(self, name, width, ground, platforms, items, checkpoint, spawns, bgm, bgm_boss,
                 sky="bg_sky.png", mid="bg_mid.png", tiles="", boss_x=None,
                 boss_title=C.BOSS_TITLE, boss_name=C.BOSS_NAME, boss_pattern=C.BOSS_PATTERN,
                 talk_boss=C.TALK_BOSS, talk_tanuki=C.TALK_TANUKI, number=1, stele_x=150, boss_kind="boss"):
        self.name, self.width = name, width
        self.ground, self.platforms, self.items = ground, platforms, items
        self.checkpoint, self.spawns = checkpoint, spawns
        self.bgm, self.bgm_boss = bgm, bgm_boss
        self.sky, self.mid, self.tiles = sky, mid, tiles   # tiles は、タイルの入ったフォルダ（空なら、直下）
        self.boss_x = boss_x if boss_x is not None else width - 110   # ボスが降ってくる場所
        self.boss_title, self.boss_name, self.boss_pattern = boss_title, boss_name, boss_pattern
        self.talk_boss, self.talk_tanuki = talk_boss, talk_tanuki
        self.boss_kind = boss_kind   # boss=泰衡（落ち武者） / boss2=基衡
        self.number = number    # 第N面（面の名前・石碑の絵の番号）
        self.stele_x = stele_x  # 石碑を置く場所

    @property
    def arena_x0(self):
        """ボスの場所の左端（ここで画面が止まる）"""
        return self.width - C.BASE_W

    @property
    def end_boss_x(self):
        """倒したボスが、吹っ飛んで倒れる場所"""
        return self.boss_x

    @property
    def end_tanuki_x(self):
        """寸劇で、タヌキ侍が話すときに立つ場所"""
        return self.arena_x0 + C.BOSS_TRIGGER + 20

    @property
    def dango_total(self):
        return sum(1 for k, _, _ in self.items if k == "dango")

    def terrain(self):
        return Terrain(self.ground, self.platforms)


STAGE1 = StageDef("月見坂", C.STAGE_W, GROUND, PLATFORMS, ITEMS, CHECKPOINT, SPAWNS1, C.BGM_STAGE1, C.BGM_BOSS,
                  boss_x=C.BOSS_X, number=1, stele_x=140)

# ---------------------------------------------------------------- 2面（毛越寺）
# 浄土庭園。池（広い穴）を、飛び石（足場）で渡る。反橋（太鼓橋）の階段、庭の塔（石灯籠の高台）、石橋
GROUND2 = (
    (0, 420, T),
    (420, 520, T - 16),
    (520, 700, T),
    # 池1: 700〜860（幅160）。飛び石で渡る
    (860, 1060, T - 16),
    (1060, 1180, T),
    (1180, 1240, T - 16),      # 反橋（登って、降りる）
    (1240, 1300, T - 32),
    (1300, 1360, T - 48),
    (1360, 1420, T - 32),
    (1420, 1480, T - 16),
    (1480, 1760, T),
    # 池2: 1760〜1900（幅140）。飛び石で渡る
    (1900, 2100, T - 16),
    (2100, 2240, T - 32),      # 中間地点
    (2240, 2380, T - 32),
    (2380, 2520, T),           # 谷。庭の塔の足もと
    (2520, 2600, T - 140),     # 庭の塔
    (2600, 2700, T - 32),      # 塔から、飛び降りる先
    (2700, 2900, T - 16),
    (2900, 3100, T),
    # 池3: 3100〜3290（幅190）。長い飛び石
    (3290, 3500, T - 16),
    (3500, 3560, T - 32),      # 2つ目の反橋（高い）
    (3560, 3620, T - 48),
    (3620, 3700, T - 64),
    (3700, 3760, T - 48),
    (3760, 3820, T - 32),
    (3820, 3880, T - 16),
    (3880, 4200, T),
    # 池4: 4200〜4330（幅130）。ボスの前の飛び石
    (4330, 5120, T),           # ボスの場所（面の端の先は、クリアのときに走り抜ける分）
)
PLATFORMS2 = (
    (560, 600, T - 70),
    (725, 760, T - 40), (785, 820, T - 52),                    # 池1の飛び石
    (1500, 1540, T - 74), (1560, 1600, T - 98),                # 上の道
    (1785, 1820, T - 42), (1835, 1870, T - 52),                # 池2の飛び石
    (1960, 2000, T - 60),
    (2400, 2440, T - 56), (2450, 2490, T - 108),               # 庭の塔を登る足場
    (2620, 2660, T - 90), (2800, 2860, T - 72),
    (3115, 3150, T - 40), (3170, 3205, T - 52), (3225, 3260, T - 40),   # 池3の飛び石（長い）
    (3330, 3370, T - 60), (3400, 3440, T - 84),
    (3980, 4040, T - 70), (4100, 4140, T - 96),
    (4222, 4255, T - 44), (4278, 4311, T - 44),                # 池4の飛び石
)
ITEMS2 = (
    ("dango", 150, T - 14), ("dango", 180, T - 14), ("dango", 210, T - 14),
    ("dango", 580, T - 88), ("onigiri", 660, T - 14),
    ("dango", 742, T - 58), ("dango", 802, T - 70),
    ("dango", 940, T - 32), ("dango", 970, T - 32),
    ("dango", 1270, T - 50), ("dango", 1330, T - 66),
    ("dango", 1520, T - 92), ("onigiri", 1580, T - 116),
    ("dango", 1802, T - 60), ("dango", 1852, T - 70),
    ("dango", 1980, T - 78),
    ("onigiri", 2180, T - 50),
    ("dango", 2420, T - 74), ("dango", 2470, T - 126),
    ("dango", 2535, T - 158), ("leaf", 2560, T - 160), ("dango", 2585, T - 158),
    ("dango", 2640, T - 108), ("dango", 2830, T - 90),
    ("dango", 3132, T - 58), ("dango", 3187, T - 70), ("dango", 3242, T - 58),
    ("dango", 3350, T - 78), ("dango", 3420, T - 102),
    ("onigiri", 3590, T - 70),
    ("dango", 3660, T - 82),
    ("dango", 4010, T - 88), ("triple", 4120, T - 114),
    ("dango", 4238, T - 62), ("dango", 4295, T - 62),
    ("onigiri", 4400, T - 14),
)
SPAWNS2 = (   # 毛越寺は、敵が少なめ。池と飛び石（ジャンプ）が主役。飛ぶ敵が中心
    ("ochimusha", 600), ("kitsunebi_low", 1000),
    ("karasu", 1600), ("kitsunebi_high", 1800), ("karasu", 2000),
    ("ochimusha", 2440), ("kitsunebi_high", 2650), ("karasu", 2950),
    ("kitsunebi_low", 3420), ("karasu", 3650),
    ("ochimusha", 3950), ("kitsunebi_high", 4150), ("karasu", 4400),
)
STAGE2 = StageDef("毛越寺", 5000, GROUND2, PLATFORMS2, ITEMS2, (2170, T - 32), SPAWNS2, C.BGM_STAGE1, C.BGM_BOSS,
                  sky="stage2/bg_sky.png", mid="stage2/bg_mid.png", tiles="stage2/",
                  boss_title="enemies/boss2_title.png", boss_name="enemies/boss2_name.png",
                  talk_boss="talk_boss2.png", talk_tanuki="talk_tanuki2.png", number=2, stele_x=130,
                  boss_kind="boss2", boss_pattern=C.BOSS2_PATTERN)   # 絵が無いあいだは、1面の絵で代わりにする
STAGES = [STAGE1, STAGE2]   # 遊ぶ順番
