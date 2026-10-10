"""画面サイズ・色・物理定数・アニメの割り当て"""

TITLE = "平泉タヌキ侍"

# 内部解像度（16:9）。表示は SCALE 倍に拡大する
BASE_W, BASE_H = 480, 270
SCALE = 2
FPS = 60

STAGE_W = 4080   # 1面の長さ（最後の1画面ぶんが、ボスの場所）。遠景・中景は、この長さに合わせて、カメラの動きに比例して流れる
GROUND_Y = 222   # 地面の上端（タイルの上端）
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
JUMP_BUFFER = 8      # ジャンプを、着地や振り終わりの少し前に押しても、覚えておいて、できるようになったらすぐ跳ぶフレーム数
COYOTE = 5           # 足場の縁から出てしまっても、このフレーム数までは跳べる
ATTACK_MOVE = 0.6    # 刀・手裏剣の動作中に、向いているほうを押し続けたときの速さ（最高速に掛ける）。止まらずに、動きにつながる
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
SHURIKEN_RANGE = 170  # 手裏剣が飛ぶ距離（画面の幅の、3分の1ほど）
SHURIKEN_TICKS = 3   # 回転1コマの長さ
HIT_TICKS = 4        # 命中の破片1コマの長さ

# 攻撃のダメージ。刀は強く、手裏剣は弱い（そのかわり離れて撃てる）
SWORD_DAMAGE = 2
SHURIKEN_DAMAGE = 1

# 敵（ザコ）3種類。大きさ・体力・速さ・動きを変えて、見た目も攻略も区別する
HIT_FLASH = 6    # 攻撃を受けたとき白く光るフレーム数
HIT_STUN = 8     # 攻撃を受けたとき動きが止まるフレーム数

# 落ち武者（地上の歩兵）: 大きく、遅く、体力が多い。近づくと一度止まって構える
OCHI = dict(w=20, h=40, hp=3, touch=1, speed=0.6, active=240, ready_dist=110, ready_frames=30, swing_frames=26, wave_at=6, cooldown=120, turn_frames=150, patrol=40)
# 狐火（浮遊する炎）: 小さく、空中を上下に揺れながら横に進む。高さは低め・高めの2通り
KITSUNEBI = dict(w=14, h=14, hp=1, touch=1, speed=0.9, active=380, bob=12, period=90,
                 low=FLOOR_Y - 36, high=FLOOR_Y - 92)
# 烏（カラス）: 横長で速い。近づくと羽ばたいて予告し、そのときの主人公の位置へ急降下する
KARASU = dict(w=22, h=12, hp=1, touch=1, speed=3.5, active=240, telegraph=30, height=FLOOR_Y - 110)

# 敵の絵（assets/images/enemies/種類_動き_番号.png）。コマ数と、枠の中の基準位置（変換ツールが表示する値）
ENEMY_FRAMES = {
    "ochimusha": {"walk": 4, "stance": 3, "swing": 2, "death": 3},
    "kitsunebi": {"flicker": 4, "death": 4},
    "karasu": {"flap": 4, "dive": 2, "death": 2},
}
# w,h = 枠の大きさ / ax = 枠の中の、体の中心の左右位置 / ay = 足元（bottom）か中心（center）の上下位置
ENEMY_ART = {
    "ochimusha": dict(w=62, h=51, ax=31, ay=51, mode="bottom"),
    "kitsunebi": dict(w=16, h=18, ax=8, ay=9, mode="center"),
    "karasu": dict(w=42, h=25, ax=21, ay=12, mode="center"),
    "boss": dict(w=124, h=102, ax=62, ay=102, mode="bottom"),   # 仮の絵: 落ち武者を2倍にしたもの
}

# 落ち武者の光波（刀を振ると、前方の地面すれすれを飛ぶ。ジャンプでよけるか、刀で消せる。手裏剣は通り抜ける）
WAVE_FRAMES = 3
WAVE = dict(w=4, h=14, speed=1.1, range=140, damage=1, dy=-9, ticks=7)

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
CLEAR_WAIT = 120                # クリアしてから、Enter を受け付けるまでのフレーム数
# ボスを倒したあとの寸劇: ボスが決まった場所へ吹っ飛ぶ → タヌキ侍が決まった場所へ歩く → 間 → 倒れたボスがひとこと → 光になって消える → タヌキ侍が返す → 右へ駆け抜ける → 結果
#   skip: せりふを、キーで送れるようになるまでのフレーム数（字が出ている途中なら、まず全部出す）。type: 字を1文字出すフレーム数。exit: 画面の外へ、どこまで走るか
ENDING = dict(wait=30, boss=270, fade=70, reply=280, skip=20, type=8, exit=40)
BOSS_TRIGGER = 110              # ボスの場所の左端から、ここまで入ると、ボスが出る（画面は、そこから右端まで流れて止まる）
BOSS_CAM_SPEED = 3              # そのときに、画面が流れる速さ
END_BOSS_X = BOSS_X             # 倒したボスが、吹っ飛んで倒れる場所（降ってきた場所と同じ）
END_TANUKI_X = ARENA_X0 + BOSS_TRIGGER + 20   # タヌキ侍が、話すときに立つ場所（ボスが出てきたときに、立っていたあたり）
END_BLOW = dict(vy=-5.0, frames=40, rest=24, limit=600)   # 吹っ飛び: 上向きの速さ、横に動く時間、倒れてからの間。limit: 場所に着けないときの打ち切り
STARTLE = 44                    # ボスが降ってきたとき、タヌキ侍が驚いて跳ねるフレーム数
TALK_BOSS = "talk_boss1.png"        # ボスのせりふ（吹き出しの中の字）
TALK_TANUKI = "talk_tanuki1.png"    # タヌキ侍のせりふ
TALK_CELL = 18                  # せりふの絵の、1文字のますの幅（tools/make_talk_text.py と合わせる）
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
DROPS = (("onigiri", 0.14), ("leaf", 0.12), ("triple", 0.12), ("super", 0.06))
DROP_LIFE = 540                 # 落とし物が消えるまでのフレーム数（最後の2秒は点滅）
DROP_HOP = -2.6                 # 落とし物が出たときの、上向きの速さ（少し跳ねて、地面に落ちる）
DROP_GRAVITY = 0.22
SLASH = dict(w=8, h=26, speed=3.0, range=220, damage=1, ticks=5)   # 強化中の、刀の光波
SLASH_FRAMES = 3

# 音
BGM_STAGE1 = "bgm_stage1.ogg"  # 1面の曲。曲名は「Clash of the Iron Fan」
BGM_STORY = "bgm_story.ogg"    # 始まりの語りの間（おとなしい曲）。曲名は「Evening at the Border Post」。ファイルが無ければ、無音
BGM_BOSS = "bgm_boss.ogg"      # ボスと戦っている間。曲名は「Crimson Temple Breach」（くり返せるように、終わりの締めを切ってある）
BGM_SUPER = "bgm_super.ogg"    # スーパータヌキの間（短くて、勢いのある曲）。ファイルが無ければ、面の曲のまま
BGM_VOLUME = 0.5
BGM_VOLUMES = {BGM_STORY: 0.4}   # 曲ごとの音量（書いていない曲は BGM_VOLUME）。語りの曲は、少し小さく
SFX_THUNDER = "sfx_thunder.ogg"   # 雷鳴（スタート画面）
SFX_SWORD = "sfx_sword.ogg"       # 刀を抜く「ジャキン」（スタート画面で決定したとき）
SFX_CHECKPOINT = "sfx_checkpoint.ogg"   # 中間地点を通ったときの音（琴のような音階に、鈴の余韻）
SFX_TALK_LOW = "sfx_talk_low.ogg"     # せりふの字が出るときの「ピッ」（ボス。低い）
SFX_TALK_HIGH = "sfx_talk_high.ogg"   # 同じ（タヌキ侍。高い）
SFX_VOLUME = {SFX_THUNDER: 0.3, SFX_SWORD: 0.3, SFX_CHECKPOINT: 0.22, SFX_TALK_LOW: 0.07, SFX_TALK_HIGH: 0.07}   # 効果音の大きさ（抑えめ）。音は tools/make_sfx.py で作る
BGM_FADE_MS = 1200      # やられたとき、曲が消えていくまでの時間

# スタート画面: 絵（assets/images/title.png、480×270）の上に、題名を重ねる。Enter（Z・Space でも）で始まる。
# クリアのあとは、ここへ戻る。題名は、絵の左の空（右は主人公と月）に置く。
# 題名の絵は tools/make_title_logo.py（昔のゲームのロゴ風）、「PUSH ENTER KEY」は tools/make_text_image.py で作る
# 絵が無いときは、1面の始まりの景色を暗くして、代わりにする
TITLE_BG = "title.png"
TITLE_DIM = 70          # 絵が無いとき、景色を暗くする度合い（0〜255）
TITLE_LOGO = (150, 14)    # 題名の、左右の中心と上端
TITLE_PROMPT = (150, 232)  # 「PUSH ENTER KEY」の、左右の中心と上端
# 放っておくと、ときどき稲光が走り、少し遅れて雷鳴が鳴る（間隔は、この順のくり返し。フレーム数）
TITLE_THUNDER = (240, 600, 420, 780)
TITLE_FLASH = 26        # 稲光のフレーム数（2回光る）。空に稲妻が走り、画面も少しだけ明るくなる
# 稲妻: 走る場所（左右の範囲・上端・下端）。絵の、空が見えている所に合わせる（題名と月の間）
BOLT = dict(x0=256, x1=284, top=0, bottom=128, step=9, jitter=7,
            core=(255, 255, 255), glow=(150, 180, 255), sky=(200, 215, 255), sky_alpha=70)
THUNDER_DELAY = 22      # 稲光から雷鳴までのフレーム数
TITLE_START = 40        # 決定（刀の音）から、始まるまでのフレーム数。この間、案内が速く点滅する

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

# 残機・中間地点
LIVES = 3
RESPAWN_AT = 215        # 倒れてから、中間地点で再開するまでのフレーム数（残機が残っているとき）
RESPAWN_CLEAR = 160     # 再開した場所から、この距離までの敵は置かない（再開してすぐ、ぶつからないように）
CHECKPOINT_W = 24       # 中間地点（鳥居）に触れる範囲の幅
CHECKPOINT_FX = 100     # 中間地点を通ったときの演出のフレーム数（光の柱・火花・「中間地点」の文字・音）

# 穴に落ちたとき
FALL_Y = BASE_H + 40   # 足元がこの高さ（画面の下）を超えたら、落ちたことにする
FALL_DAMAGE = 2

# ゲームオーバー
GAMEOVER_START = 70    # 倒れ終わって、少し間をおいてから暗転を始めるフレーム
GAMEOVER_FADE = 90     # 暗くなるまでのフレーム数
GAMEOVER_DIM = 190     # 暗さ（0〜255。255で真っ黒）。背景がうっすら見える程度で止める
GAMEOVER_TEXT_AT = 25  # 「GAME OVER」が出始めるフレーム
GAMEOVER_PROMPT_AT = 60  # 「PRESS ENTER」が出始めるフレーム
GAMEOVER_WAIT = 145    # このフレームまでは、Enter を押しても再開しない
