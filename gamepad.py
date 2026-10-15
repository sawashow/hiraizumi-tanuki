"""コントローラ（ゲームパッド）の入力。挿すと、すぐ使える（起動したあとに挿しても、抜いて挿し直しても大丈夫）。
Xbox・PlayStation・Switch Pro・8BitDo など、SDL が知っているコントローラは、ボタンの名前（A・B・X・Y）で、同じ割り当てになる。
知らないコントローラは、汎用の割り当て（ボタン0・1・2・3、スティック、十字キー）で動かす。
コントローラが使えない環境でも、ゲームは止めない。
ブラウザ版は、汎用の割り当てで動かす（十字キーは、ボタン12〜15）。ブラウザは、ページを開いたあと、ボタンを一度押すまで、コントローラを見つけない。

割り当て:  十字キー・左スティック＝移動／下＝しゃがむ    A＝ジャンプ（決定）    X＝刀    B・Y＝手裏剣（Bは決定も）    Start＝再開（決定）
"""
import sys

import pygame

WEB = sys.platform == "emscripten"   # ブラウザ版（pygbag）で動いているか
WEB_DPAD = {"up": 12, "down": 13, "left": 14, "right": 15}   # ブラウザの「標準の並び」での、十字キーのボタン番号
DEADZONE = 0.45   # スティックを倒したとみなす量（0〜1）

# 「どのボタンを押したら、何になるか」（押した瞬間）。A は、ジャンプと決定（再開）を兼ねる。B（PlayStation の○）も決定にする
PRESS = {
    "A": ("jump", "restart"), "X": ("attack",), "B": ("throw", "restart"), "Y": ("throw",), "START": ("restart", "pause"),
}
RELEASE = {"A": ("jump_release",)}


def stick_held(x, y):
    """スティックの倒し具合（-1〜1）から、押している方向（left / right / up / down）。up は、メニューの項目選びに使う"""
    held = set()
    if x <= -DEADZONE:
        held.add("left")
    if x >= DEADZONE:
        held.add("right")
    if y >= DEADZONE:
        held.add("down")
    if y <= -DEADZONE:
        held.add("up")
    return held


class Pad:
    def __init__(self):
        self.sdl = None            # pygame._sdl2.controller（無ければ None）
        self.pads = {}             # 接続中のコントローラ: instance_id → Controller
        self.fallback = {}         # SDL が知らないコントローラ: instance_id → Joystick
        try:
            from pygame._sdl2 import controller
            controller.init()
            self.sdl = controller
        except Exception:          # ブラウザ版など（コントローラの部品が無い）
            self.sdl = None
        try:
            pygame.joystick.init()
            for i in range(pygame.joystick.get_count()):
                self._open(i)     # すでに挿してあるもの
        except Exception:
            pass
        # 名前（A・B・X・Y）と、pygame のボタン番号の対応
        self.names = {}
        if self.sdl:
            for name, attr in (("A", "CONTROLLER_BUTTON_A"), ("B", "CONTROLLER_BUTTON_B"), ("X", "CONTROLLER_BUTTON_X"),
                               ("Y", "CONTROLLER_BUTTON_Y"), ("START", "CONTROLLER_BUTTON_START"),
                               ("UP", "CONTROLLER_BUTTON_DPAD_UP"), ("DOWN", "CONTROLLER_BUTTON_DPAD_DOWN"),
                               ("LEFT", "CONTROLLER_BUTTON_DPAD_LEFT"), ("RIGHT", "CONTROLLER_BUTTON_DPAD_RIGHT")):
                self.names[getattr(pygame, attr, -999)] = name

    # --- 接続・取り外し ---
    def _open(self, index):
        try:
            if self.sdl and self.sdl.is_controller(index):
                c = self.sdl.Controller(index)
                self.pads[c.as_joystick().get_instance_id()] = c
            else:
                j = pygame.joystick.Joystick(index)
                self.fallback[j.get_instance_id()] = j
        except Exception:
            pass

    def _close(self, instance_id):
        self.pads.pop(instance_id, None)
        self.fallback.pop(instance_id, None)

    @property
    def connected(self):
        return bool(self.pads or self.fallback)

    # --- イベントから、「このフレームに押した」ものを返す ---
    def handle(self, event):
        t = event.type
        if t in (getattr(pygame, "CONTROLLERDEVICEADDED", -1), getattr(pygame, "JOYDEVICEADDED", -1)):
            index = getattr(event, "device_index", None)
            if index is not None and not self._already(index):
                self._open(index)
            return set()
        if t in (getattr(pygame, "CONTROLLERDEVICEREMOVED", -1), getattr(pygame, "JOYDEVICEREMOVED", -1)):
            self._close(getattr(event, "instance_id", None))
            return set()
        if t == getattr(pygame, "CONTROLLERBUTTONDOWN", -1):
            return set(PRESS.get(self.names.get(event.button), ()))
        if t == getattr(pygame, "CONTROLLERBUTTONUP", -1):
            return set(RELEASE.get(self.names.get(event.button), ()))
        if t in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP) and getattr(event, "instance_id", None) in self.fallback:
            name = {0: "A", 1: "B", 2: "X", 3: "Y", 7: "START", 9: "START"}.get(event.button)   # 汎用の割り当て
            table = PRESS if t == pygame.JOYBUTTONDOWN else RELEASE
            return set(table.get(name, ()))
        return set()

    def _already(self, index):
        try:
            iid = pygame.joystick.Joystick(index).get_instance_id()
        except Exception:
            return False
        return iid in self.pads or iid in self.fallback

    # --- 押している間の方向 ---
    def held(self):
        out = set()
        for c in list(self.pads.values()):
            try:
                x = c.get_axis(pygame.CONTROLLER_AXIS_LEFTX) / 32767
                y = c.get_axis(pygame.CONTROLLER_AXIS_LEFTY) / 32767
                out |= stick_held(x, y)
                if c.get_button(pygame.CONTROLLER_BUTTON_DPAD_LEFT):
                    out.add("left")
                if c.get_button(pygame.CONTROLLER_BUTTON_DPAD_RIGHT):
                    out.add("right")
                if c.get_button(pygame.CONTROLLER_BUTTON_DPAD_DOWN):
                    out.add("down")
                if c.get_button(pygame.CONTROLLER_BUTTON_DPAD_UP):
                    out.add("up")
            except Exception:
                pass
        for j in list(self.fallback.values()):
            try:
                x, y = (j.get_axis(0), j.get_axis(1)) if j.get_numaxes() >= 2 else (0.0, 0.0)
                out |= stick_held(x, y)
                if j.get_numhats():
                    hx, hy = j.get_hat(0)
                    if hx:
                        out.add("right" if hx > 0 else "left")
                    if hy:
                        out.add("down" if hy < 0 else "up")
                if WEB and j.get_numbuttons() >= 16:    # ブラウザ: 十字キーは、ボタン12〜15（上・下・左・右）で届く
                    if j.get_button(WEB_DPAD["down"]):
                        out.add("down")
                    if j.get_button(WEB_DPAD["up"]):
                        out.add("up")
                    if j.get_button(WEB_DPAD["left"]):
                        out.add("left")
                    if j.get_button(WEB_DPAD["right"]):
                        out.add("right")
            except Exception:
                pass
        if "left" in out and "right" in out:    # 左右が同時なら、どちらも無効
            out -= {"left", "right"}
        return out
