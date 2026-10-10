"""平泉タヌキ侍 - メインループ

操作: ←→ 移動 / SPACE or ↑ ジャンプ / Z 刀 / X 木の葉手裏剣 / Enter 再開（ゲームオーバー時） / ESC 終了
"""
import asyncio

import pygame

import config as C
from sprites import Assets, Enemy, HitEffect, Player, Shuriken

ENEMY_XS = (520, 820, 1120, 1500, 1900)
# 地面タイルの並べ方（石畳A・B・苔・落ち葉）。位置から決めるので、スクロールしても変わらない
FILL_PATTERN = (0, 3, 0, 4, 3, 0, 3, 5, 0, 3, 4, 0)


class Game:
    def __init__(self):
        self.a = Assets()
        self.reset()

    def reset(self):
        self.player = Player(60, self.a)
        self.enemies = [Enemy(x) for x in ENEMY_XS]
        self.shurikens = []
        self.effects = []
        self.cam_x = 0

    # --- 1フレーム進める。held は押している間のキー、pressed はこのフレームに押したキー ---
    def step(self, held, pressed=()):
        p = self.player
        if p.hp <= 0:
            if "restart" in pressed:
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
        p.update(held, C.STAGE_W)
        if p.release:
            self.shurikens.append(Shuriken(*p.shuriken_spawn(), self.a))
        for e in self.enemies:
            e.update()
        for s in self.shurikens:
            s.update(C.STAGE_W)

        # 刀 → 敵（1振りにつき、同じ敵に1回だけ）
        sword = p.sword_rect()
        if sword:
            for e in self.enemies:
                if e.alive and e.last_swing != p.swing_id and sword.colliderect(e.rect):
                    e.last_swing = p.swing_id
                    e.hit()
        # 手裏剣 → 敵
        for s in self.shurikens:
            for e in self.enemies:
                if s.alive and e.alive and s.rect.colliderect(e.rect):
                    s.alive = False
                    e.hit()
                    self.effects.append(HitEffect(*s.rect.center, self.a))
        # 敵 → 主人公（踏んでも倒せない。触れるとダメージ）
        for e in self.enemies:
            if e.alive and p.rect.colliderect(e.rect):
                p.take_damage(e.rect.centerx)

        self.enemies = [e for e in self.enemies if e.alive]
        self.shurikens = [s for s in self.shurikens if s.alive]
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
        self.player.draw(screen, cam)
        for fx in self.effects:
            fx.draw(screen, cam)
        self._draw_hud(screen, font)

    def _draw_ground(self, screen, cam):
        tiles = self.a.tiles
        top = tiles[1]
        first = cam // 32
        for i in range(first, first + C.BASE_W // 32 + 2):
            x = i * 32 - cam
            screen.blit(top, (x, C.GROUND_Y))
            row = 0
            y = C.GROUND_Y + top.get_height()
            while y < C.BASE_H:
                screen.blit(tiles[FILL_PATTERN[(i * 7 + row * 5) % len(FILL_PATTERN)]], (x, y))
                y += 32
                row += 1

    def _draw_hud(self, screen, font):
        for i in range(C.PLAYER_HP):
            color = C.HEART if i < self.player.hp else C.HEART_EMPTY
            pygame.draw.rect(screen, C.BLACK, (8 + i * 14 - 1, 8 - 1, 12, 12))
            pygame.draw.rect(screen, color, (8 + i * 14, 8, 10, 10))
        if self.player.hp <= 0:
            for k, line in enumerate(("GAME OVER", "PRESS ENTER")):
                img = font.render(line, False, C.TEXT)
                screen.blit(img, (C.BASE_W // 2 - img.get_width() // 2, 110 + k * 18))


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
