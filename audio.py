"""音（BGM）。音が出せない環境（音声デバイスなし・画面なしのテスト）でも、ゲームは止めない"""
import os

import pygame

import config as C

DIR = os.path.join(os.path.dirname(__file__), "assets", "audio")


class Audio:
    def __init__(self):
        self.ok = False
        self.playing = None   # いま鳴らしている曲の名前
        self.sounds = {}      # 読み込んだ効果音
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.ok = True
        except pygame.error:
            pass   # 音なしで続ける

    def play_bgm(self, name):
        if not self.ok or self.playing == name:
            return
        try:
            pygame.mixer.music.load(os.path.join(DIR, name))
            pygame.mixer.music.set_volume(C.BGM_VOLUMES.get(name, C.BGM_VOLUME))
            pygame.mixer.music.play(-1)
            self.playing = name
        except (pygame.error, FileNotFoundError):
            self.ok = False

    def play_sfx(self, name):
        if not self.ok:
            return
        try:
            if name not in self.sounds:
                self.sounds[name] = pygame.mixer.Sound(os.path.join(DIR, name))
                self.sounds[name].set_volume(C.SFX_VOLUME.get(name, 0.3))
            self.sounds[name].play()
        except (pygame.error, FileNotFoundError):
            pass   # 効果音が鳴らせなくても、続ける

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
            pygame.mixer.music.fadeout(ms)
            self.playing = None
