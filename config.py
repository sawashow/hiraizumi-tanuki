"""画面サイズ・色・物理定数・アニメの割り当て"""

TITLE = "平泉タヌキ侍"

# 内部解像度（16:9）。表示は SCALE 倍に拡大する
BASE_W, BASE_H = 480, 270
SCALE = 2
FPS = 60

STAGE_W = 4080   # 1面の長さ（最後の1画面ぶんが、ボスの場所）。遠景・中景は、この長さに合わせて、カメラの動きに比例して流れる
GROUND_Y = 222   # 地面の上端（タイルの上端）
# 穴の上に重ねる「もや」: 高さ h、step ドットごとの段、curve が大きいほど、上のほうが薄い（池のある面には、出さない）
PIT_HAZE = dict(h=72, step=4, curve=1.6, edge=8)   # edge: 穴の両端の外へ、薄くしながら、はみ出す幅（×2段）
FLOOR_Y = GROUND_Y + 4  # 足がつく高さ（地面の石の縁の中）

# 色
BLACK = (0, 0, 0)
WHITE = (252, 252, 252)
TEXT = (252, 252, 252)
ENEMY = (168, 0, 32)
HEART = (212, 36, 28)
HEART_EMPTY = (60, 40, 60)

# 物理
GRAVITY = 0.4
JUMP_SPEED = -7.8
JUMP_CUT = 0.5       # ジャンプボタンを早く離したとき、上向きの速さに掛ける倍率
JUMP_CUT_MIN = -3.0  # これより遅い上昇には掛けない
FALL_GRAVITY = 1.3   # 下降中は重力をこの倍率にして、ふわっとした感じを減らす
MAX_FALL = 9.5

# 慣性（1フレームあたり）。ここを変えると操作感が変わる
MAX_SPEED = 2.8      # 最高速
ACCEL = 0.15         # 地上で押したときの加速（最高速まで約19フレーム）
FRICTION = 0.19      # 地上で離した・攻撃中の減速（約15フレームで止まる）
TURN_DECEL = 0.6     # 地上で逆向きに押したときの減速（少しだけすべって切り返す。向きは、押した瞬間に変わる）
JUMP_START = 0.7     # 左右を押しながら跳んだとき、跳んだ瞬間に持つ横の速さ（最高速に掛ける）。立ったままからでも、すぐ斜めに跳ぶ
PLATFORM_DROP = 10  # 下＋ジャンプで浮き足場から降りたあと、浮き足場に乗らないフレーム数（同じ足場に、すぐ乗り直さない）
JUMP_BUFFER = 8      # ジャンプを、着地や振り終わりの少し前に押しても、覚えておいて、できるようになったらすぐ跳ぶフレーム数
COYOTE = 5           # 足場の縁から出てしまっても、このフレーム数までは跳べる
ATTACK_MOVE = 0.6    # 刀・手裏剣の動作中に、向いているほうを押し続けたときの速さ（最高速に掛ける）。止まらずに、動きにつながる
SWORD_COOLDOWN = 8   # 刀を振り終わってから、次の刀を振れるまでのフレーム数（連打で、強くなりすぎないように。手裏剣や移動は、すぐできる）
INPUT_BUFFER = 10    # 刀・手裏剣を、前の動作が終わる少し前に押しても、覚えておいて、終わったらすぐ出すフレーム数
AIR_ACCEL = 0.18     # 空中で押したときの加速（逆向きでも約0.4秒で反転する）
AIR_FRICTION = 0.02  # 空中で離したときの減速（勢いはほぼ保たれる）
WALK_MIN_SPEED = 0.15  # これ以上の速さなら歩きのコマにする

# 主人公
PLAYER_W, PLAYER_H = 16, 36          # 当たり判定（体だけ。しっぽと刀は見た目だけ）
FRAME_W, FRAME_H = 64, 48            # 絵の枠
HEAD_X = 35                          # 絵の中の頭の左右位置（右向きのとき）
CROUCH_H = 28                        # しゃがんでいる間の、当たり判定の高さ（ボスの高い光波の下に入る）
PLAYER_HP = 6
INVINCIBLE_FRAMES = 90
HURT_FRAMES = 24
KNOCKBACK = 3.0

# 絵のコマ番号（assets/images/player_XX.png）
IDLE = (0,)      # 立ち。2コマ目（1）は、刀が出たり消えたりして見えるので、使わない
WALK = (2, 3, 4, 5, 6, 7)
WALK_TICKS = 5
HURT = (12, 13)
CROUCH = (27,)   # しゃがみ。2コマ目（28）は、体が横にずれて見えるので、使わない
# しゃがんだままの刀・手裏剣。コマの長さは、立っているとき（SWORD_SEQ・THROW_SEQ）と同じにする（判定や発射は、そちらで決めている）
CROUCH_SWORD_SEQ = ((29, 5), (30, 4), (31, 7), (32, 8))
CROUCH_THROW_SEQ = ((33, 4), (34, 4), (35, 4), (36, 8))
# やられて倒れる動き: (絵, 表示するフレーム数)。最後は、倒れたまま
DEFEAT_SEQ = ((13, 14), (24, 16), (25, 16))
DEFEAT_END = 26
JUMP_TAKEOFF, JUMP_RISE, JUMP_TOP, JUMP_FALL, JUMP_LAND = 14, 15, 16, 17, 18

# 刀: (コマ番号, 表示フレーム数)。判定が出るのは SWORD_ACTIVE 番目のコマだけ
SWORD_SEQ = ((8, 5), (9, 4), (10, 7), (11, 8))
SWORD_ACTIVE = 2
SWORD_W, SWORD_H = 30, 30
SWORD_TRAIL = 16     # 刀を振った勢いの軌跡（三日月の光）。刀の先に出て、そのぶん、届く距離が伸びる（光波のようには飛ばない）

# 手裏剣を投げる動作。THROW_RELEASE 番目のコマに入ったとき発射する
THROW_SEQ = ((19, 4), (20, 4), (21, 4), (22, 8))
THROW_RELEASE = 2
SHURIKEN_SPEED = 4.5
SHURIKEN_W, SHURIKEN_H = 12, 8
SHURIKEN_RANGE = BASE_W  # 手裏剣が飛ぶ距離の上限。実際は、画面の端まで飛んで、画面の外に出たら消える（main.py）。
                         # 前は 170（画面の3分の1）。団子の数だけしか投げられなくなったので、射程は、画面いっぱいにした（2026-10-12）
SHURIKEN_TICKS = 3   # 回転1コマの長さ
HIT_TICKS = 4        # 命中の破片1コマの長さ

# 攻撃のダメージ。刀は強く、手裏剣は弱い（そのかわり離れて撃てる）
SWORD_DAMAGE = 2
SHURIKEN_DAMAGE = 1

# 敵（ザコ）3種類。大きさ・体力・速さ・動きを変えて、見た目も攻略も区別する
HIT_FLASH = 6    # 攻撃を受けたとき白く光るフレーム数
HIT_STUN = 8     # 攻撃を受けたとき動きが止まるフレーム数

# 落ち武者（地上の歩兵）: 大きく、遅く、体力が多い。近づくと一度止まって構える
OCHI = dict(w=20, h=40, hp=2, touch=1, speed=0.6, active=240, ready_dist=110, ready_frames=30, swing_frames=26, wave_at=6, cooldown=120, turn_frames=150, patrol=40)
# ミイラ（亡者）: ゆっくり歩いて近づくだけ。攻撃はしない（触れると、ダメージ）。体力1。最初に出会う、いちばん弱い敵。
# 動きは、落ち武者と同じ仕組み（ready_dist=0 で、構えない）
MIIRA = dict(w=18, h=40, hp=1, touch=1, speed=0.4, active=260, ready_dist=0, ready_frames=1, swing_frames=1, wave_at=0, cooldown=0,
             turn_frames=120, patrol=30)
# 天狗（高館）: 地面を、ぴょんぴょん跳んで近づく。跳ぶ前に、かがむ（予告）。着地の隙は、狙い目。触れるとダメージ。体力2
#   crouch: かがむフレーム数 / rest: 着地してから、次にかがむまで
#   hop_vy: 跳ぶ上向きの速さ（頂点が、主人公の頭より高くなる = 下を、くぐれる）/ over: 主人公を飛び越えて、うしろに降りる距離 /
#   hop_max: 1回で跳べる横の距離の上限（遠いときは、この距離ずつ近づく） / step_up・step_down: 降りられる地面の、高さの差（穴や崖は、越えて跳ぶ）
TENGU = dict(w=20, h=40, hp=2, touch=1, active=260, crouch=22, rest=34, hop_vy=6.8, over=44, hop_max=130, step_up=50, step_down=100)
# 狐火（浮遊する炎）: 小さく、空中を上下に揺れながら横に進む。高さは低め・高めの2通り
KITSUNEBI = dict(w=14, h=14, hp=1, touch=1, speed=0.9, active=380, bob=12, period=90,
                 low=FLOOR_Y - 36, high=FLOOR_Y - 92)
# 烏（カラス）: 横長で速い。近づくと羽ばたいて予告し、そのときの主人公の位置へ急降下する
#   drop: 急降下で降りる深さ（待っている高さ → 地面に立つ主人公の胸のあたり）。主人公の高さに関係なく、いつも同じ
#   min_dx: 急降下の、横の進みの下限（真下にいても、これより急な角度では落ちない）
KARASU = dict(w=22, h=12, hp=1, touch=1, speed=3.5, active=240, telegraph=30, height=FLOOR_Y - 110, drop=92, min_dx=70)

# 討伐難易度（仮。1〜10）: 体力・予告の短さ・攻撃のよけにくさ・倒す手間から、見積もる。遊んで直す。
# 面の難易度（敵の密度＝敵の難易度の合計 ÷ 面の長さ(1000px)）を測るのに使う。tools/difficulty.py で、面ごとに表にする。
# 配置表の種類名（kitsunebi_low など）は、「_」より前で引く。まだ無い敵も、先に決めておく（assets/敵コンセプト.md）
ENEMY_DIFFICULTY = {
    "miira": 1,                                         # ミイラ（歩いてくるだけ）
    "kitsunebi": 2, "karakasa": 2, "kocho": 2,          # 狐火・唐傘小僧・金の蝶
    "karasu": 3, "koi": 3, "natsukusa": 3,              # 烏・鯉の怨霊・夏草の亡者
    "tachiojo": 4, "oboro": 4,                          # 立ち往生・朧
    "ochimusha": 5, "yumihei": 5, "tengu": 4,           # 落ち武者・弓兵・天狗
}
BOSS_DIFFICULTY = {"boss": 6, "boss2": 7, "boss3": 8, "boss4": 9, "benkei": 5}   # 泰衡・基衡・秀衡・清衡・弁慶（中ボス）
# 面の出来を測るときの物差し（tools/difficulty.py）。面を区画（stage.py の zones。無ければ window ごと）に分けて、単調な所を見つける
#   level: 区画の強さ（敵の難易度の合計＋穴×hole_cost。500px あたりに直す）を、1〜5 の段に分ける境目
#   same_run: 同じ敵が、これ以上続いたら注意 / flat: 平らな道が、これより長く続いたら注意（px）
#   empty: 敵も穴も物も無い区間が、これより長ければ注意（px） / combo: 違う種類の敵と一緒に出る敵の割合が、これより低ければ注意
#   near: 「一緒に出る」とみなす距離（px。画面の半分）
#   spacing: 敵の間隔のばらつき（標準偏差÷平均）が、これより小さければ注意（等間隔に並べただけ）
#   group / grouped: group 以内に、ほかの敵がいる敵の割合が、grouped より低ければ注意（1体ずつ順番に出るだけ）
#   crowd: 1画面に入る敵が、いちばん多い所でも、これより少なければ注意（見せ場が無い）
#   jump: 穴を越える1回のジャンプの難しさ。必要な距離 ÷ 届く距離（全速で跳んだとき）が、この境目を超えるごとに、1 → 2 → 3 → 4
#   narrow: 着地する足場の幅が、これより狭ければ、＋1 / edge: 穴のふちから、この距離より近い敵は、＋1（跳ぶのを邪魔する）
MAP_CHECK = dict(window=500, level=(3, 7, 11, 16), jump=(0.45, 0.65, 0.8), narrow=45, edge=100, same_run=4, flat=600, empty=320, combo=0.35, near=240,
                 spacing=0.6, group=110, grouped=0.4, crowd=5, gimmick=4)     # gimmick: 仕掛け（山おろし・光の柱）の強さ（500px あたり）
# 面の仕掛け: 山おろし（風）は、主人公が near より近くにいる間だけ吹く。光の柱の廊下は、stagger フレームずつ遅れて、左から順に落ちる
WIND = dict(near=300)
TRAP = dict(near=320, stagger=22)
ZONE_ROLES = ("教える", "試す", "組み合わせ", "渡る", "休む", "見せ場")     # 区画の役目（渡る = 敵は少なく、跳んで進むのが主役）
# 面ごとの目標（面の番号 → 敵の密度, ボスの難易度）。許す幅は、密度の ±DENSITY_TOLERANCE
STAGE_TARGET = {1: (8, 6), 2: (14, 7), 3: (20, 8), 4: (10, 9)}
DENSITY_TOLERANCE = 0.25

# 敵の絵（assets/images/enemies/種類_動き_番号.png）。コマ数と、枠の中の基準位置（変換ツールが表示する値）
ENEMY_FRAMES = {
    "ochimusha": {"walk": 4, "stance": 3, "swing": 2, "death": 3},
    "miira": {"walk": 4, "death": 3},
    "tengu": {"walk": 4, "death": 3},                    # 天狗（tools/make_tengu.py）。walk の 0 = 待つ / 1 = 空中 / 2 = かがむ / 3 = 着地（いまは使わない）
    "kitsunebi": {"flicker": 4, "death": 4},
    "karasu": {"flap": 4, "dive": 2, "death": 2},
    # 泰衡（tools/make_boss1.py）: 歩く・立ち・高い構え・振る・かがむ・跳ぶ・やられ（のけぞる・倒れる）
    "boss": {"walk": 4, "stance": 3, "high": 2, "swing": 2, "crouch": 2, "leap": 2, "death": 3},
    "yumihei": {"idle": 2, "draw": 3, "shoot": 2, "death": 3},   # 弓兵（tools/make_poses.py）
    "tachiojo": {"stand": 2},                                    # 立ち往生（動かない。倒せない）
    "boss3": {"walk": 4, "stance": 3, "low": 2, "high": 2, "swing": 2, "crouch": 2, "leap": 2, "death": 3},   # 秀衡（tools/make_boss3.py）。low = 低い構え
    "boss4": {"idle": 1, "pray": 2, "cast": 2, "spread": 2, "hold": 1, "roar": 2, "death": 3},   # 清衡: 浮いて座る・数珠を飛ばす・光になって消える（tools/make_boss4.py）
}
# w,h = 枠の大きさ / ax = 枠の中の、体の中心の左右位置 / ay = 足元（bottom）か中心（center）の上下位置
# 絵がまだ無い敵の、代わりの絵: 種類 → (借りる種類, 塗り替える色)。assets/images/enemies/種類_*.png を置けば、そちらを使う
ENEMY_STANDIN = {}      # 例: {"種類": ("ochimusha", (236, 222, 180))}。ミイラは、2026-10-12 に、絵ができた
ENEMY_ART = {
    "ochimusha": dict(w=62, h=51, ax=31, ay=51, mode="bottom"),
    "miira": dict(w=47, h=42, ax=23, ay=42, mode="bottom"),      # ミイラ（tools/make_miira.py）
    "tengu": dict(w=43, h=46, ax=22, ay=46, mode="bottom"),      # 天狗（tools/make_tengu.py）
    "kitsunebi": dict(w=16, h=18, ax=8, ay=9, mode="center"),
    "karasu": dict(w=42, h=25, ax=21, ay=12, mode="center"),
    "yumihei": dict(w=49, h=48, ax=24, ay=48, mode="bottom"),
    "tachiojo": dict(w=42, h=88, ax=16, ay=88, mode="bottom"),   # いつも左向き（絵を反転して出す）。体の中心は、薙刀のぶん、枠の左寄り
    "boss3": dict(w=116, h=115, ax=58, ay=114, mode="bottom"),   # 秀衡（枠の下端の1ドットは、縁取り）
    "boss4": dict(w=112, h=89, ax=60, ay=89, mode="bottom"),    # 清衡（蓮の台座の下端が、枠の下端。横は、台座の中心）
    "boss": dict(w=144, h=107, ax=72, ay=107, mode="bottom"),   # 泰衡（足元が、枠の下端）
    "boss2": dict(w=120, h=77, ax=60, ay=77, mode="bottom"),    # 基衡: 霧の下端が、地面より3ドット下に来る
}
# 基衡のコマ（assets/images/enemies/boss2_名前.png。左向き。tools/make_boss2.py が作る）
BOSS2_FRAMES = ("idle_0", "idle_1", "idle_2", "walk_0", "walk_1", "fan_up", "fan_swing", "throw_0", "throw_1",
                "petal", "hurt", "down", "vanish", "fan")

# 落ち武者の光波（刀を振ると、前方の地面すれすれを飛ぶ。ジャンプでよけるか、刀で消せる。手裏剣は通り抜ける）
WAVE_FRAMES = 3
# 立ち往生（弁慶の亡霊）: 動かない。倒せない。ダメージも与えない。敵の矢や光波を弾く「矢よけ」（うしろに隠れられる）。
#   触れると、手前へ押し戻される。刀・手裏剣は、白く光って弾かれる。
#   飛び越えて進む。当たり判定（h）は、見た目（体の高さ 約60）より低くして、地面からのジャンプ（高さ72）で、余裕をもって越えられるようにする
TACHIOJO = dict(w=24, h=48, hp=2, touch=0, flash=10, breath=44, fade=26, drop="onigiri")
# 弓兵: 動かない。近づくと弓を引き（draw_frames が予告）、主人公をねらって、矢をまっすぐ撃つ。矢は、刀で斬って消せる（手裏剣は、通り抜ける）
#   active: 気づく距離（横）。reach_y: 気づく高さの差。bow_y: 矢が出る高さ（足元から）。max_angle: ねらえる角度（水平から、上下に）
YUMI = dict(w=18, h=40, hp=2, touch=1, active=300, reach_y=150, draw_frames=42, shoot_frames=24, cooldown=150, first_wait=30,
            bow_y=27, max_angle=38)
ARROW = dict(w=12, h=6, speed=2.5, range=360, damage=1, break_frames=18)
WAVE = dict(w=4, h=14, speed=1.1, range=140, damage=1, dy=-17, ticks=7)   # dy: 光波の中心の高さ（足元から。絵の下端が、地面に付く高さ）

# ボス（1面は、四代の藤原泰衡。見た目は、落ち武者）: 最後の1画面に入ると、上から降ってくる。画面はそこで止まり、倒すとクリア
# 動きは「歩く → 構えて光波」を2回、そのあと「かがんで跳びかかり」の繰り返し（1面のボスなので、攻撃は1つずつ）。
# 光波は、低い（跳んでよける）と、高い（しゃがんでよける）を打ち分ける。大きさは同じで、飛ぶ高さが違う。構えも違うので、見て判断する。
# 主人公が壁ぎわにいるときは、跳びかかりを選ぶ（下をくぐって、反対側へ逃げられる）。
# 攻撃のあとに隙がある。体力が半分になると、歩く時間と隙が短くなる
BOSS = dict(w=36, h=76, hp=24, touch=1, speed=0.5, near=70, gravity=0.3,
            walk_frames=80, ready_frames=40, swing_frames=30, wave_at=8, recover_frames=70,
            crouch_frames=34, leap_frames=56, wave_speed=1.8, wave_range=420,
            rage_walk_frames=50, rage_recover_frames=45,
            high_bottom=30, high_h=32, corner=70)   # 高い光波の下端と高さ（地面から。高さは、絵と同じ） / 壁ぎわとみなす距離
# ボスの名前（藤原四代。1面は、四代の泰衡。設定は assets/ストーリー設定.md）。出てきたときに、
# まず二つ名（「呪落武者」）が出て、少し遅れて、名前が出る。どちらも、上に小さく、ふりがなを付ける。
# 文字の絵は tools/make_boss_name.py で作る（名前を変えるときは、絵を作り直す）
BOSS_TITLE = "enemies/boss_ochimusha_title.png"   # 二つ名（上に、ふりがな）
BOSS_NAME = "enemies/boss_ochimusha_name.png"     # 名前（上に、ふりがな）
BOSS_TITLE_Y = 28               # 二つ名（ふりがな）の上端
BOSS_NAME_Y = 84                # 名前（ふりがな）の上端
BOSS_NAME_DELAY = 50            # 二つ名が出てから、名前が出るまでのフレーム数
# ボスが出てくる場面（この間、主人公は動かせない）: 静かになる → 降ってくる → 着地（画面が揺れる。ここで曲が始まる）
# → かがんだまま止まる → 立って名前が出る → 戦いが始まる。やられて入り直したときは、短くする
BOSS_INTRO = dict(wait=70, land=50, pose=220, shake=22, bar=26, bar_frames=40, name_fade=36)
BOSS_INTRO_QUICK = dict(wait=20, land=24, pose=60)   # 短いときは、二つ名と名前を一度に出す
LEAP_SHAKE = 8                  # 跳びかかりの着地で、画面が揺れるフレーム数
BOSS_PATTERN = "LHHLHLLH"       # 光波の順番（L=低い / H=高い）。くり返す
BOSS_X = STAGE_W - 110          # ボスが降ってくる場所
ARENA_X0 = STAGE_W - BASE_W     # ボスの場所の左端（ここで画面が止まる）
SCORE_BOSS = 2000
CLEAR_SCORE_AT = 40             # クリアしてから、SCORE の行が出て、数字が増え始めるまでのフレーム数
CLEAR_COUNT = 60                # SCORE が 0 から最終値まで増える長さ（点数の大きさによらず同じ）
CLEAR_WAIT = CLEAR_SCORE_AT + CLEAR_COUNT + 60   # クリアしてから、Enter を受け付けるまでのフレーム数（FOOD・TIME が出たあと）
# ボスを倒したあとの寸劇: ボスが決まった場所へ吹っ飛ぶ → タヌキ侍が決まった場所へ歩く → 間 → 倒れたボスがひとこと → 光になって消える → タヌキ侍が返す → 右へ駆け抜ける → 結果
#   skip: せりふを、キーで送れるようになるまでのフレーム数（字が出ている途中なら、まず全部出す）。type: 字を1文字出すフレーム数。exit: 画面の外へ、どこまで走るか
ENDING = dict(wait=30, boss=270, fade=70, reply=280, skip=20, type=8, exit=40)
BOSS_TRIGGER = 110              # ボスの場所の左端から、ここまで入ると、ボスが出る（画面は、そこから右端まで流れて止まる）
SHADOW_MULT = (96, 100, 150)    # 影のボス: 色に掛ける値（暗く、青く）
SHADOW_ADD = (6, 8, 26)         # 影のボス: 足す値（真っ黒につぶれないように）
SHADOW_MIN_HP = 8               # 影のボスの体力の下限
SCORE_SHADOW = SCORE_BOSS // 2  # 影を倒したときの点
BOSS_CAM_SPEED = 3              # そのときに、画面が流れる速さ
END_BOSS_X = BOSS_X             # 倒したボスが、吹っ飛んで倒れる場所（降ってきた場所と同じ）
END_TANUKI_X = ARENA_X0 + BOSS_TRIGGER + 20   # タヌキ侍が、話すときに立つ場所（ボスが出てきたときに、立っていたあたり）
END_BLOW = dict(vy=-5.0, frames=40, rest=24, limit=600)   # 吹っ飛び: 上向きの速さ、横に動く時間、倒れてからの間。limit: 場所に着けないときの打ち切り
STARTLE = 44                    # ボスが降ってきたとき、タヌキ侍が驚いて跳ねるフレーム数
TALK_BOSS = "talk_boss1.png"        # ボスのせりふ（吹き出しの中の字）
TALK_TANUKI = "talk_tanuki1.png"    # タヌキ侍のせりふ
TALK_CELL = 24                  # せりふの絵の、1文字のますの幅（tools/make_talk_text.py と合わせる）
# 考えごとの吹き出し（返事の代わりに、食べ物を思い浮かべる面。stage.py の thought）。数は、せりふの「文字」と同じ刻み（ENDING の type フレーム）で数える
#   grow: 丸が出て、雲がふくらみきるまで / per: 食べ物が1つ浮かぶごとの間
#   lift: 頭のてっぺんから、雲の下端までのすき間（雲が、頭や兜に重ならないように）/ head: 姫を助ける場面での、足元から頭のてっぺんまでの高さ
THOUGHT = dict(grow=10, per=8, lift=12, head=44, hold=70)
# タヌキ侍の、頭の中の食べ物（いつも腹ペコ）。夢の吹き出し（語りの眠り・姫を助けたあと）では、これを順に浮かべる。assets/images/items/food_*.png（tools/make_foods.py）。絵が無い物は、飛ばす
FOODS = ("onigiri", "dango", "wanko", "reimen", "jajamen", "mochi", "senbei", "kushi", "hittsumi", "anko")
FOOD_SWAP = 40      # 夢の吹き出しで、食べ物が替わるフレーム数
TALK_PAUSE = {"reply": (3, 90)}   # せりふの途中の間: (何文字目のあとで, 何フレーム止まるか)。「・・・」のあと、間をおいて「姫？」
TALK_BOSS_Y = 40                # ボスの吹き出しの、しっぽの先（足元からの高さ）

# アイテム。団子=スコア / おにぎり=回復 / 金の葉=強化（刀を振ると光波が出る。ダメージを受けると消える）
ITEM_SIZE = 16
SCORE_DANGO = 100
SCORE_FULL_HP = 50      # 体力が満タンでおにぎりを取ったときのスコア
HEAL_ONIGIRI = 2
# 強化は3種類。金の葉・三方手裏剣は、ダメージを受けると消える（両方、同時に持てる）。スーパータヌキは、時間で切れる
#   leaf   = 金の葉: 刀を振ると、光波が出る
#   triple = 三方手裏剣: 手裏剣が、前・斜め上・斜め下の3方向に出る
#   super  = スーパータヌキ: しばらくの間、速くなって、敵や光波に当たってもダメージを受けない（穴には落ちる）
TRIPLE_VY = (-1.6, 0.0, 1.6)    # 三方手裏剣の、上下の速さ
SUPER_FRAMES = 480              # スーパータヌキの長さ（8秒）
SUPER_SPEED = 1.5               # 速さの倍率（最高速と、加速）
SUPER_WARN = 90                 # 残りがこのフレーム数になったら、光り方が変わる（もうすぐ切れる合図）
# 敵を倒したとき、落とす物と、その確率（残りは、何も落とさない）。ボスは落とさない
# 石灯籠（道ばたにあり、刀・手裏剣・光波で壊すと、中の物が出る）。絵は tools/make_enemy.py で作る（元絵は prop_toro.jpg）
#   w, h: 当たり判定。flicker: 火のゆらぎの1コマの長さ。break_ticks: 壊れる動きの1コマの長さ。ax: 絵の枠の、足元の中心（左から）
TORO = dict(w=22, h=34, flicker=9, break_ticks=5, ax=21, shard_vx=1.6, shard_vy=-3.4, shard_life=34)
DROPS = (("onigiri", 0.12), ("leaf", 0.07), ("triple", 0.07), ("dango", 0.18))
# 手裏剣は、数に限りがある（悪魔城ドラキュラのサブウェポンと同じ扱い）。数は「団子」で持つ。刀は、いくらでも振れる
#   max: 持てる数。start: 面の始まり・やられて再開したときの数。dango: 団子1つで増える数。cost: 1投げで減る数（三方手裏剣も、1投げで1）
#   empty: 団子が無いのに投げようとしたとき、団子のゲージを赤く点滅させるフレーム数
AMMO = dict(max=12, start=6, dango=1, cost=1, empty=24)
DROP_LIFE = 540                 # 落とし物が消えるまでのフレーム数（最後の2秒は点滅）
DROP_HOP = -2.6                 # 落とし物が出たときの、上向きの速さ（少し跳ねて、地面に落ちる）
DROP_GRAVITY = 0.22
SLASH = dict(w=8, h=26, speed=3.0, range=220, damage=1, ticks=5)   # 強化中の、刀の光波
SLASH_FRAMES = 3

# 音
BGM_STAGE1 = "bgm_stage1.ogg"  # 1面の曲。曲名は「Clash of the Iron Fan」
BGM_STORY = "bgm_story.ogg"    # 始まりの語りの間（おとなしい曲）。曲名は「Evening at the Border Post」。ファイルが無ければ、無音
BGM_BOSS = "bgm_boss.ogg"      # ボスと戦っている間。曲名は「Crimson Temple Breach」（くり返せるように、終わりの締めを切ってある）
BGM_SUPER = "bgm_super.ogg"    # スーパータヌキの間（勢いのある曲）。曲名は「Seven Blades High」。ファイルが無ければ、面の曲のまま
# 場面ごとの曲（ファイルを assets/audio に置けば、鳴る。無ければ、右に書いた、いまの曲で代わりにする）
BGM_MAP = "bgm_map.ogg"            # ステージ選択の地図。曲名は「Steps Into the Morning Sun」（前後の無音を切ってある。無ければ、語りの曲）
BGM_TITLE = "bgm_title.ogg"        # スタート画面（無ければ、無音。雷の音だけ）
BGM_ENDING = "bgm_ending.ogg"      # エンディング（無ければ、語りの曲）
BGM_STAGE_N = "bgm_stage%d.ogg"    # 面ごとの曲（%d は、遊ぶ順の番号 1〜4。無ければ、その面に決めてある曲 = 1面の曲）
BGM_BOSS_N = "bgm_boss%d.ogg"      # 面ごとの、ボスの曲（無ければ、ボスの曲）
BGM_MIDBOSS = "bgm_midboss.ogg"    # 面の途中の相手（弁慶・影のボス。無ければ、ボスの曲）
BGM_VOLUME = 0.5
BGM_VOLUMES = {BGM_STORY: 0.4}   # 曲ごとの音量（書いていない曲は BGM_VOLUME）。語りの曲は、少し小さく
SFX_THUNDER = "sfx_thunder.ogg"   # 雷鳴（スタート画面）
SFX_SWORD = "sfx_sword.ogg"       # 刀を抜く「ジャキン」（スタート画面で決定したとき）
SFX_CHECKPOINT = "sfx_checkpoint.ogg"   # 中間地点を通ったときの音（琴のような音階に、鈴の余韻）
SFX_TALK_LOW = "sfx_talk_low.ogg"     # せりふの字が出るときの「ピッ」（ボス。低い）
SFX_TALK_HIGH = "sfx_talk_high.ogg"   # 同じ（タヌキ侍。高い）
SFX_CLANG = "sfx_clang.ogg"           # 刀や手裏剣が、弾かれる音（立ち往生）
SFX_VOLUME = {SFX_CLANG: 0.2, SFX_THUNDER: 0.3, SFX_SWORD: 0.3, SFX_CHECKPOINT: 0.22, SFX_TALK_LOW: 0.07, SFX_TALK_HIGH: 0.07}   # 効果音の大きさ（抑えめ）。音は tools/make_sfx.py で作る
# 遊びの効果音（tools/make_sfx.py --game で作る）。名前 → 音の大きさ。ファイルは sfx_名前.ogg。
# よく鳴る音（跳ぶ・斬る・拾う）は小さく、大事な合図（予告・ボス）は、少し大きく
SFX_GAME = dict(
    jump=0.07, swing=0.14, throw=0.14, hit=0.2, hurt=0.26, dead=0.26, fall=0.22, empty=0.2, startle=0.2,     # 主人公
    dango=0.16, heal=0.22, power=0.22, **{"break": 0.22},                                                    # 拾う・壊す
    die=0.18, wave=0.16, cut=0.18, caw=0.16, dive=0.16, draw=0.14, arrow=0.18, snap=0.18,                    # ザコ敵
    thud=0.3, boss_wave=0.22, leap=0.2, boss_hit=0.22, boss_die=0.32, roar=0.3, thrust=0.22,                 # ボス
    fan=0.18, gust=0.2, petal=0.14, bead=0.16, ring=0.22, charge=0.2, pillar_warn=0.09, beam=0.12, warp=0.2, warp_in=0.2,
    select=0.14, cursor=0.16, decide=0.18, clear=0.26, gameover=0.26,                                                                  # 画面
)
SFX = {k: "sfx_%s.ogg" % k for k in SFX_GAME}
SFX_VOLUME.update({SFX[k]: v for k, v in SFX_GAME.items()})
BGM_FADE_MS = 1200      # やられたとき、曲が消えていくまでの時間

# スタート画面: 絵（assets/images/title.png、480×270）の上に、題名を重ねる。Enter（Z・Space でも）で始まる。
# クリアのあとは、ここへ戻る。題名は、絵の左の空（右は主人公と月）に置く。
# 題名の絵は tools/make_title_logo.py（昔のゲームのロゴ風）、「PUSH ENTER KEY」は tools/make_text_image.py で作る
# 絵が無いときは、1面の始まりの景色を暗くして、代わりにする
TITLE_BG = "title.png"
TITLE_DIM = 70          # 絵が無いとき、景色を暗くする度合い（0〜255）
TITLE_LOGO = (150, 14)    # 題名の、左右の中心と上端
TITLE_PROMPT = (150, 214)  # 「PUSH ENTER KEY」の、左右の中心と上端（これより上は、中央の人物の足に重なる。前は 232）
# 題名は、画面の上の外から、ゆっくり下りてきて止まる（最後に減速）。着いてから、案内が出る
TITLE_DROP_WAIT = 30    # 開いてから、下り始めるまでのフレーム数
TITLE_DROP = 120        # 下りるフレーム数
# 放っておくと、ときどき稲光が走り、少し遅れて雷鳴が鳴る（間隔は、この順のくり返し。フレーム数）
TITLE_THUNDER = (240, 600, 420, 780)
TITLE_FLASH = 26        # 稲光のフレーム数（2回光る）。空に稲妻が走り、画面も少しだけ明るくなる
# 稲妻: 走る場所（左右の範囲・上端・下端）。絵の、空が見えている所に合わせる（題名と月の間）
BOLT = dict(x0=256, x1=284, top=0, bottom=128, step=9, jitter=7,
            core=(255, 255, 255), glow=(150, 180, 255), sky=(200, 215, 255), sky_alpha=70)
THUNDER_DELAY = 22      # 稲光から雷鳴までのフレーム数
TITLE_START = 40        # 決定（刀の音）から、始まるまでのフレーム数。この間、案内が速く点滅する

# ステージ選択の地図（assets/images/stage_map.png、480×270）: ゲームの始まりと、面をクリアしたあとに出す。
# 駒（タヌキ侍）が、前の場所から次の場所へ、道を歩いて、「第N面 地名」を出す。Enter で飛ばせる（やり直しのときは出さない）
# 場所の番号は、面の番号（1 毛越寺・2 高館・3 月見坂・4 金色堂）。座標は、絵の上の、駒の足元
MAP_IMAGE = "stage_map.png"
MAP_PADS = {1: (178, 234), 2: (343, 220), 3: (192, 146), 4: (107, 52)}
MAP_JUNCTION = (275, 198)    # 毛越寺・高館・月見坂の道が集まる分かれ道（地図に、道が描いてある）
# 隣り合う場所の間の道（途中の点）。遠い面へ飛ぶとき（高館がまだ無い間）は、間の道をつなげて歩く
MAP_ROUTE = {
    (1, 2): [(230, 212), MAP_JUNCTION, (310, 208)],
    (2, 3): [(310, 208), MAP_JUNCTION, (235, 172)],
    (3, 4): [(165, 110), (128, 70)],
}
MAP_WAIT = 45         # 地図を出してから、駒が歩き出すまでのフレーム数
MAP_WALK_SPEED = 1.2   # 駒が歩く速さ（1フレームに進むピクセル数）
MAP_HOLD = 150         # 着いてから、次へ進むまでのフレーム数（待たずに Enter で進める）
MAP_SKIP_WAIT = 20    # 出してから、Enter を受け付けるまで（押しっぱなしで飛ばさない）
MAP_DOT_GAP = 7       # 道の点線の、点の間隔（ピクセル）
MAP_VIGNETTE = 150    # 地図の四隅を暗くする強さ（0〜255）。中心は暗くしない
MAP_PIECE_SCALE = 0.5  # 駒の大きさ（主人公の絵に対する倍率）

# エンディング画面（assets/images/ending.png、480×270）: 最後の面をクリアして Enter を押すと、出る。夜明けの金色堂の前で、タヌキ侍が手を合わせる絵と、「交通安全」の文字。
# 暗い所から、ゆっくり明るくなる。しばらくして、Enter で、スタート画面へ戻る
ENDING_IMAGE = "ending.png"
ENDING_SCREEN = dict(fade=90, wait=240)
# 姫を助ける場面（最後の面の結果のあと、エンディングの絵の前）。昔のゲームの「THANK YOU ○○!」の画面。
# 暗い堂の中。タヌキ侍が左から歩いてきて、奥で待っていた姫の前で止まる。姫が跳ねて喜び、礼の文が、1文字ずつ出る。
#   walk: 歩く速さ / stop_x・hime_x: 二人が立つ場所 / hop: 姫が跳ねるフレーム数（2回） / type: 1文字が出る間隔 / gap: 行と行の間 / wait: 文が出きってから、キーを受け付けるまで
STORY_BG = "story_bg.png"       # 始まりの語りの背景（夜の平泉。tools/make_story_bg.py）。無ければ、真っ暗
THANKS_BG = "thanks_bg.png"     # 姫を助ける場面の背景（夜明けの参道。地面ごと描いた1枚絵。tools/make_thanks_bg.py）。無ければ、真っ暗な背景に、タイルの床
THANKS = dict(walk=1.3, stop_x=178, hime_x=298, floor=238, hop=44, type=4, gap=26, wait=70,
              lines=("THANK YOU TANUKI!", "YOUR QUEST IS OVER."), text_y=(24, 52), sub_y=82,
              dream=40, dream_swap=45,     # dream: 文が出きってから、タヌキ侍の頭の上に、食べ物の吹き出しが出るまで / dream_swap: 食べ物（FOODS）が入れ替わる間隔
              cloud=(150, 72), cols=5, food_dx=28, food_dy=26, food_every=14,   # タヌキ侍の吹き出し: 大きさ / 食べ物を並べる列数・間隔 / 1つずつ浮かぶ間隔
              heart_after=30, heart_cloud=(36, 28))    # 姫の吹き出し（ハート）: タヌキ侍の吹き出しから、遅れて出るフレーム数 / 大きさ
# エンドロール（姫を助ける場面のあと、エンディングの絵の前）。平和になった、いまの平泉の道を、タヌキ侍と姫が、右へ歩いていく。
# 道は、手前と奥に歩道があって、間を車道が横に通っている。横断歩道に来ると、二人は止まる。車が通りすぎるのを待って、
# 右・左を見てから、向こうの歩道へ渡る。これを、くり返す。その間、画面の右半分を、エンドロールの文字が、下から上へ流れる。
#   x・hime_dx: タヌキ侍の立つ所と、姫が、そのうしろに付く距離 / far・near: 奥と手前の歩道の、足元の高さ / road: 車道の上端と下端
#   speed: 歩く速さ（景色が流れる速さ）/ every: 横断歩道の間隔 / zebra: 横断歩道の幅
#   car_wait: 止まってから、車が来るまで / car_speed: 車の速さ / look: 右・左を見る1回の長さ（3回見る）/ cross: 渡りきるまでのフレーム数
#   scroll: 文字が流れる速さ / window: 文字が見える範囲（上端, 下端）/ skip: 決定のキーで飛ばせるようになるまで / tail: 文字が流れきってから、絵に替わるまで
#   view_w: 左の、動きを見せる枠の幅。画面の左半分で、二人が歩き、右半分（暗い地）を、文字が流れる
ROLL = dict(view_w=240, x=140, hime_dx=-46, far=166, near=252, road=(176, 240), speed=0.9, every=330, zebra=38,
            car_wait=24, car_speed=3.4, look=26, cross=76, scroll=0.35, window=(0, 270), skip=90, tail=120,
            slot_h=118, boss_tick=14, edge=24)      # slot_h: 文字の絵（credits.png）の、ボスの絵の空き場所の高さ（tools/make_credits.py の SLOT_H と同じ）/ boss_tick: ボスの絵が、次のコマに替わるフレーム数 / edge: 左の枠の、右の端を暗くぼかす幅（ドット）
# 「しゅつえん」に出る、ボスの待機の絵（コマの順。1コマだけのときは、ゆっくり、1ドットずつ上下する）。文字の絵の空き場所（上から順）に、この順で重ねて描く。右半分の中央に、足元をそろえて置く
ROLL_BOSSES = (tuple("enemies/boss_stance_%d.png" % i for i in range(3)),                       # 四代 泰衡
               tuple("enemies/boss3_stance_%d.png" % i for i in range(3)),                      # 三代 秀衡
               tuple("enemies/boss2_idle_%d.png" % i for i in range(3)),                        # 二代 基衡
               ("enemies/boss4_pray_0.png",))      # 初代 清衡（座った像なので、1コマだけ。ゆっくり浮き沈みする。コマを替えると、うるさい）
ROLL_IMAGES = dict(bg="ending_bg.png", cars=("ending_car_0.png", "ending_car_1.png", "ending_car_2.png"), credits="credits.png",
                   hime_walk=tuple("hime_walk_%d.png" % i for i in range(6)),
                   road="roll_road.png", zebra="roll_zebra.png",     # 道（歩道・縁石・車道）の帯と、横断歩道（tools/make_roll_road_ai.py）。無ければ、四角の塗りで描く
                   tanuki_raise=tuple("roll_tanuki_raise_%d.png" % i for i in range(6)),    # 道を渡る間の、手を挙げて歩く絵（tools/make_roll_raise.py）。右向き
                   hime_raise=tuple("roll_hime_raise_%d.png" % i for i in range(6)))        # 姫。左向き。   # 無い絵は、図形や、いまの絵で代わりにする
HIME_IMAGES = ("hime_0.png", "hime_1.png")      # 姫の絵（立つ・跳ねる）。無ければ、タヌキ侍の絵を、桃色にして代わりにする
THANKS_SUB = "thanks_sub.png"                   # 英語の文の下に出す、日本語の一行（tools/make_text_image.py）   # 明るくなるまでのフレーム数 / Enter を受け付けるまで

# 始まりの語り: スタート画面で決定すると、暗い画面の上半分を、文章が下から上へゆっくり流れる（1回だけ）。
# 下には、タヌキ侍が立っている。しばらくすると、座って眠ってしまい、夢の中でおにぎりのことを考える。
# Enter（Z・Space でも）を押すと、はっと気づいて（眠っていたら、飛び起きて）、右へ素早く駆け抜けて、ゲームが始まる。
# 押すまでは始まらない（曲を、好きなだけ聴ける）。文章は assets/story_intro.txt に書き、tools/make_story_text.py で絵にする
STORY_SPEED = 0.3       # 流れる速さ（1フレームに進むドット数。1行が、約1.4秒で通る）
STORY_WINDOW = 166      # 文章が流れる範囲の高さ（画面の上から。その下に、タヌキ侍が立つ）
STORY_FADE = 40         # その範囲の上下で、文字が暗がりに消えていく幅
STORY_SKIP_WAIT = 20    # 始まってすぐは、キーを受け付けない（決定の連打で、飛ばしてしまわないように）
# タヌキ侍の絵は、語りの画面専用（assets/images/story/tanuki_00〜10.png）。大きさも、ドットの粗さも、ゲーム中の主人公と同じ。
#   0 立ち / 1 あくび / 2 うとうと / 3 座りこむ / 4・5 眠り（息）/ 6 眠り（鼻ちょうちん）/ 7 はっと起きる / 8 飛び上がる / 9 走り出す / 10 全力で走る
# x・ground = 立つ場所 / head_x・foot_y = 絵の中の、頭の左右位置と足元 / sleep_at = 眠るフレーム（その前に、あくび→うとうと→座る）
# dream_at = 夢を見始めるフレーム / notice・wake = 気づく・飛び起きるのにかかるフレーム / run_speed = 駆け抜ける速さ
STORY_TANUKI = dict(x=150, ground=236, head_x=56, foot_y=46, sleep_at=720, dream_at=960, notice=10, wake=34,
                    run_speed=5.0, run_ticks=4, yawn=70, drowsy=70, sit=30, breath=60)
STORY_SLEEP_SEQ = (4, 5, 4, 5, 4, 6)   # 眠っている間のコマの順番（1コマが breath フレーム）
# ゲーム中も、何も押さずに立っていると、あくびをして、座って眠る（「Z」が出る）。絵は、語りの画面と同じもの。
# キーを押すか、ダメージを受けると、すぐ起きる。眠っていても、当たり判定は立っているときと同じ
REST = dict(start=480, yawn=70, drowsy=70, sit=30, breath=60)   # start = 眠りに入るまでの、何もしない時間（8秒）
STORY_PROMPT = (350, 216)   # 「PUSH ENTER KEY」の、左右の中心と上端

# 面の名前の表示（面の始まりに、縦書きで出す）: 少し待って → 現れる → 見せる → 消える（フレーム数）
STAGE_TITLE = dict(wait=20, fade_in=25, hold=120, fade_out=35)
STELE_Y = 2           # 石碑を、地面に少し埋める（足元から）
LEDGE_SINK = 4        # 足場の絵（ledge_幅.png）を、足の高さより、上にずらす量（草の葉先のぶん）
STONE_PAD = 5         # 礎石の足場の絵を、足場の幅より、左右にはみ出させる分

# 池（水面の絵がある面）
WATER_DEPTH = 8       # 穴の上端から、水面までの深さ
WATER_TICKS = 30      # 水面が、もう1コマに切り替わるまでのフレーム数

# 起動したときの、会社のロゴ画面（splash.py）。fade: 現れる・消えるのフレーム数 / hold: 止まっているフレーム数 / width: 窓の幅に対するロゴの幅
# スマホのタッチ操作（touch.py）。大きさは、窓の高さに掛ける。
#   side＝左右の帯の幅（ゲームの絵は、残りに16:9で出す）／cuts＝右半分の帯の境目（上から: ポーズの隅の下端・手裏剣と刀・刀とジャンプ）
#   stick_dead＝歩き出す、指のずれ／stick_down＝しゃがむ、指の下へのずれ／stick_max＝スティックの中心が、指についてくる距離
#   coyote・jump_buffer＝タッチのときだけ、ジャンプを受け付ける時間を、長くする（COYOTE・JUMP_BUFFER の代わり）
#   ring＝指の所に出す輪の半径／ring_alpha・hint_alpha＝輪の濃さ（指を置いたとき・置いていないときの目印）／band_alpha＝押している帯の明るさ
#   arc＝右のボタンの、帯の真ん中からの横のずれ（帯の幅に掛ける。上から手裏剣・刀・ジャンプ。親指の弧に沿って、下ほど内側）／vibrate＝押したときの振動（ミリ秒。Android のみ）
TOUCH = dict(side=0.33, cuts=(0.18, 0.42, 0.64), stick_dead=0.03, stick_down=0.07, stick_max=0.04, ring=0.10, ring_alpha=150, hint_alpha=70, band_alpha=40, arc=(0.12, 0.0, -0.12), vibrate=12, coyote=8, jump_buffer=12,
             color=(110, 110, 130), lit=(255, 236, 150), mark=(200, 200, 215))
LOGO = dict(file="ponpoco_logo.png", bg=(255, 255, 255), fade=30, hold=120, after=50, width=0.35)   # after: ロゴが消えたあと、白いまま待つ（余韻）

# 残機・中間地点
LIVES = 3
# 難しさ（スタート画面で、左右で選ぶ。起動のときに easy・hard と書いても選べる）。面の形は変えず、数字だけを変える
#   keep: 置く敵の割合（1 より小さいと、決まった敵を間引く） / enemy_hp: 体力が2以上の敵（落ち武者・弓兵）の体力に、足す数
#   boss_hp: ボス・中ボスの体力の倍率 / drops: 敵が物を落とす確率の倍率 / ammo: 面の始まりの団子 / lives: 残機
LEVELS = {
    "easy": dict(label="EASY", keep=0.7, enemy_hp=0, boss_hp=0.75, drops=1.5, ammo=10, lives=5),
    "normal": dict(label="NORMAL", keep=1.0, enemy_hp=0, boss_hp=1.0, drops=1.0, ammo=6, lives=LIVES),
    "hard": dict(label="HARD", keep=1.0, enemy_hp=1, boss_hp=1.3, drops=0.6, ammo=4, lives=2),
}
LEVEL_ORDER = ("easy", "normal", "hard")
LEVEL = "normal"        # 最初に選ばれている難しさ
LEVEL_LABEL = (150, 252)    # （前の、難しさの表示の場所。いまは、メニューの中に出す）
# スタート画面のメニュー: 決定のキーで開く。上下で項目を選び、決定で進む。
#   main:   STORY（始める）/ OPTION（設定の画面へ）/ HOW TO PLAY（操作説明。assets/images/howto.png。tools/make_howto.py で作る）
#   option: LEVEL（難しさ。左右で変える）/ MUSIC・SOUND（音量。左右で変える）/ BACK（戻る）
#   cx = 行の中心（題名と同じ。どの行も、中央ぞろえ。右の大きなタヌキ侍は、x=265 あたりから。行の幅は、200 まで）
#   y = 1行目の上端 / row・row_option = 行の間隔 / head = 見出しを、1行目より、どれだけ上に出すか / gap = 項目名と値の間 / steps = 音量の段の数
# ディスコグラフィ（スタート画面のメニュー）: 曲のファイルと、曲名。ファイルが無い曲は、並べない
DISCO = (("bgm_story.ogg", "Evening at the Border Post"), ("bgm_map.ogg", "Steps Into the Morning Sun"),
         ("bgm_stage1.ogg", "Clash of the Iron Fan"), ("bgm_boss.ogg", "Crimson Temple Breach"), ("bgm_super.ogg", "Seven Blades High"))
MENU = dict(cx=150, y=196, row=18, row_option=15, head=18, gap=10, steps=5,
            pages=dict(main=("story", "option", "disco", "howto"), option=("level", "music", "sound", "back"),
                       disco=tuple("t%d" % i for i in range(len(DISCO))) + ("back",)),
            label=dict(story="STORY", option="OPTION", disco="DISCOGRAPHY", howto="HOW TO PLAY", level="LEVEL", music="MUSIC", sound="SOUND", back="BACK",
                       **{"t%d" % i: name for i, (_, name) in enumerate(DISCO)}))
RESPAWN_AT = 215        # 倒れてから、中間地点で再開するまでのフレーム数（残機が残っているとき）
RESPAWN_CLEAR = 160     # 再開した場所から、この距離までの敵は置かない（再開してすぐ、ぶつからないように）
CHECKPOINT_W = 24       # 中間地点（鳥居）に触れる範囲の幅
CHECKPOINT_FX = 100     # 中間地点を通ったときの演出のフレーム数（光の柱・火花・「中間地点」の文字・音）

# 穴に落ちたとき
FALL_Y = BASE_H + 40   # 足元がこの高さ（画面の下）を超えたら、落ちたことにする
# 消える光の足場（stage.py の blinks）: period フレームで一巡り。初めの on フレームの間だけ、乗れる。
# そのうち、終わりの warn フレームは、点滅する（もうすぐ消える予告）。消えている間も、うすい枠が見える（どこに出るかが、分かるように）
BLINK = dict(period=200, on=130, warn=40)
# 動く足場（stage の movers）。A から B へ往復する。両端で、dwell（一巡りに対する割合）だけ止まる（乗り降りしやすいように）。period: 往復のフレーム数
MOVER = dict(period=240, dwell=0.14)
# 崖登り（縦に進む区画。stage.py の climb）: 画面が、上下にも動く。跳ぶたびには動かさず、着地した高さを、画面の feet の高さに合わせる。
# 足元が、画面の top より上・bottom より下に出そうなときだけ、すぐ追いかける（落ちたとき）
CLIMB_CAM = dict(feet=190, speed=4, top=70, bottom=230)
# 崖登りの背景: 中景（松・柵など）は、画面の動きの mid 倍だけ、ついてくる（登ると、下へ沈む）。崖の上の中景は、崖より右にだけ出す。
# 空は、縦に長い絵（bg_sky_tall.png）があれば、登るにつれて、絵の下から上へ、見える所が移る。
# 崖の壁は、岩肌のタイル（cliff_*.png）があれば、地面の上端から cliff_rows 段より下を、それで埋める
# overhang: 崖の縁のまわりで、崖の下の中景と、崖の上の中景を、だんだん入れ替える幅（ドット）。崖の下は、縁へ向かって薄くなり、崖の上は、縁より右で、縁から濃くなる（崖の外に、崖の上の中景を出さない。すっぱり切ると、縁にかかった松や島が、四角く切れて見える）
CLIMB_BG = dict(mid=0.6, cliff_rows=2, overhang=56)
CLIFF_PATTERN = (1, 2, 4, 1, 0, 2, 4, 1, 3, 2, 1, 4, 5, 2, 4, 1)     # 岩肌のタイルの並べ方（ほとんどは、無地の岩。ときどき、割れ目・根・苔）
FALL_DAMAGE = 2

# ゲームオーバー
GAMEOVER_START = 70    # 倒れ終わって、少し間をおいてから暗転を始めるフレーム
GAMEOVER_FADE = 90     # 暗くなるまでのフレーム数
GAMEOVER_DIM = 190     # 暗さ（0〜255。255で真っ黒）。背景がうっすら見える程度で止める
GAMEOVER_TEXT_AT = 25  # 「GAME OVER」が出始めるフレーム
GAMEOVER_PROMPT_AT = 60  # 「PRESS ENTER」が出始めるフレーム
GAMEOVER_WAIT = 145    # このフレームまでは、Enter を押しても再開しない

# 2面のボス（二代・基衡「怨庭公家」）: 歩いて、「扇の風」「扇を投げる」を交互に出す。体力が半分になると、「花びらの雨」が入る。
# 順番の文字: W=扇の風 / T=扇を投げる / P=花びらの雨。風は、ダメージなしで、主人公を押し戻す（池や穴が近いと危ない）。
# 扇は、ゆっくり飛んで、戻ってくる（刀で消せる）。花びらは、落ちる場所に、先に目印が出る
# keep_off: 基衡は、部屋の左右の端から、これだけ内側までしか歩かない（左右の、上下する足場の下に入らない。足場に、いつも乗れるように）
BOSS2 = dict(w=36, h=76, keep_off=115, hp=36, touch=1, speed=0.75, near=80, gravity=0.3,
             walk_frames=70, rage_walk_frames=42, recover_frames=56, rage_recover_frames=34,      # 2026-10-13 に、弱すぎたので、テコ入れ（体力 28→36、歩き 90→70、隙 75→56 など）
             wind_ready=34, wind_at=12, wind_frames=34,
             throw_ready=38, throw_ready_chain=20, throw_at=8, throw_frames=26,       # throw_ready_chain: 風のすぐあとの、扇の構え（風で押し戻して、すぐ投げる）
             fan2_delay=14, fan2_y=14,                                                  # 体力が半分以下: 2枚目の扇（足元の高さ）を、14 フレームあとに投げる。しゃがむか、跳ぶか、選ばせる
             petal_ready=50, petal_frames=30,
             gale_frames=30)     # 大風: 扇を振り下ろしてから、次の動き（扇を投げる）に移るまで。予告の長さは GALE の warn
BOSS2_PATTERN = "WTWT"
BOSS2_RAGE_PATTERN = "TPWP"
# 月見坂の基衡（本家）だけが使う順番。G=低い大風（床が風。足場へ登る） / H=高い大風（足場の高さが風。床へ降りる）。
# 安全な場所が、上と下で入れ替わる。金色堂の影の基衡は、足場の無い間で戦うので、上の順番（大風なし）のまま
BOSS2_GALE_PATTERN = "WTGTHT"
BOSS2_GALE_RAGE_PATTERN = "TPGTHTP"
# 大風: ボスの間の、端から端まで、横に吹く。ダメージは無いが、風の帯の中にいると、吹いている間、押され続ける。
# 低い大風は、床から h の高さまで（足場は、これより高い）。高い大風は、床から high_bottom 上がった所から、high_h の高さ
# （足場の上に立つと、帯の中。床に立つと、帯の下。跳ぶと、帯に入って、流される。床の扇は、しゃがむか、斬る）。
# warn=予告の長さ（扇を高く上げて、床に、弱い風の筋と木の葉が流れ始める） / blow=吹いている長さ / push=押す速さ（最高速より小さい。跳べば、進める）
# 見た目: 風の帯を、うすい白で塗る（alpha=濃さ 0〜255。うしろが見える濃さ）。上の縁に、波打つ線（風の高さが、ひと目で分かる）。
# 筋の数・長さ・速さ: 予告は、少なく・短く・ゆっくり（warn_〜）。帯は、だんだん濃くなる。吹いている間は、多く・長く・速く
GALE = dict(h=40, high_bottom=46, high_h=54, push=2.4, warn=70, blow=150, alpha=84, streaks=14, long=34, speed=6.0, leaves=8,
            warn_alpha=50, warn_streaks=6, warn_long=14, warn_speed=1.6, warn_leaves=4)
# 3面のボス（三代・秀衡「鬼角薙将」）。縦に高く、角のある兜に、大鎧、長い薙刀。動きは、1面の泰衡と同じ形
# （歩く → 構える → 薙刀を振って光波、3回に1回、跳びかかり）だが、間合いが長く、光波が速くて遠くまで届く。
# 光波の高さの順は、「低・高」を、交互に薙ぎ分ける
BOSS3 = dict(BOSS, w=34, h=88, hp=30, speed=0.55, near=90, wave_speed=2.3, wave_range=520, high_bottom=34,
             rage_walk_frames=46, rage_recover_frames=40,
             combo=2, rage_combo=3, combo_ready=26,   # 光波を、続けて撃つ（ふだん2発、体力が半分で3発）。2発目からは、構えが短い
             thrust_near=150, thrust_ready=34, thrust_speed=4.4, thrust_range=130,   # 踏み込み突き: 主人公が、この距離より近いと、光波の代わりに突く。構え 34 フレーム（足元に赤い矢印）
             thrust_dash=44, thrust_dash_frames=10)      # 突くとき、前へ 44 ドット踏み込む（10 フレームで）。光波は、速くて短い低い光波（跳ぶか、下がればよけられる）
BOSS3_PATTERN = "LHLLHH"
# 高館の中ボス（弁慶の亡霊「立ち往生」）。道の真ん中に立って、動かない。どこから斬っても、効く（特別な決まりは無い）。
#   離れていると: 薙刀を薙いで、光波を飛ばす（低い = 跳ぶ / 高い = しゃがむ）
#   近づくと（near より内側）: 突き。速いが、thrust_range までしか届かない（下がるか、跳ぶ）
#   攻撃のあとに隙がある。体力が半分になると、光波を2発続け、間が短くなる。倒すと、光になって消える
BENKEI = dict(BOSS, w=24, h=60, hp=14, speed=0.0, near=80, wave_speed=2.0, wave_range=460, high_bottom=34,
              walk_frames=70, rage_walk_frames=44, recover_frames=64, rage_recover_frames=44,
              combo=1, rage_combo=2, combo_ready=26,
              thrust_ready=34, thrust_speed=4.2, thrust_range=90, fade=44, breath=44)
BENKEI_PATTERN = "LHLLH"
# 4面のボス（初代・清衡）。地面から少し浮いて、座ったまま動く。数珠の玉を、高さを変えて飛ばす（低い・真ん中・高い）。
# 玉は、刀で消せる。体力が半分になると、玉の数が増え、間が短くなる
BOSS4 = dict(w=44, h=72, hp=36, bob=2, touch=1, speed=0.7, near=110, gravity=0.3, hover=12,
             walk_frames=80, rage_walk_frames=52, recover_frames=60, rage_recover_frames=40,
             ready=36, fire_at=8, cast_frames=44, gap=36, rage_gap=30,
             ring_ready=44, pillar_frames=102, warp_out=22, warp_in=26, warp_dist=150, warp_min=90, roar=56)
# 攻撃の順（くり返す）。beads=数珠の玉 / pillar=光の柱 / ring=数珠の輪 / warp=転移（すぐ次の攻撃に移る）
BOSS4_CYCLE = ("beads", "pillar", "warp", "beads", "ring", "pillar", "warp", "ring")
BOSS4_RAGE_CYCLE = ("beads", "pillar", "ring", "warp", "pillar", "beads", "warp", "ring")   # 怒ったあと（最初に、転移が入る）
# 光の柱: warn=予告の長さ / beam=柱が出ている長さ / spread=柱の間隔（主人公の足元を中心に並ぶ。間に立てる幅） / stagger=外側の柱が遅れるフレーム数
# flash=落ちる直前に、予告が速く点滅するフレーム数。予告は、柱と同じ太さの、うすい光で見せる（どこまで動けば安全かが、先に分かる）。
# 2026-10-13: 発生が早すぎて、よけづらかったので、予告を長くした（warn 54→78、rage_warn 42→60）。清衡の pillar_frames も、合わせて 78→102
PILLAR = dict(w=20, warn=78, rage_warn=60, flash=14, beam=16, damage=1, count=3, rage_count=5, spread=64, stagger=8)
# 数珠の輪: 清衡のまわり radius の所に count 個の玉が出て、八方へ飛ぶ。横へ飛ぶ玉は、しゃがめば当たらない高さ
RING = dict(count=8, radius=40, speed=1.9, rage_speed=2.3, range=200)
# 後光: 半径 r（怒ると rage_r）、光の筋 rays 本（長い・短いを交互）、spin=回る速さ、dy=体の中心から上へずらす量
HALO = dict(r=44, rage_r=54, rays=16, ray_long=16, ray_short=8, spin=0.012, dy=8, roar_grow=10,
            color=(255, 214, 90), rage_color=(255, 132, 56))
BOSS4_VOLLEYS = ("LMH", "HML", "MHL", "LHM")          # 玉の高さの順（L=低い / M=真ん中 / H=高い）。くり返す
BOSS4_RAGE_VOLLEYS = ("LMHML", "HLMLH", "MHLHM")
BEAD = dict(w=12, h=12, cut_pad=10, speed=1.9, rage_speed=2.2, range=360, damage=1, low=10, mid=26, high=44, ticks=6)   # 高さは、地面から
GUST = dict(w=34, h=40, speed=1.5, range=150, push=2.2, ticks=7, lead=10, sink=2, alpha=110)    # 扇の風（押す速さは、最高速より小さい。押されながらでも、進める。alpha: 風の絵の濃さ 0〜255。薄くして、うしろが見えるように）
FAN = dict(w=16, h=16, speed=1.7, range=170, damage=1, y=40, spin=9, turn=18, steep=1.7)   # steep: 上へ投げる角度の上限（横1に対して、縦 steep。約60度）   # 投げた扇（y=地面からの高さ）。往路のあと、turn フレーム止まって白く光り（戻る予告）、同じ速さで戻る
PETAL = dict(w=7, h=7, count=4, spread=34, warn=44, speed=2.6, top=-12, damage=1, stagger=10)   # 花びらの雨
