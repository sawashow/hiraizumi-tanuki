"""ブラウザ版（pygbag）用に、ゲームに必要なファイルだけを web/ にコピーする。

使い方: python tools/build_web.py
  web/ には main.py・config.py・sprites.py と assets/images だけを置く（元絵や試作の画像は入れない）。
  そのあと `pygbag web` で手元のサーバーが立ち、http://localhost:8000 で遊べる。

公開は、main へ push すると GitHub Actions（.github/workflows/pages.yml）が自動で行う。
  Actions は、このスクリプトのあとに次を実行する（日本語を含むので Python を UTF-8 モードで動かす）:
  PYTHONUTF8=1 python -m pygbag --build --PYBUILD 3.12 --template tools/web_template.tmpl web
  web/build/web の index.html・web.tar.gz・favicon.png を公開する。web.tar.gz はコミットしない
  ※ web.apk は itch.io に上げるときだけ使う。公開物には入れない
"""
import os
import shutil

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "web")

shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(os.path.join(OUT, "assets", "images"))
for name in ("main.py", "config.py", "sprites.py", "stage.py", "audio.py", "gamepad.py", "splash.py", "touch.py", "records.py"):
    shutil.copy(os.path.join(ROOT, name), OUT)
src_images = os.path.join(ROOT, "assets", "images")
for dirpath, _, files in os.walk(src_images):
    for f in files:
        if f.endswith(".png") and "sheet" not in f:   # 確認用の一覧画像は入れない
            rel = os.path.relpath(dirpath, src_images)
            dst = os.path.join(OUT, "assets", "images", rel)
            os.makedirs(dst, exist_ok=True)
            shutil.copy(os.path.join(dirpath, f), dst)
shutil.copytree(os.path.join(ROOT, "assets", "audio"), os.path.join(OUT, "assets", "audio"))   # BGM（ogg）
n = sum(len(fs) for _, _, fs in os.walk(os.path.join(OUT, "assets", "images")))
size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
print("画像 %d 枚、合計 %.0f KB" % (n, size / 1024))
