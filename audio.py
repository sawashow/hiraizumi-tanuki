"""音（BGM）。音が出せない環境（音声デバイスなし・画面なしのテスト）でも、ゲームは止めない"""
import os

import pygame

import config as C

DIR = os.path.join(os.path.dirname(__file__), "assets", "audio")


class Audio:
    def __init__(self):
        self.ok = False
        self.playing = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.ok = True
        except pygame.error:
            pass   # 音なしで続ける

    def play_bgm(self, name):
        if not self.ok or self.playing:
            return
        try:
            pygame.mixer.music.load(os.path.join(DIR, name))
            pygame.mixer.music.set_volume(C.BGM_VOLUME)
            pygame.mixer.music.play(-1)
            self.playing = True
        except (pygame.error, FileNotFoundError):
            self.ok = False

    def fade_out(self, ms):
        if self.ok and self.playing:
            pygame.mixer.music.fadeout(ms)
            self.playing = False
