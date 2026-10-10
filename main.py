"""平泉タヌキ侍 - メインループ

操作: ←→ 移動 / SPACE or ↑ ジャンプ / Z 刀 / X 木の葉手裏剣 / Enter 再開（ゲームオーバー時） / ESC 終了
"""
import asyncio

import pygame

import config as C
from stage import CHECKPOINT, ITEMS, Terrain
from sprites import Assets, Checkpoint, HitEffect, Item, Player, Shuriken, SlashWave, Wave, make_enemy

# 敵の配置（種類, x）。序盤は落ち武者だけ→中盤に狐火→後半に烏→終盤は混ぜる
DANGO_TOTAL = sum(1 for k, _, _ in ITEMS if k == "dango")   # 団子の数

ENEMY_SPAWNS = (
    ("ochimusha", 520), ("ochimusha", 900),
    ("kitsunebi_low", 1250), ("kitsunebi_high", 1420), ("ochimusha", 1455),
    ("karasu", 1850), ("karasu", 2000),
    ("ochimusha", 2100), ("kitsunebi_high", 2200), ("karasu", 2300),
)
# 地面タイルの並べ方（石畳A・B・苔・落ち葉）。位置から決めるので、スクロールしても変わらない
FILL_PATTERN = (0, 3, 0, 4, 3, 0, 3, 5, 0, 3, 4, 0)


class Game:
    def __init__(self, terrain=None):
        self.a = Assets()
        self.terrain = terrain or Terrain()
        self.reset()

    def reset(self):
        """最初から（残機・スコア・中間地点も、初期値に戻す）"""
        self.lives = C.LIVES
        self.score = 0
        self.dango = 0
        self.taken = set()          # 取ったアイテム（配置表の番号）
        self.one_up_given = False
        self.checkpoint = Checkpoint(*CHECKPOINT, self.a)
        self.cp_state = None        # 中間地点を通ったときの (スコア, 団子の数, 取ったもの)
        self._start(60, float(C.FLOOR_Y))

    def respawn(self):
        """やられて、残機が残っているとき: 中間地点（なければ最初）から、体力満タンで再開する"""
        if self.cp_state:
            self.score, self.dango, taken = self.cp_state
            self.taken = set(taken)
            self._start(self.checkpoint.x, float(self.checkpoint.y))
        else:
            self.score, self.dango, self.taken = 0, 0, set()
            self._start(60, float(C.FLOOR_Y))

    def _start(self, x, y):
        self.player = Player(x, self.a)
        self.player.py = y
        self.player.safe_x, self.player.safe_y = float(x), y
        self.enemies = [make_enemy(kind, ex, self.a, self.terrain) for kind, ex in ENEMY_SPAWNS]
        self.shurikens = []
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
        if "jump" in pressed:
            p.jump()
        if "jump_release" in pressed:
            p.cut_jump()
        if "attack" in pressed:
            p.attack()
        if "throw" in pressed:
            p.throw()
        p.update(held, C.STAGE_W, self.terrain)
        if p.release:
            self.shurikens.append(Shuriken(*p.shuriken_spawn(), self.a))
        if p.slash:
            self.slashes.append(SlashWave(*p.slash_spawn(), self.a))
        for e in self.enemies:
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
            it.update()
        for s in self.shurikens:
            s.update(C.STAGE_W)

        # 刀 → 敵（1振りにつき、同じ敵に1回だけ）
        sword = p.sword_rect()
        if sword:
            for e in self.enemies:
                if e.active and e.last_swing != p.swing_id and sword.colliderect(e.rect):
                    e.last_swing = p.swing_id
                    e.hit(C.SWORD_DAMAGE)
        # 手裏剣 → 敵
        for s in self.shurikens:
            for e in self.enemies:
                if s.alive and e.active and s.rect.colliderect(e.rect):
                    s.alive = False
                    e.hit(C.SHURIKEN_DAMAGE)
                    self.effects.append(HitEffect(*s.rect.center, self.a))
        # 強化中の光波 → 敵
        for s in self.slashes:
            for e in self.enemies:
                if s.alive and e.active and s.rect.colliderect(e.rect):
                    s.alive = False
                    e.hit(C.SLASH["damage"])
                    self.effects.append(HitEffect(*s.rect.center, self.a))
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
                else:
                    p.power = True
        # 中間地点（鳥居）を通る
        if not self.checkpoint.active and p.rect.colliderect(self.checkpoint.rect):
            self.checkpoint.active = True
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
            if w.alive and not p.invincible and p.rect.colliderect(w.rect):
                w.alive = False
                p.take_damage(w.px, C.WAVE["damage"])
        # 敵 → 主人公（踏んでも倒せない。触れるとダメージ）
        for e in self.enemies:
            if e.active and p.rect.colliderect(e.rect):
                p.take_damage(e.rect.centerx, e.P["touch"])

        self.enemies = [e for e in self.enemies if e.alive]
        self.shurikens = [s for s in self.shurikens if s.alive]
        self.waves = [w for w in self.waves if w.alive]
        self.slashes = [s for s in self.slashes if s.alive]
        self.items = [it for it in self.items if it.alive]
        for fx in self.effects:
            fx.update()
        self.effects = [fx for fx in self.effects if fx.alive]

        self.cam_x = max(0, min(p.rect.centerx - C.BASE_W // 2, C.STAGE_W - C.BASE_W))

    # --- 描画 ---
    def draw(self, screen, font):
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
        if self.player.hp <= 0:
            self._draw_dim(screen)
        self._draw_hud(screen, font)
        if self.player.hp <= 0:
            self._draw_gameover_text(screen, font)

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
        if self.player.power:   # 強化中の印（金の葉）
            x, y = 8 + C.PLAYER_HP * 14 + 6, 13
            pygame.draw.polygon(screen, C.BLACK, [(x, y - 7), (x + 6, y), (x, y + 7), (x - 6, y)])
            pygame.draw.polygon(screen, (252, 208, 40), [(x, y - 4), (x + 3, y), (x, y + 4), (x - 3, y)])
        text = font.render("%06d" % self.score, False, C.TEXT)
        screen.blit(text, (C.BASE_W - text.get_width() - 8, 8))
        dango = pygame.transform.scale(self.a.item["dango"], (4, 12))
        screen.blit(dango, (8, 24))
        screen.blit(font.render("%d/%d" % (self.dango, DANGO_TOTAL), False, C.TEXT), (16, 26))
        screen.blit(font.render("LIFE x%d" % max(self.lives, 0), False, C.TEXT), (C.BASE_W - 64, 24))
        if self.msg_t:   # 団子を全部取った
            screen.blit(self.a.oneup, (self.player.rect.centerx - self.cam_x - self.a.oneup.get_width() // 2,
                                       self.player.rect.top - 28 - (90 - self.msg_t) // 4))

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
    game = Game()

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
        game.draw(screen, font)
        pygame.transform.scale(screen, window.get_size(), window)
        pygame.display.flip()
        clock.tick(C.FPS)
        await asyncio.sleep(0)   # ブラウザ版では、毎フレームここで制御をブラウザに返す


if __name__ == "__main__":
    asyncio.run(main())
