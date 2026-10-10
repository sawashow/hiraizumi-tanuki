"""効果音を、計算で作って書き出す（昔のゲーム機の、ノイズと単純な波で作った音の感じ）。

使い方: python tools/make_sfx.py 出力フォルダ
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


def talk(freq, rate=22050, seconds=0.05):
    """せりふの字が1文字出るときの音: 短い四角い波（昔のゲームの、しゃべる音）"""
    n = int(rate * seconds)
    out = []
    for i in range(n):
        t = i / rate
        v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        out.append(v * min(1.0, i / 20) * min(1.0, (n - i) / 200))   # 出だしと終わりを丸める（プチッと鳴らさない）
    return out, rate


if __name__ == "__main__":
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    save(os.path.join(out_dir, "sfx_thunder.wav"), *thunder())
    save(os.path.join(out_dir, "sfx_sword.wav"), *sword())
    save(os.path.join(out_dir, "sfx_checkpoint.wav"), *checkpoint())
    save(os.path.join(out_dir, "sfx_talk_low.wav"), *talk(330))
    save(os.path.join(out_dir, "sfx_talk_high.wav"), *talk(660))
