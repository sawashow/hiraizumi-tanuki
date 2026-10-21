"""公開物（_site）から、itch.io に上げる zip を作る。

使い方: python tools/make_itch_zip.py _site itch.zip
  _site には、index.html・web.tar.gz・favicon.png と、後読みの曲（config.BGM_LATE）がある（pages.yml が作る）。
  itch.io の遊ぶ場所（*.itch.zone）では、テンプレートが web.tar.gz ではなく web.apk（zip）を読む。
  そこで、web.tar.gz の中身を同じ並びで zip に詰め替えて web.apk にする。
  zip の中身: index.html・web.apk・favicon.png・後読みの曲（web.tar.gz は入れない）
上げるのは、pages.yml の butler の手順。
"""
import io
import os
import sys
import tarfile
import zipfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
import config as C

site, out = sys.argv[1], sys.argv[2]

apk = io.BytesIO()
with tarfile.open(os.path.join(site, "web.tar.gz"), "r:gz") as tar, zipfile.ZipFile(apk, "w", zipfile.ZIP_DEFLATED) as z:
    for m in tar.getmembers():
        if m.isfile():
            z.writestr(m.name, tar.extractfile(m).read())

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(site, "index.html"), "index.html")
    z.write(os.path.join(site, "favicon.png"), "favicon.png")
    z.writestr("web.apk", apk.getvalue())
    for name in C.BGM_LATE:     # 1曲でも欠けたら、ここで失敗にする
        z.write(os.path.join(site, name), name)

with zipfile.ZipFile(out) as z:
    for i in z.infolist():
        print("%-18s %9d" % (i.filename, i.file_size))
