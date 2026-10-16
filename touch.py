"""スマホのタッチ操作。画面の左右の帯に、ボタンを出す（ゲームの絵には重ねない）。
一度でも画面に触ると、ボタンが出る（キーボード・コントローラで遊ぶ人には、出さない）。

並び:  左の帯＝十字キー（↑↓←→。指を滑らせて、向きを変えられる）
      右の帯＝上から、手裏剣・刀・ジャンプ（互い違い）、いちばん上に、ポーズ
ゲームの絵は、窓から左右の帯を除いた所に、16:9 のまま、できるだけ大きく出す（config.TOUCH の side が、帯の幅）。
コントローラ（gamepad.py）と同じく、「このフレームに押したもの」（handle）と「押している方向」（held）を返す。
"""
import math

import pygame

import config as C

# ボタンを押した瞬間に、何になるか（コントローラの A・X・B・START と同じ）。ジャンプは、決定も兼ねる
PRESS = {"jump": ("jump", "restart"), "attack": ("attack",), "throw": ("throw",), "pause": ("restart", "pause")}
RELEASE = {"jump": ("jump_release",)}


class Touch:
    def __init__(self):
        self.active = False     # 一度でも触ったら、ボタンを出す
        self.fingers = {}       # 指の番号 → いま押しているもの（"jump" など。十字キーは、方向の集まり）

    # --- 並び（窓の大きさから、毎回計算する） ---
    @staticmethod
    def game_rect(ww, wh):
        """ゲームの絵を出す所: 左右の帯を除いた所に、16:9 で、できるだけ大きく"""
        side = round(wh * C.TOUCH["side"])
        k = min((ww - 2 * side) / C.BASE_W, wh / C.BASE_H)
        w, h = round(C.BASE_W * k), round(C.BASE_H * k)
        return pygame.Rect((ww - w) // 2, (wh - h) // 2, w, h)

    @staticmethod
    def buttons(ww, wh):
        """ボタンの、中心と半径: {名前: (x, y, r)}。十字キーは "dpad"（中心と、外側の半径）"""
        side = round(wh * C.TOUCH["side"])
        u = wh                      # 大きさの物差し（窓の高さ）
        lx, rx = side // 2, ww - side // 2
        r = round(u * C.TOUCH["button"])
        s = round(r * 0.35)         # 互い違いのずれ（縦に並べて、親指を滑らせやすく）
        return {
            "dpad": (lx, round(u * 0.62), min(round(u * C.TOUCH["dpad"]), side // 2 - 4)),
            "throw": (rx + s, round(u * 0.36), r),          # 右の帯: 上から、手裏剣・刀・ジャンプ（いちばん押す物を、いちばん下に）
            "attack": (rx - s, round(u * 0.58), r),
            "jump": (rx + s, round(u * 0.80), r),
            "pause": (rx, round(u * 0.10), round(r * 0.5)),
        }

    def _hit(self, x, y, ww, wh):
        """窓の上の (x, y) に、何があるか。十字キーは、方向の集まり（frozenset）。何も無ければ None"""
        bs = self.buttons(ww, wh)
        cx, cy, R = bs["dpad"]
        dx, dy = x - cx, y - cy
        if math.hypot(dx, dy) <= R * C.TOUCH["reach"]:      # 十字キー: 中心からの角度で、向きを決める（斜めは、2つ）
            dirs = set()
            if math.hypot(dx, dy) > R * 0.18:
                a = math.degrees(math.atan2(-dy, dx)) % 360
                if a < 60 or a > 300:
                    dirs.add("right")
                if 120 < a < 240:
                    dirs.add("left")
                if 30 < a < 150:
                    dirs.add("up")
                if 210 < a < 330:
                    dirs.add("down")
            return frozenset(dirs)
        best = None
        for name in ("jump", "attack", "throw", "pause"):
            bx, by, r = bs[name]
            d = math.hypot(x - bx, y - by)
            if d <= r * C.TOUCH["reach"] and (best is None or d < best[0]):     # 少し外れても、近いボタンを押したことにする
                best = (d, name)
        return best and best[1]

    # --- イベントから、「このフレームに押した」ものを返す ---
    def handle(self, event, size):
        t = event.type
        if t not in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
            return set()
        self.active = True
        ww, wh = size
        out = set()
        before = self.fingers.get(event.finger_id)
        now = None if t == pygame.FINGERUP else self._hit(event.x * ww, event.y * wh, ww, wh)
        if t == pygame.FINGERMOTION and isinstance(before, str) and now != before:
            now = before        # ボタンから指がずれても、離すまでは、押したまま（十字キーだけ、滑らせて向きを変える）
        if now != before:
            if isinstance(before, str):
                out |= set(RELEASE.get(before, ()))
            if isinstance(now, str):
                out |= set(PRESS.get(now, ()))
        if now is None:
            self.fingers.pop(event.finger_id, None)
        else:
            self.fingers[event.finger_id] = now
        return out

    def held(self):
        out = set()
        for v in self.fingers.values():
            if isinstance(v, frozenset):
                out |= v
        if "left" in out and "right" in out:
            out -= {"left", "right"}
        return out

    # --- 描く（左右の帯の上。帯は黒なので、透明にしなくてよい） ---
    def draw(self, window):
        ww, wh = window.get_size()
        bs = self.buttons(ww, wh)
        on = set(self.held()) | {v for v in self.fingers.values() if isinstance(v, str)}
        base, lit, mark = C.TOUCH["color"], C.TOUCH["lit"], C.TOUCH["mark"]
        cx, cy, R = bs["dpad"]
        pygame.draw.circle(window, base, (cx, cy), R, max(2, R // 14))
        s = round(R * 0.32)
        for name, (vx, vy) in (("up", (0, -1)), ("down", (0, 1)), ("left", (-1, 0)), ("right", (1, 0))):
            px, py = cx + vx * round(R * 0.62), cy + vy * round(R * 0.62)
            tip = (px + vx * s, py + vy * s)
            wing = ((px - vy * s - vx * s // 2, py - vx * s - vy * s // 2), (px + vy * s - vx * s // 2, py + vx * s - vy * s // 2))
            pygame.draw.polygon(window, lit if name in on else mark, (tip,) + wing)
        for name in ("jump", "attack", "throw", "pause"):
            bx, by, r = bs[name]
            pygame.draw.circle(window, lit if name in on else base, (bx, by), r, 0 if name in on else max(2, r // 10))
            self._icon(window, name, bx, by, r, (16, 16, 24) if name in on else mark)

    @staticmethod
    def _icon(window, name, x, y, r, color):
        """ボタンの印（字は使わない）: ジャンプ＝上向きの山／刀＝斜めの線／手裏剣＝四方の星／ポーズ＝縦の2本"""
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
