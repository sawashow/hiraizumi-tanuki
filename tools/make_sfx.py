"""効果音を、計算で作って書き出す（昔のゲーム機の、ノイズと単純な波で作った音の感じ）。

使い方: python tools/make_sfx.py 出力フォルダ [--game] [--ogg assets/audio]
  --game: 遊びの効果音（GAME_SOUNDS。跳ぶ・斬る・拾う・敵・ボス・画面の、40ほど）だけを作る
  --ogg 置き場所: できた wav を、ogg に変換して置く
出力: 出力フォルダ/sfx_thunder.wav（雷鳴）、sfx_sword.wav（刀を抜く「ジャキン」）、sfx_checkpoint.wav（中間地点の音階）、
      sfx_talk_low.wav・sfx_talk_high.wav（せりふの字が出るときの「ピッ」。低いのがボス、高いのがタヌキ侍）
  - ブラウザ版で読めるように、このあと ogg に変換して assets/audio/ に置く（ffmpeg を使う）
  - 乱数の種を固定しているので、何度作っても同じ音になる
"""
import math
import os
import random
import struct
import sys
import wave


def save(path, samples, rate):
    peak = max(abs(v) for v in samples) or 1.0
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"".join(struct.pack("<h", int(v / peak * 0.9 * 32767)) for v in samples))
    print("書き出し:", path, "%.2f秒" % (len(samples) / rate))


def thunder(rate=22050, seconds=3.4):
    """雷鳴: 遠くで鳴る感じ。鋭い一撃は弱めにして、低いゴロゴロが、何度かうねりながら消えていく"""
    rnd = random.Random(7)
    n = int(rate * seconds)
    rolls = [(0.00, 1.00), (0.45, 0.55), (0.95, 0.42), (1.55, 0.30), (2.20, 0.18)]   # (始まる時刻, 強さ)
    out, held, hold_left, low = [], 0.0, 0, 0.0
    for i in range(n):
        t = i / rate
        if hold_left <= 0:      # 同じ値を何サンプルか続ける（時間がたつほど長く = 音が低くなる）
            held = rnd.uniform(-1, 1)
            hold_left = 1 + int(t * 16)
        hold_left -= 1
        env = sum(a * math.exp(-(t - t0) * 3.2) for t0, a in rolls if t >= t0)
        crack = math.exp(-t * 28) * 0.25                # 最初の一撃（弱め。驚かせない）
        k = 0.05 + 0.5 * math.exp(-t * 6)               # こもり具合（だんだん低い音だけ残す）
        low += (held - low) * k
        fade_in = min(1.0, t / 0.06)                    # 出だしを、少しだけ丸める
        out.append((low * env * 1.8 + held * crack) * fade_in)
    return out, rate


def sword(rate=44100, seconds=0.75):
    """刀を抜く音: 短い擦れる音（ジャ）のあと、高い金属の響き（キン）が残る"""
    rnd = random.Random(3)
    n = int(rate * seconds)
    partials = [(2637, 1.0, 9), (3951, 0.7, 11), (5274, 0.5, 13), (7040, 0.35, 16), (9397, 0.2, 20)]   # (高さHz, 強さ, 消える速さ)
    ring_at, out, low = 0.055, [], 0.0
    for i in range(n):
        t = i / rate
        v = 0.0
        if t < 0.09:            # 擦れる音: 高い成分だけのノイズが、強くなって切れる
            noise = rnd.uniform(-1, 1)
            low += (noise - low) * 0.25
            v += (noise - low) * (t / 0.09) ** 2 * 0.9
        if t >= ring_at:
            u = t - ring_at
            for freq, amp, decay in partials:
                wobble = 1 + 0.003 * math.sin(2 * math.pi * 6 * u)
                v += amp * math.exp(-u * decay) * math.sin(2 * math.pi * freq * wobble * u)
        out.append(v)
    return out, rate


def checkpoint(rate=44100, seconds=2.0):
    """中間地点: 琴をつまびくような音が、やわらかく駆け上がり、最後の音に鈴の響きが重なって、余韻が残る。
    音階は、和風の5音（レ・ソ・ラ・レ・ミ）。少し遅れて、こだまが返る"""
    notes = [(587.33, 0.00), (783.99, 0.11), (880.00, 0.22), (1174.66, 0.33), (1318.51, 0.47)]   # (高さHz, 鳴り始め)
    n = int(rate * seconds)
    dry = [0.0] * n
    for k, (freq, start) in enumerate(notes):
        last = k == len(notes) - 1
        for i in range(int(start * rate), n):
            t = i / rate - start
            attack = min(1.0, t / 0.006)
            v = 0.0
            for h, amp in ((1, 1.0), (2, 0.45), (3, 0.22), (4, 0.10)):      # 弦の音: 高い倍音ほど、早く消える
                v += amp * math.exp(-t * (3.2 + h * 2.4)) * math.sin(2 * math.pi * freq * h * t)
            if last:                                                       # 最後の音に、鈴の響き（長く残る）
                v += 0.35 * math.exp(-t * 2.2) * math.sin(2 * math.pi * freq * 2.01 * t)
                v += 0.20 * math.exp(-t * 2.8) * math.sin(2 * math.pi * freq * 3.02 * t)
            dry[i] += v * attack * (0.8 if not last else 1.0)
    delay = int(rate * 0.19)                                               # こだま
    out = list(dry)
    for i in range(delay, n):
        out[i] += dry[i - delay] * 0.32
    for i in range(2 * delay, n):
        out[i] += dry[i - 2 * delay] * 0.12
    fade = int(rate * 0.25)
    for i in range(fade):                                                  # 終わりを、なめらかに消す
        out[n - 1 - i] *= i / fade
    return out, rate


def clang(rate=44100, seconds=0.28):
    """弾かれる音: 石を打ったような、短くて硬い「カン」。高い音が、すぐ消える"""
    rnd = random.Random(11)
    n = int(rate * seconds)
    partials = [(1568, 1.0, 22), (2349, 0.6, 28), (3520, 0.45, 34), (5274, 0.25, 44)]   # (高さHz, 強さ, 消える速さ)
    out, low = [], 0.0
    for i in range(n):
        t = i / rate
        v = sum(a * math.exp(-t * d) * math.sin(2 * math.pi * f * t) for f, a, d in partials)
        noise = rnd.uniform(-1, 1)
        low += (noise - low) * 0.4
        v += (noise - low) * math.exp(-t * 90) * 0.8        # 当たった瞬間の、硬い音
        out.append(v * min(1.0, i / 8))
    return out, rate


def talk(freq, rate=22050, seconds=0.05):
    """せりふの字が1文字出るときの音: 短い四角い波（昔のゲームの、しゃべる音）"""
    n = int(rate * seconds)
    out = []
    for i in range(n):
        t = i / rate
        v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        out.append(v * min(1.0, i / 20) * min(1.0, (n - i) / 200))   # 出だしと終わりを丸める（プチッと鳴らさない）
    return out, rate


# ---------------------------------------------------------------- 遊びの効果音（まとめて作る）
R = 22050


def tone(f0, f1, dur, shape="square", vol=1.0, decay=0.0, vib=0.0, vib_hz=18.0, duty=0.5, attack=0.004):
    """f0 から f1 へ、高さが動く音。shape: square（四角い波）・tri（三角）・saw（のこぎり）・sine。
    decay: 大きいほど、早く消える。vib: 高さの揺れの幅（割合）"""
    n = int(R * dur)
    out, ph = [], 0.0
    for i in range(n):
        t = i / R
        k = i / max(1, n - 1)
        f = (f0 + (f1 - f0) * k) * (1 + vib * math.sin(2 * math.pi * vib_hz * t))
        ph = (ph + f / R) % 1.0
        if shape == "square":
            v = 1.0 if ph < duty else -1.0
        elif shape == "tri":
            v = 4 * abs(ph - 0.5) - 1
        elif shape == "saw":
            v = 2 * ph - 1
        else:
            v = math.sin(2 * math.pi * ph)
        env = min(1.0, t / attack) * math.exp(-t * decay) * min(1.0, (n - i) / (R * 0.008))
        out.append(v * env * vol)
    return out


def hiss(dur, vol=1.0, k0=0.5, k1=0.5, decay=0.0, swell=0.0, seed=1, high=False):
    """ノイズ。k0 → k1: こもり具合（小さいほど、低い音だけ残る）。swell: 出だしが、ゆっくり大きくなる時間。high: 高い成分だけにする"""
    rnd = random.Random(seed)
    n = int(R * dur)
    out, low = [], 0.0
    for i in range(n):
        t = i / R
        w = rnd.uniform(-1, 1)
        low += (w - low) * (k0 + (k1 - k0) * i / max(1, n - 1))
        v = (w - low) if high else low
        env = (min(1.0, t / swell) if swell else min(1.0, t / 0.003)) * math.exp(-t * decay) * min(1.0, (n - i) / (R * 0.01))
        out.append(v * env * vol)
    return out


def mix(*parts):
    """重ねる。(音, 始まる秒) か、音だけを渡す"""
    parts = [p if isinstance(p, tuple) else (p, 0.0) for p in parts]
    out = [0.0] * max(int(at * R) + len(snd) for snd, at in parts)
    for snd, at in parts:
        o = int(at * R)
        for i, v in enumerate(snd):
            out[o + i] += v
    return out


def notes(freqs, step, dur, shape="square", vol=1.0, decay=6.0):
    """音を、step 秒ずつずらして、順に鳴らす（駆け上がる・下がる）"""
    return mix(*[(tone(f, f, dur, shape, vol, decay), k * step) for k, f in enumerate(freqs)])


# 名前 → 音。名前は、config.py の SFX の鍵と同じ（ファイルは sfx_名前.ogg）
GAME_SOUNDS = {
    # 主人公
    "jump": lambda: tone(250, 400, 0.075, "tri", 0.8, 16),     # 何度も鳴るので、短く・低く・丸い音に（四角い波で、高く駆け上がると、しつこい）
    "swing": lambda: hiss(0.12, 1.0, 0.25, 0.7, 14, seed=2, high=True),
    "throw": lambda: mix(hiss(0.07, 0.7, 0.6, 0.9, 30, seed=3, high=True), tone(900, 1500, 0.07, "tri", 0.6, 20)),
    "hit": lambda: mix(hiss(0.07, 1.0, 0.5, 0.2, 40, seed=4), tone(260, 120, 0.08, "square", 0.7, 25)),
    "hurt": lambda: tone(360, 110, 0.24, "saw", 1.0, 5, vib=0.06, vib_hz=28),
    "dead": lambda: mix(notes((440, 370, 311, 247, 185, 123), 0.11, 0.2, "square", 0.8, 5), (hiss(0.5, 0.4, 0.2, 0.05, 5, seed=5), 0.55)),
    "fall": lambda: tone(700, 90, 0.45, "sine", 1.0, 2.5),
    "empty": lambda: mix(tone(150, 130, 0.05, "square", 0.8, 30), (tone(120, 100, 0.06, "square", 0.8, 30), 0.08)),
    "startle": lambda: notes((880, 1320), 0.06, 0.09, "square", 0.7, 12),
    # 拾う・壊す
    "dango": lambda: mix(tone(1320, 1320, 0.05, "tri", 0.9, 20), (tone(1760, 1760, 0.10, "tri", 0.9, 16), 0.05)),
    "heal": lambda: notes((523, 659, 784, 1047), 0.07, 0.16, "tri", 0.9, 9),
    "power": lambda: notes((392, 523, 659, 784, 1047, 1319), 0.05, 0.14, "square", 0.7, 9),
    "break": lambda: mix(hiss(0.30, 1.0, 0.6, 0.12, 9, seed=6), tone(180, 70, 0.18, "tri", 0.8, 10)),
    # ザコ敵
    "die": lambda: mix(tone(520, 90, 0.22, "square", 0.8, 6), hiss(0.2, 0.6, 0.4, 0.1, 12, seed=7)),
    "wave": lambda: mix(tone(560, 220, 0.24, "saw", 0.8, 7), hiss(0.18, 0.4, 0.5, 0.3, 14, seed=8, high=True)),
    "cut": lambda: mix(tone(1900, 2400, 0.09, "sine", 0.9, 22), hiss(0.04, 0.6, 0.8, 0.8, 60, seed=9, high=True)),
    "caw": lambda: mix(tone(760, 520, 0.09, "square", 0.8, 8, duty=0.3), (tone(700, 460, 0.11, "square", 0.8, 8, duty=0.3), 0.13)),
    "dive": lambda: hiss(0.32, 1.0, 0.7, 0.15, 5, swell=0.05, seed=10, high=True),
    "draw": lambda: tone(95, 150, 0.30, "saw", 0.8, 1.5, vib=0.12, vib_hz=34),
    "arrow": lambda: mix(hiss(0.09, 0.8, 0.7, 0.4, 28, seed=11, high=True), tone(820, 300, 0.12, "tri", 0.8, 14)),
    "snap": lambda: mix(hiss(0.05, 1.0, 0.7, 0.3, 60, seed=12), tone(900, 500, 0.04, "square", 0.5, 40)),
    # ボス
    "thud": lambda: mix(tone(110, 38, 0.36, "sine", 1.0, 7), hiss(0.2, 0.7, 0.15, 0.05, 14, seed=13)),
    "boss_wave": lambda: mix(tone(330, 80, 0.42, "saw", 1.0, 4.5), hiss(0.3, 0.5, 0.35, 0.1, 9, seed=14)),
    "leap": lambda: tone(140, 520, 0.26, "square", 0.8, 3, duty=0.3),
    "boss_hit": lambda: mix(tone(170, 80, 0.11, "square", 1.0, 18), hiss(0.09, 0.9, 0.3, 0.1, 30, seed=15)),
    "boss_die": lambda: mix(hiss(1.2, 1.0, 0.2, 0.04, 2.6, seed=16), tone(240, 40, 1.1, "saw", 0.8, 2.2, vib=0.05),
                            (notes((330, 262, 196, 131), 0.16, 0.3, "square", 0.6, 5), 0.1)),
    "roar": lambda: mix(tone(120, 62, 0.9, "saw", 1.0, 1.6, vib=0.10, vib_hz=23), hiss(0.9, 0.6, 0.12, 0.05, 2.5, swell=0.08, seed=17)),
    "thrust": lambda: mix(hiss(0.10, 0.9, 0.5, 0.9, 20, seed=18, high=True), tone(380, 980, 0.11, "saw", 0.7, 12)),
    "fan": lambda: tone(620, 760, 0.22, "tri", 0.9, 5, vib=0.08, vib_hz=26),
    "gust": lambda: hiss(0.65, 1.0, 0.05, 0.35, 2.2, swell=0.22, seed=19),
    "petal": lambda: mix(tone(2100, 1500, 0.10, "sine", 0.8, 18), (tone(2600, 1900, 0.08, "sine", 0.6, 20), 0.05)),
    "bead": lambda: mix(tone(880, 880, 0.16, "sine", 1.0, 14), tone(1760, 1760, 0.10, "sine", 0.4, 22)),
    "ring": lambda: mix(*[(tone(f, f, 0.34, "sine", 0.7, 8), k * 0.015) for k, f in enumerate((660, 880, 1109, 1320))]),
    "charge": lambda: tone(180, 940, 0.62, "tri", 0.9, 0.6, vib=0.03, vib_hz=40),
    "pillar_warn": lambda: mix(tone(1050, 1050, 0.07, "square", 0.7, 8, duty=0.3), (tone(1050, 1050, 0.07, "square", 0.7, 8, duty=0.3), 0.13),
                               (tone(1400, 1400, 0.09, "square", 0.7, 8, duty=0.3), 0.26)),
    "beam": lambda: mix(tone(1500, 160, 0.34, "saw", 1.0, 5), hiss(0.34, 0.8, 0.8, 0.2, 6, seed=20), tone(70, 50, 0.3, "sine", 0.9, 6)),
    "warp": lambda: tone(1700, 260, 0.36, "sine", 0.9, 3, vib=0.20, vib_hz=42),
    "warp_in": lambda: tone(260, 1700, 0.34, "sine", 0.9, 2, vib=0.20, vib_hz=42),
    # 画面
    "select": lambda: tone(880, 990, 0.05, "square", 0.7, 16, duty=0.3),
    "clear": lambda: mix(notes((523, 659, 784, 1047, 784, 1047, 1319), 0.11, 0.30, "square", 0.7, 5),
                         notes((262, 330, 392, 523, 392, 523, 659), 0.11, 0.30, "tri", 0.6, 5)),
    "gameover": lambda: mix(notes((392, 370, 330, 294, 262, 196), 0.22, 0.42, "tri", 0.9, 3.5),
                            notes((196, 185, 165, 147, 131, 98), 0.22, 0.42, "square", 0.4, 3.5)),
}


if __name__ == "__main__":
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    if "--game" not in sys.argv:        # --game を付けると、遊びの効果音だけを作る（もとの6つは、作り直さない）
        save(os.path.join(out_dir, "sfx_thunder.wav"), *thunder())
        save(os.path.join(out_dir, "sfx_sword.wav"), *sword())
        save(os.path.join(out_dir, "sfx_checkpoint.wav"), *checkpoint())
        save(os.path.join(out_dir, "sfx_clang.wav"), *clang())
        save(os.path.join(out_dir, "sfx_talk_low.wav"), *talk(330))
        save(os.path.join(out_dir, "sfx_talk_high.wav"), *talk(660))
    for name, make in GAME_SOUNDS.items():
        save(os.path.join(out_dir, "sfx_%s.wav" % name), make(), R)
    if "--ogg" in sys.argv:             # --ogg 出力先: できた wav を、ogg にして置く（imageio-ffmpeg の ffmpeg を使う）
        import subprocess

        import imageio_ffmpeg
        dst = sys.argv[sys.argv.index("--ogg") + 1]
        for f in sorted(os.listdir(out_dir)):
            if f.endswith(".wav") and ("--game" not in sys.argv or f[4:-4] in GAME_SOUNDS):
                subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", os.path.join(out_dir, f),
                                "-c:a", "libvorbis", "-q:a", "4", os.path.join(dst, f[:-4] + ".ogg")], check=True)
        print("ogg:", dst)
