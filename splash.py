"""起動したときの、会社のロゴ画面（ゲームの内容とは関係ない。起動の1回だけ）。
白い背景に、ロゴがふわっと現れて、消える。何かを押すと、飛ばせる。
ロゴは、小さな画面（480×270）ではなく、窓にそのまま描く（拡大してぼやけないように）。
"""
import os

import pygame

import config as C

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "images", C.LOGO["file"])


class Splash:
    def __init__(self):
        self.t = 0
        try:
            self.logo = pygame.image.load(PATH).convert_alpha()
        except (pygame.error, FileNotFoundError):    # ロゴが読めなくても、ゲームは止めない（飛ばして始める）
            self.logo = None
        self._cache = (None, None)      # （窓の大きさ, その大きさに合わせたロゴ）

    @property
    def done(self):
        return self.logo is None or self.t >= C.LOGO["fade"] * 2 + C.LOGO["hold"]

    def skip(self):
        self.t = C.LOGO["fade"] * 2 + C.LOGO["hold"]

    def alpha(self):
        """いまの濃さ（0〜255）: ふわっと現れる → 止まる → ふわっと消える"""
        f, hold = C.LOGO["fade"], C.LOGO["hold"]
        return 255 * max(0, min(self.t, f, f * 2 + hold - self.t)) // f

    def step(self):
        self.t += 1

    def draw(self, window):
        window.fill(C.LOGO["bg"])
        if self.logo is None:
            return
        ww, wh = window.get_size()
        if self._cache[0] != (ww, wh):
            w = min(round(ww * C.LOGO["width"]), round(wh * C.LOGO["width"] * 2.5))
            self._cache = ((ww, wh), pygame.transform.smoothscale(self.logo, (w, round(w * self.logo.get_height() / self.logo.get_width()))))
        img = self._cache[1]
        img.set_alpha(self.alpha())
        window.blit(img, ((ww - img.get_width()) // 2, (wh - img.get_height()) // 2))
