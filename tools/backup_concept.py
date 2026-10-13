"""assets/concept（リポジトリに入れない、元絵・曲・試作）を、zip にまとめて、Google ドライブに置く。

使い方: python tools/backup_concept.py [置き場所]
  - 置き場所を書かなければ、G:\\マイドライブ（Google ドライブ）に置く。WSL からは G: が見えないので、PowerShell 経由で、読み書きする（zip は、いったん、WSL の一時フォルダに作る）
  - 名前は hiraizumi_concept_年-月-日.zip。同じ日の zip があれば、作り直す。前の日の zip は、消さない
  - zip の中は concept/ から始まる（展開して assets/ に置けば、元に戻る）
  - 前に作った zip と中身が同じなら、作らない（増えたとき・変わったときだけ、置く）
決まり: 絵や曲が増えたら、コミットしてプッシュするときに、これも実行する
"""
import datetime
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "concept")
DEFAULT_DIR = "G:\\マイドライブ"
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


def ps(command):
    """PowerShell で、Windows 側の命令を動かす（G: は、WSL から見えないため）"""
    r = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise SystemExit("PowerShell が失敗しました: %s" % (r.stderr or r.stdout).strip())
    return r.stdout


def win_path(p):
    """WSL の道を、Windows から見える道（\\\\wsl.localhost\\...）にする"""
    return subprocess.run(["wslpath", "-w", p], capture_output=True, text=True).stdout.strip()


def main_windows(dest_dir):
    """G:\\ のような、WSL から見えない置き場所: PowerShell で、前の zip を一時フォルダに取り寄せて比べ、zip を作って、コピーする"""
    tmp = tempfile.mkdtemp(prefix="concept_")
    try:
        names = [n.strip() for n in ps("Get-ChildItem -LiteralPath '%s' -Filter 'hiraizumi_concept_*.zip' | Sort-Object Name | Select-Object -ExpandProperty Name" % dest_dir).splitlines() if n.strip()]
        files = listing(ROOT)
        now = {(n, s) for n, s, _ in files}
        if names:
            old = os.path.join(tmp, "old.zip")
            ps("Copy-Item -LiteralPath '%s' -Destination '%s' -Force" % (dest_dir + "\\" + names[-1], win_path(old)))
            with zipfile.ZipFile(old) as z:
                before = {(i.filename, i.file_size) for i in z.infolist() if not i.is_dir()}
            if before == now:
                print("前の zip（%s）と同じ中身なので、作りません" % names[-1])
                return
            print("増えた・変わった: %d　無くなった: %d" % (len(now - before), len(before - now)))
        name = "hiraizumi_concept_%s.zip" % datetime.date.today().isoformat()
        out = os.path.join(tmp, name)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for n, _, path in files:
                z.write(path, n)
        ps("Copy-Item -LiteralPath '%s' -Destination '%s' -Force" % (win_path(out), dest_dir + "\\" + name))
        print("置きました: %s\\%s（%d ファイル、%.0f MB）" % (dest_dir, name, len(files), os.path.getsize(out) / 1024 / 1024))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(dest_dir):
    if not os.path.isdir(dest_dir) and re.match(r"^[A-Za-z]:\\", dest_dir) and shutil.which("powershell.exe"):
        return main_windows(dest_dir)
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
