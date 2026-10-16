"""スマホのタッチ操作。画面の左右の帯に、目印を出す（ゲームの絵には重ねない）。
一度でも画面に触ると、目印が出る（キーボード・コントローラで遊ぶ人には、出さない）。

決まった小さな場所を、正確に押さなくてよい作りにする（手元を見ずに遊べるように）:
  左半分＝移動のスティック。触った所が中心になり、指を左右にずらすと歩き、下へずらすと、しゃがむ。
          中心は、指が離れすぎると、ついてくる（反対へ向きを変えるのに、大きく戻さなくてよい）
  右半分＝高さで選ぶ3つの帯。上から、手裏剣・刀・ジャンプ（ジャンプが、いちばん広い）。
          指を滑らせて、別の帯に入ると、そちらが出る。右上の小さな丸は、ポーズ（丸そのものを押したときだけ。誤って止めないように）
ゲームの絵は、窓から左右の帯を除いた所に、16:9 のまま、できるだけ大きく出す（config.TOUCH の side が、帯の幅）。
コントローラ（gamepad.py）と同じく、「このフレームに押したもの」（handle）と「押している方向」（held）を返す。
"""
import pygame

import config as C

# 押した瞬間に、何になるか（コントローラの A・X・B・START と同じ）。ジャンプは、決定も兼ねる
PRESS = {"jump": ("jump", "restart"), "attack": ("attack",), "throw": ("throw",), "pause": ("restart", "pause")}
RELEASE = {"jump": ("jump_release",)}
ACTIONS = ("throw", "attack", "jump")       # 右半分の帯（上から）


class Stick:
    """移動のスティック（左半分の指1本）。触った所が中心。中心は、指が離れすぎると、ついてくる"""

    def __init__(self, x, y, wh):
        self.ox, self.oy = x, y
        self.x, self.y = x, y
        self.wh = wh

    def move(self, x, y):
        K, u = C.TOUCH, self.wh
        lim, vlim = u * K["stick_max"], u * K["stick_down"] * 1.5     # 縦は、しゃがむのに要る分は、残す
        self.x, self.y = x, y
        self.ox = min(max(self.ox, x - lim), x + lim)     # 離れすぎたら、中心が、指についてくる
        self.oy = min(max(self.oy, y - vlim), y + vlim)

    def dirs(self):
        K, u = C.TOUCH, self.wh
        dx, dy = self.x - self.ox, self.y - self.oy
        out = set()
        if dx >= u * K["stick_dead"]:
            out.add("right")
        elif dx <= -u * K["stick_dead"]:
            out.add("left")
        if dy >= u * K["stick_down"]:
            out.add("down")
        elif dy <= -u * K["stick_down"]:
            out.add("up")       # メニューの項目選び
        return out


class Touch:
    def __init__(self):
        self.active = False     # 一度でも触ったら、目印を出す
        self.fingers = {}       # 指の番号 → Stick（移動）か、"jump" などの名前

    # --- 並び（窓の大きさから、毎回計算する） ---
    @staticmethod
    def game_rect(ww, wh):
        """ゲームの絵を出す所: 左右の帯を除いた所に、16:9 で、できるだけ大きく"""
        side = round(wh * C.TOUCH["side"])
        k = min((ww - 2 * side) / C.BASE_W, wh / C.BASE_H)
        w, h = round(C.BASE_W * k), round(C.BASE_H * k)
        return pygame.Rect((ww - w) // 2, (wh - h) // 2, w, h)

    @staticmethod
    def bands(wh):
        """右半分の帯の、上端と下端: {名前: (上, 下)}。ポーズは、右上の隅（帯の上の端の、さらに上）"""
        cut = C.TOUCH["cuts"]           # 手裏剣・刀・ジャンプの境目（窓の高さに対する割合）
        ys = [round(wh * c) for c in cut] + [wh]
        return {name: (ys[i], ys[i + 1]) for i, name in enumerate(ACTIONS)}

    @staticmethod
    def pause_button(ww, wh):
        """ポーズのボタン（右上の、小さな丸）: (x, y, 半径)。丸そのものを押したときだけ効く（端を触って、誤って止めないように）"""
        side = round(wh * C.TOUCH["side"])
        r = round(wh * C.TOUCH["pause_r"])
        return ww - max(side // 2, r + 6), round(wh * C.TOUCH["cuts"][0] / 2), r

    def _action(self, x, y, ww, wh):
        """右半分の (x, y) が、どの帯か（ポーズの丸なら "pause"。帯より上は、何も無い）"""
        px, py, pr = self.pause_button(ww, wh)
        if (x - px) ** 2 + (y - py) ** 2 <= pr * pr:
            return "pause"
        for name, (top, bottom) in self.bands(wh).items():
            if top <= y < bottom:
                return name
        return None

    # --- イベントから、「このフレームに押した」ものを返す ---
    def handle(self, event, size):
        t = event.type
        if t not in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
            return set()
        self.active = True
        ww, wh = size
        x, y = event.x * ww, event.y * wh
        fid = event.finger_id
        before = self.fingers.get(fid)
        if t == pygame.FINGERDOWN:
            if x < ww / 2:
                self.fingers[fid] = Stick(x, y, wh)
                return set()
            now = self._action(x, y, ww, wh)
        elif t == pygame.FINGERMOTION:
            if isinstance(before, Stick):
                before.move(x, y)
                return set()
            now = self._action(x, y, ww, wh) if before is not None else None
            if before == "pause" or now == "pause":     # ポーズには、滑らせて入らない（誤って止めない）
                now = before
        else:
            now = None
        out = set()
        if now != before and not isinstance(before, Stick):
            if before is not None:
                out |= set(RELEASE.get(before, ()))
            if now is not None:
                out |= set(PRESS.get(now, ()))
        if now is None:
            self.fingers.pop(fid, None)
        else:
            self.fingers[fid] = now
        return out

    def held(self):
        out = set()
        for v in self.fingers.values():
            if isinstance(v, Stick):
                out |= v.dirs()
        if "left" in out and "right" in out:
            out -= {"left", "right"}
        return out

    # --- 描く ---
    def draw(self, window):
        """左＝移動: 指を置いていないときは、帯に薄い目印だけ。指を置くと、指の所に輪（中心）とつまみ（ゲームの絵の上でも、半透明）。
        右＝武器: 親指の動く弧に沿って、ボタンを並べる（下ほど内側）。押している帯は、ボタンを塗って、帯もうっすら明るくする"""
        ww, wh = window.get_size()
        K = C.TOUCH
        side = round(wh * K["side"])
        base, lit, mark = K["color"], K["lit"], K["mark"]
        pressed = {v for v in self.fingers.values() if isinstance(v, str)}
        dirs = self.held()
        sticks = [f for f in self.fingers.values() if isinstance(f, Stick)]
        R = round(wh * K["ring"])
        if not sticks:          # 目印: 「ここに触って、動かす」
            self._stick(window, max(side // 2, R + 6), round(wh * 0.62), R, set(), alpha=K["hint_alpha"])    # 帯が細くても、画面の端で切れないように
        for f in sticks:
            self._stick(window, f.ox, f.oy, R, dirs, alpha=K["ring_alpha"], knob=(f.x, f.y))
        # 右の帯: 高さの帯ごとに、ボタン（親指の弧: 下ほど内側）
        for k, (name, (top, bottom)) in enumerate(self.bands(wh).items()):
            on = name in pressed
            if on:      # 押している帯を、うっすら明るく
                band = pygame.Surface((side, bottom - top), pygame.SRCALPHA)
                band.fill(lit + (K["band_alpha"],))
                window.blit(band, (ww - side, top))
            elif k:
                pygame.draw.line(window, base, (ww - side + 8, top), (ww - 8, top), 1)
            r = min(side // 2 - 8, (bottom - top) // 2 - 6)
            bx = ww - side // 2 + round(side * K["arc"][k])
            bx = min(max(bx, ww - side + r + 4), ww - r - 4)
            my = (top + bottom) // 2
            pygame.draw.circle(window, lit if on else base, (bx, my), r, 0 if on else max(2, r // 10))
            self._icon(window, name, bx, my, r, (16, 16, 24) if on else mark)
        px, py, r = self.pause_button(ww, wh)
        on = "pause" in pressed
        pygame.draw.circle(window, lit if on else base, (px, py), r, 0 if on else max(2, r // 6))
        self._icon(window, "pause", px, py, r, (16, 16, 24) if on else mark)

    @staticmethod
    def _stick(window, cx, cy, R, dirs, alpha, knob=None):
        """スティックの輪（中心）・左右と下の矢印・つまみ。半透明（ゲームの絵の上にも出す）"""
        K = C.TOUCH
        size = R * 2 + 8
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        pygame.draw.circle(surf, K["mark"] + (alpha,), (c, c), R, 2)
        s = max(4, R // 4)
        for name, (vx, vy) in (("left", (-1, 0)), ("right", (1, 0)), ("down", (0, 1)), ("up", (0, -1))):
            if name == "up" and name not in dirs:
                continue        # 上は、メニューでだけ使う（押していないときは、出さない）
            px, py = c + vx * (R - s - 2), c + vy * (R - s - 2)
            tip = (px + vx * s, py + vy * s)
            wing = ((px - vy * s - vx * s // 2, py - vx * s - vy * s // 2), (px + vy * s - vx * s // 2, py + vx * s - vy * s // 2))
            on = name in dirs
            pygame.draw.polygon(surf, (K["lit"] if on else K["mark"]) + (255 if on else alpha,), (tip,) + wing)
        window.blit(surf, (round(cx) - c, round(cy) - c))
        if knob:        # つまみ: 指の所（輪の中に収める）
            dx, dy = knob[0] - cx, knob[1] - cy
            d = max(1.0, (dx * dx + dy * dy) ** 0.5)
            k = min(1.0, (R - s) / d)
            kr = max(5, R // 3)
            ks = pygame.Surface((kr * 2, kr * 2), pygame.SRCALPHA)
            pygame.draw.circle(ks, K["lit"] + (alpha + 40,), (kr, kr), kr)
            window.blit(ks, (round(cx + dx * k) - kr, round(cy + dy * k) - kr))

    @staticmethod
    def _icon(window, name, x, y, r, color):
        """印（字は使わない）: ジャンプ＝上向きの山／刀＝斜めの線／手裏剣＝四方の星／ポーズ＝縦の2本"""
        w = max(2, r // 7)
        if name == "jump":
            pygame.draw.lines(window, color, False, ((x - r * 0.4, y + r * 0.2), (x, y - r * 0.3), (x + r * 0.4, y + r * 0.2)), w)
        elif name == "attack":
            pygame.draw.line(window, color, (x - r * 0.4, y + r * 0.4), (x + r * 0.4, y - r * 0.4), w + 1)
        elif name == "throw":
            q = r * 0.45
            pygame.draw.polygon(window, color, ((x, y - q), (x + q * 0.25, y - q * 0.25), (x + q, y), (x + q * 0.25, y + q * 0.25),
                                                (x, y + q), (x - q * 0.25, y + q * 0.25), (x - q, y), (x - q * 0.25, y - q * 0.25)))
        else:
            for dx in (-r * 0.25, r * 0.25):
                pygame.draw.line(window, color, (x + dx, y - r * 0.4), (x + dx, y + r * 0.4), w)
