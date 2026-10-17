"""順位表（サーバー）との通信。ブラウザ版だけで動く（PC 版・URL が空のときは、何もしない）。
通信そのものは、web_template.tmpl の JavaScript（hzStart・hzSubmit・hzRanking）が行い、結果を window.HZ に置く。Python は、それを読むだけ
（Python から JavaScript の Promise を待つのは確実でないため。日本語は通らないので、送るのは、英数字だけ）。
どの関数も、失敗しても例外を出さない（通信できなくても、ゲームは止めない。記録が、端末の中に残るだけ）。
"""
import json
import sys


def enabled(url):
    return sys.platform == "emscripten" and bool(url)


def _win():
    import platform
    return platform.window


def _read(value):
    """JavaScript が置いた JSON の文字列を、辞書にする。まだ（空）・読めないときは None"""
    try:
        s = str(value)
        return json.loads(s) if s and s not in ("undefined", "null") else None
    except Exception:
        return None


def _call(name, *args):
    try:
        getattr(_win(), name)(*args)
        return True
    except Exception:
        return False


def start(url, level):
    """遊び始めを知らせる（サーバーが、開始の時刻を覚える。返事は、token() で読む）"""
    if enabled(url):
        _call("hzStart", url, level)


def start_state():
    """開始の合図の状態: "ok" / "pending"（まだ返事が無い）/ "fail:理由" / "nobridge"（通信の窓口が無い = 古いページ）。PC 版は "off" """
    if sys.platform != "emscripten":
        return "off"
    try:
        w = _win()
        if not hasattr(w, "hzStart"):
            return "nobridge"
        d = _read(w.HZ.start)
    except Exception:
        return "nobridge"
    if d is None:
        return "pending"
    return "ok" if d.get("ok") and d.get("token") else "fail:" + str(d.get("error"))


def token():
    """いまの遊びの合図（まだ・失敗なら None）"""
    try:
        d = _read(_win().HZ.start)
    except Exception:
        return None
    return d.get("token") if d and d.get("ok") else None


def submit(url, level, name, frames):
    """通しの記録を送る。送れる状態なら True（返事は、submit_result() で読む）"""
    t = token()
    if not (enabled(url) and t):
        return False
    return _call("hzSubmit", url, t, level, name, int(frames))


def submit_result():
    """送った結果: まだ待っている間は None、返事が来たら辞書（{ok: True, rank} か {ok: False, error}）"""
    try:
        return _read(_win().HZ.submit)
    except Exception:
        return None


def ask_name(current):
    """スマホ用: ブラウザの入力欄で、イニシャルを入れてもらう。入れた文字をそのまま返す（やめたとき・できないときは None）。形を整えるのは、呼んだ側"""
    if sys.platform != "emscripten":
        return None
    try:
        _win().hzAskName(current)
        return str(_win().HZ.name)
    except Exception:
        return None


def fetch_ranking(url, level):
    if enabled(url):
        _call("hzRanking", url, level)


def ranking_state(level):
    """順位表の状態: ("pending", None) = まだ返事が無い / ("ok", [{name, frames}, ...]) / ("fail", None) = 取れなかった"""
    try:
        d = _read(getattr(_win().HZ.rank, level))
    except Exception:
        return "pending", None
    if d is None:
        return "pending", None
    return ("ok", d.get("rows") or []) if d.get("ok") else ("fail", None)


def ranking(level):
    """順位表の上位（まだ・失敗なら None）: [{name, frames}, ...]"""
    state, rows = ranking_state(level)
    return rows if state == "ok" else None
