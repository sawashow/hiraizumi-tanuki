"""画面サイズ・色・物理定数・アニメの割り当て"""

TITLE = "平泉タヌキ侍"

# 内部解像度（16:9）。表示は SCALE 倍に拡大する
BASE_W, BASE_H = 480, 270
SCALE = 2
FPS = 60

STAGE_W = 2400   # 1面の長さ（遠景・中景の幅から逆算して決めた）
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
TURN_DECEL = 0.38    # 地上で逆向きに押したときの減速（すべって切り返す）
AIR_ACCEL = 0.18     # 空中で押したときの加速（逆向きでも約0.4秒で反転する）
AIR_FRICTION = 0.02  # 空中で離したときの減速（勢いはほぼ保たれる）
WALK_MIN_SPEED = 0.15  # これ以上の速さなら歩きのコマにする

# 主人公
PLAYER_W, PLAYER_H = 16, 36          # 当たり判定（体だけ。しっぽと刀は見た目だけ）
FRAME_W, FRAME_H = 64, 48            # 絵の枠
HEAD_X = 35                          # 絵の中の頭の左右位置（右向きのとき）
PLAYER_HP = 6
INVINCIBLE_FRAMES = 90
HURT_FRAMES = 24
KNOCKBACK = 3.0

# 絵のコマ番号（assets/images/player_XX.png）
IDLE = (0, 1)
WALK = (2, 3, 4, 5, 6, 7)
WALK_TICKS = 5
HURT = (12, 13)
# やられて倒れる動き: (絵, 表示するフレーム数)。最後は、倒れたまま
DEFEAT_SEQ = ((13, 14), (24, 16), (25, 16))
DEFEAT_END = 26
JUMP_TAKEOFF, JUMP_RISE, JUMP_TOP, JUMP_FALL, JUMP_LAND = 14, 15, 16, 17, 18

# 刀: (コマ番号, 表示フレーム数)。判定が出るのは SWORD_ACTIVE 番目のコマだけ
SWORD_SEQ = ((8, 5), (9, 4), (10, 7), (11, 8))
SWORD_ACTIVE = 2
SWORD_W, SWORD_H = 30, 30

# 手裏剣を投げる動作。THROW_RELEASE 番目のコマに入ったとき発射する
THROW_SEQ = ((19, 4), (20, 4), (21, 4), (22, 8))
THROW_RELEASE = 2
SHURIKEN_SPEED = 4.5
SHURIKEN_W, SHURIKEN_H = 12, 8
SHURIKEN_RANGE = 300
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
KITSUNEBI = dict(w=14, h=14, hp=2, touch=1, speed=0.9, active=380, bob=12, period=90,
                 low=FLOOR_Y - 36, high=FLOOR_Y - 92)
# 烏（カラス）: 横長で速い。近づくと羽ばたいて予告し、そのときの主人公の位置へ急降下する
KARASU = dict(w=22, h=12, hp=2, touch=1, speed=3.5, active=240, telegraph=30, height=FLOOR_Y - 110)

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
}

# 落ち武者の光波（刀を振ると、前方の地面すれすれを飛ぶ。ジャンプでよけるか、刀で消せる。手裏剣は通り抜ける）
WAVE_FRAMES = 3
WAVE = dict(w=4, h=14, speed=1.1, range=140, damage=1, dy=-9, ticks=7)

# アイテム。団子=スコア / おにぎり=回復 / 金の葉=強化（刀を振ると光波が出る。ダメージを受けると消える）
ITEM_SIZE = 16
SCORE_DANGO = 100
SCORE_FULL_HP = 50      # 体力が満タンでおにぎりを取ったときのスコア
HEAL_ONIGIRI = 1
SLASH = dict(w=8, h=26, speed=3.0, range=220, damage=1, ticks=5)   # 強化中の、刀の光波
SLASH_FRAMES = 3

# 音
BGM_STAGE1 = "bgm_stage1.ogg"
BGM_BOSS = "bgm_boss.ogg"      # ボスができたら使う（まだ、鳴らす場面がない）
BGM_VOLUME = 0.5
BGM_FADE_MS = 1200      # やられたとき、曲が消えていくまでの時間

# 残機・中間地点
LIVES = 3
RESPAWN_AT = 215        # 倒れてから、中間地点で再開するまでのフレーム数（残機が残っているとき）
CHECKPOINT_W = 24       # 中間地点（鳥居）に触れる範囲の幅

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
