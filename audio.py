"""音（BGM）。音が出せない環境（音声デバイスなし・画面なしのテスト）でも、ゲームは止めない"""
import os
import sys

import pygame

import config as C

DIR = os.path.join(os.path.dirname(__file__), "assets", "audio")
pygame.mixer.pre_init(44100, -16, 2, 2048)    # 出力の溜め（バッファ）を大きく: ブラウザ版で、音がぶつぶつ切れるのを減らす（pygame.init より前に効かせる）


class Audio:
    def __init__(self):
        self.ok = False
        self.playing = None   # いま鳴らしている曲の名前
        self.sounds = {}      # 読み込んだ効果音
        self.gain = (1.0, 1.0)    # 曲と効果音の、音量の倍率（スタート画面のメニューで変える）
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.set_num_channels(24)    # 同時に鳴らせる数（足りないと、音が途中で切られる）
            self.ok = True
        except pygame.error:
            pass   # 音なしで続ける

    def play_bgm(self, name):
        if not self.ok or self.playing == name:
            return
        try:
            pygame.mixer.music.load(os.path.join(DIR, name))
            pygame.mixer.music.set_volume(C.BGM_VOLUMES.get(name, C.BGM_VOLUME) * self.gain[0])
            pygame.mixer.music.play(-1)
            self.playing = name
        except (pygame.error, FileNotFoundError):
            self.ok = False

    def keep_playing(self):
        """曲が終わっていたら、もう一度かける（ブラウザ版で、くり返し再生が効かず、長いボス戦の途中で、曲が止まるため）"""
        if not self.ok or not self.playing or getattr(self, "paused", False):
            return
        try:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    def preload(self, names):
        """効果音を先に読み込む（初めて鳴らす瞬間の読み込みで、フレームが止まって音が途切れるのを防ぐ）"""
        for n in names:
            self._sound(n)

    def _sound(self, name):
        if name not in self.sounds:
            self.sounds[name] = pygame.mixer.Sound(os.path.join(DIR, name))
            self.sounds[name].set_volume(C.SFX_VOLUME.get(name, 0.3) * self.gain[1])
        return self.sounds[name]

    def play_sfx(self, name):
        if not self.ok:
            return
        try:
            self._sound(name).play()
        except (pygame.error, FileNotFoundError):
            pass   # 効果音が鳴らせなくても、続ける

    def set_gain(self, bgm, sfx):
        """曲と効果音の音量の倍率（0〜1）を変える。鳴っている曲と、読み込み済みの効果音にも、すぐ効く"""
        if (bgm, sfx) == self.gain:
            return
        self.gain = (bgm, sfx)
        if not self.ok:
            return
        try:
            if self.playing:
                pygame.mixer.music.set_volume(C.BGM_VOLUMES.get(self.playing, C.BGM_VOLUME) * bgm)
            for name, snd in self.sounds.items():
                snd.set_volume(C.SFX_VOLUME.get(name, 0.3) * sfx)
        except pygame.error:
            pass

    def set_paused(self, on):
        """曲を、止める・続きから鳴らす（ポーズ）"""
        if self.ok and on != getattr(self, "paused", False):
            self.paused = on
            try:
                (pygame.mixer.music.pause if on else pygame.mixer.music.unpause)()
            except pygame.error:
                pass

    def fade_out(self, ms):
        if self.ok and self.playing:
            if sys.platform == "emscripten":    # ブラウザ版: フェード中に次の曲を読むと固まるので、すぐ止める
                pygame.mixer.music.stop()
            else:
                pygame.mixer.music.fadeout(ms)
            self.playing = None
