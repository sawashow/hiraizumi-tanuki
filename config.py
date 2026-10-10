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

# 敵（仮の四角）
ENEMY_W, ENEMY_H = 16, 20
ENEMY_SPEED = 0.6
ENEMY_PATROL = 70
ENEMY_HP = 2
