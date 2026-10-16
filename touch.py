"""スマホのタッチ操作。画面の左右の帯に、目印を出す（ゲームの絵には重ねない）。
一度でも画面に触ると、目印が出る（キーボード・コントローラで遊ぶ人には、出さない）。

決まった小さな場所を、正確に押さなくてよい作りにする（手元を見ずに遊べるように）:
  左半分＝移動のスティック。触った所が中心になり、指を左右にずらすと歩き、下へずらすと、しゃがむ。
          中心は、指が離れすぎると、ついてくる（反対へ向きを変えるのに、大きく戻さなくてよい）
  右半分＝高さで選ぶ3つの帯。上から、手裏剣・刀・ジャンプ（ジャンプが、いちばん広い）。
          指を滑らせて、別の帯に入ると、そちらが出る。右上の隅だけは、ポーズ（小さい。誤って押さないように）
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
    def pause_rect(ww, wh):
        side = round(wh * C.TOUCH["side"])
        return pygame.Rect(ww - side, 0, side, round(wh * C.TOUCH["cuts"][0]))

    def _action(self, x, y, ww, wh):
        """右半分の (x, y) が、どの帯か（ポーズの隅なら "pause"）"""
        if self.pause_rect(ww, wh).collidepoint(x, y):
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

    # --- 描く（左右の帯の上。帯は黒なので、透明にしなくてよい） ---
    def draw(self, window):
        ww, wh = window.get_size()
        K = C.TOUCH
        side = round(wh * K["side"])
        base, lit, mark = K["color"], K["lit"], K["mark"]
        pressed = {v for v in self.fingers.values() if isinstance(v, str)}
        dirs = self.held()
        # 左の帯: 移動の目印（左右の矢印と、下の矢印）。押している向きは、光る
        cx, cy, s = side // 2, round(wh * 0.62), round(wh * 0.05)
        for name, (vx, vy) in (("left", (-1, 0)), ("right", (1, 0)), ("down", (0, 1))):
            px, py = cx + vx * round(s * 1.6), cy + vy * round(s * 1.6)
            tip = (px + vx * s, py + vy * s)
            wing = ((px - vy * s, py - vx * s), (px + vy * s, py + vx * s))
            pygame.draw.polygon(window, lit if name in dirs else mark, (tip,) + wing)
        pygame.draw.circle(window, base, (cx, cy), max(3, s // 2))
        for f in self.fingers.values():         # 指を置いた所（スティックの中心）を、輪で示す（帯の中にいるときだけ）
            if isinstance(f, Stick) and f.ox < side:
                pygame.draw.circle(window, base, (round(f.ox), round(f.oy)), round(wh * K["stick_max"]), 2)
        # 右の帯: 高さの帯ごとに、印。押している帯は、光る
        rx = ww - side // 2
        for name, (top, bottom) in self.bands(wh).items():
            if name != ACTIONS[0]:
                pygame.draw.line(window, base, (ww - side + 8, top), (ww - 8, top), 1)
            r = min(side // 2 - 8, (bottom - top) // 2 - 6)
            my = (top + bottom) // 2
            on = name in pressed
            pygame.draw.circle(window, lit if on else base, (rx, my), r, 0 if on else max(2, r // 10))
            self._icon(window, name, rx, my, r, (16, 16, 24) if on else mark)
        pr = self.pause_rect(ww, wh)
        r = min(pr.w, pr.h) // 4
        pygame.draw.circle(window, lit if "pause" in pressed else base, pr.center, r, max(2, r // 6))
        self._icon(window, "pause", pr.centerx, pr.centery, r, mark)

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
