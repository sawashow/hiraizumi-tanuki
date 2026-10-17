"""遊んだ記録（面ごとのベストタイム）。難しさごとに、別々に残す。
ブラウザ版は localStorage（ブラウザの保存領域）、PC 版は records.json に保存する。
読み書きに失敗しても（保存できない環境でも）、ゲームは止めない（記録が残らないだけ）。
時間は、ゲーム内のフレーム数（1秒 = 60）で持つ。
"""
import base64
import json
import os
import sys

KEY = "hiraizumi_records_v2"       # v1 は、日本語が化けた古いデータ（読まない）
status = "ok"       # 最後の保存・読み込みの結果（"ok" 以外は、RECORDS に出す。原因を見つけるため）
NAME_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"     # イニシャルに使える文字
TOTAL = "通し"       # 4面を続けて遊んだ、合計タイムの記録の名前（面の名前と同じように、level の下に残す）
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "records.json")     # PC 版の保存先（.gitignore）


def _encode(data):
    """辞書を、英数字と - _ = だけの文字列にする（base64）。引用符・バックスラッシュ・日本語を含むと、ブラウザの保存領域へ渡す途中で、壊れるおそれがあるため"""
    return base64.urlsafe_b64encode(json.dumps(data).encode("ascii")).decode("ascii")


def _decode(text):
    return json.loads(base64.urlsafe_b64decode(text.encode("ascii")).decode("ascii"))


def _load():
    global status
    try:
        if sys.platform == "emscripten":
            import platform
            raw = platform.window.localStorage.getItem(KEY)
            s = str(raw)
            return {} if raw is None or s in ("", "null", "undefined", "None") else _decode(s)
        with open(PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:       # 壊れている・保存領域が使えない: 記録なしとして続ける
        status = "READ ERROR"
        return {}


def _save(data):
    global status
    try:
        if sys.platform == "emscripten":
            import platform
            text = _encode(data)
            platform.window.localStorage.setItem(KEY, text)
            status = "ok" if str(platform.window.localStorage.getItem(KEY)) == text else "WRITE MISMATCH"       # 読み戻して、確かめる
        else:
            with open(PATH, "w", encoding="utf-8") as f:
                f.write(json.dumps(data))
            status = "ok"
    except Exception:
        status = "WRITE ERROR"


def can_save():
    """記録を保存して、読み戻せるか（保存領域が使えない環境 = シークレットモードなどでは False。RECORDS に注意を出す）"""
    try:
        if sys.platform == "emscripten":
            import platform
            ls = platform.window.localStorage
            ls.setItem(KEY + "_check", "ok")
            return str(ls.getItem(KEY + "_check")) == "ok"
        return True
    except Exception:
        return False


def last_name():
    """前に入れたイニシャル（3文字。無い・おかしいときは AAA）"""
    n = _load().get("name")
    return n if isinstance(n, str) and len(n) == 3 and all(c in NAME_CHARS for c in n) else "AAA"


def set_name(name):
    data = _load()
    data["name"] = name
    _save(data)


SCORE = "score"       # スコアの記録の名前（level の下に、最高点を残す。タイムと違って、大きいほどよい）


def best_score(level):
    v = _load().get(level, {}).get(SCORE)
    return v if isinstance(v, int) and v > 0 else None


def submit_score(level, points):
    """今回のスコアを、最高点と比べて、高ければ保存する。(いまの最高点, 更新したか) を返す"""
    data = _load()
    now = data.get(level, {}).get(SCORE)
    if not (isinstance(now, int) and now > 0) or points > now:
        data.setdefault(level, {})[SCORE] = int(points)
        _save(data)
        return int(points), True
    return now, False


def best(level, stage):
    """level（easy など）・stage（面の名前）の、ベストのフレーム数。まだ無ければ None"""
    v = _load().get(level, {}).get(stage)
    return v if isinstance(v, int) and v > 0 else None


def submit(level, stage, frames):
    """今回のフレーム数を、ベストと比べて、速ければ保存する。(いまのベスト, 更新したか) を返す"""
    data = _load()
    now = data.get(level, {}).get(stage)
    if not (isinstance(now, int) and now > 0) or frames < now:
        data.setdefault(level, {})[stage] = int(frames)
        _save(data)
        return int(frames), True
    return now, False


def fmt(frames):
    """フレーム数を、分:秒.百分の1秒 にする（None は、記録なし）"""
    if frames is None:
        return "-:--.--"
    return "%d:%02d.%02d" % (frames // 3600, frames // 60 % 60, frames % 60 * 100 // 60)
