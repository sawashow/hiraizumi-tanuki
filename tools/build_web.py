"""ブラウザ版（pygbag）用に、ゲームに必要なファイルだけを web/ にコピーする。

使い方: python tools/build_web.py
  web/ には main.py・config.py・sprites.py と assets/images だけを置く（元絵や試作の画像は入れない）。
  そのあと `pygbag web` で手元のサーバーが立ち、http://localhost:8000 で遊べる。
"""
import os
import shutil

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "web")

shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(os.path.join(OUT, "assets", "images"))
for name in ("main.py", "config.py", "sprites.py"):
    shutil.copy(os.path.join(ROOT, name), OUT)
for f in os.listdir(os.path.join(ROOT, "assets", "images")):
    if f.endswith(".png") and "sheet" not in f:   # 確認用の一覧画像は入れない
        shutil.copy(os.path.join(ROOT, "assets", "images", f), os.path.join(OUT, "assets", "images"))
n = len(os.listdir(os.path.join(OUT, "assets", "images")))
size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
print("画像 %d 枚、合計 %.0f KB" % (n, size / 1024))
