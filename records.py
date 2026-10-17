"""遊んだ記録（面ごとのベストタイム）。難しさごとに、別々に残す。
ブラウザ版は localStorage（ブラウザの保存領域）、PC 版は records.json に保存する。
読み書きに失敗しても（保存できない環境でも）、ゲームは止めない（記録が残らないだけ）。
時間は、ゲーム内のフレーム数（1秒 = 60）で持つ。
"""
import json
import os
import sys

KEY = "hiraizumi_records_v1"
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "records.json")     # PC 版の保存先（.gitignore）


def _load():
    try:
        if sys.platform == "emscripten":
            import platform
            raw = platform.window.localStorage.getItem(KEY)
            return json.loads(str(raw)) if raw else {}
        with open(PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:       # 無い・壊れている・保存領域が使えない: 記録なしとして続ける
        return {}


def _save(data):
    try:
        text = json.dumps(data, ensure_ascii=False)
        if sys.platform == "emscripten":
            import platform
            platform.window.localStorage.setItem(KEY, text)
        else:
            with open(PATH, "w", encoding="utf-8") as f:
                f.write(text)
    except Exception:
        pass


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
