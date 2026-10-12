"""assets/concept（リポジトリに入れない、元絵・曲・試作）を、zip にまとめて、Google ドライブに置く。

使い方: python tools/backup_concept.py [置き場所]
  - 置き場所を書かなければ、I:\\マイドライブ（Google ドライブ）に置く
  - 名前は hiraizumi_concept_年-月-日.zip。同じ日の zip があれば、作り直す。前の日の zip は、消さない
  - zip の中は concept/ から始まる（展開して assets/ に置けば、元に戻る）
  - 前に作った zip と中身が同じなら、作らない（増えたとき・変わったときだけ、置く）
決まり: 絵や曲が増えたら、コミットしてプッシュするときに、これも実行する
"""
import datetime
import glob
import os
import sys
import zipfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "concept")
DEFAULT_DIR = "I:\\マイドライブ"
SKIP_DIRS = {"__pycache__"}


def listing(root):
    """(zip の中の名前, 大きさ) の一覧"""
    out = []
    for folder, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            path = os.path.join(folder, name)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            out.append(("concept/" + rel, os.path.getsize(path), path))
    return out


def main(dest_dir):
    if not os.path.isdir(dest_dir):
        raise SystemExit("置き場所が見つかりません: %s（Google ドライブが動いているか、確かめてください）" % dest_dir)
    files = listing(ROOT)
    now = {(n, s) for n, s, _ in files}
    old = sorted(glob.glob(os.path.join(dest_dir, "hiraizumi_concept_*.zip")))
    if old:
        with zipfile.ZipFile(old[-1]) as z:
            before = {(i.filename, i.file_size) for i in z.infolist() if not i.is_dir()}
        if before == now:
            print("前の zip（%s）と同じ中身なので、作りません" % os.path.basename(old[-1]))
            return
        print("増えた・変わった: %d　無くなった: %d" % (len(now - before), len(before - now)))
    out = os.path.join(dest_dir, "hiraizumi_concept_%s.zip" % datetime.date.today().isoformat())
    tmp = out + ".part"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for name, _, path in files:
            z.write(path, name)
    os.replace(tmp, out)
    print("置きました: %s（%d ファイル、%.0f MB）" % (out, len(files), os.path.getsize(out) / 1024 / 1024))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DIR)
