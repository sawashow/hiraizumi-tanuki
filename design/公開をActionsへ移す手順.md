# 公開を GitHub Actions へ移す手順

## なぜ移すか

いまは、公開のたびに、ブラウザ版（`docs/web.tar.gz`。約7.6MB）をコミットしている。
2026-10-16 時点で33回コミットし、リポジトリは約170MB（size-pack）になった。この先も、公開するたびに太り続ける。

Actions に移すと、次のようになる。

- push すると、GitHub 側でブラウザ版を作り、そのまま Pages に公開する。`web.tar.gz` は、コミットしない。
- 手元での `pygbag --build` と、`docs/` へのコピーが要らなくなる。
- 公開の URL（https://hiraizumi-tanuki.ponpoco-works.com/）は変わらない。

## いまの状態（2026-10-16）

- Pages: `build_type=legacy`。`main` の `/docs` から公開している。独自ドメインは `hiraizumi-tanuki.ponpoco-works.com`。HTTPS は強制済み。
- 手元のビルド: Python 3.13.5、pygbag 0.9.3。
  ビルドの命令は `PYTHONUTF8=1 python -m pygbag --build --PYBUILD 3.12 --template tools/web_template.tmpl web`。
- ゲームのファイルを `web/` へ集めるのは、`tools/build_web.py` の役目。

## 手順

### 1. ワークフローを作る（`.github/workflows/pages.yml`）

- きっかけ: `main` への push。ただし、ゲームの中身に関わるパスが変わったときだけ動かす。
  - 対象: `*.py`、`assets/images/**`、`assets/audio/**`、`tools/build_web.py`、`tools/web_template.tmpl`
  - 手で動かせるように、`workflow_dispatch` も付ける。
- 仕事の流れ:
  1. `actions/checkout`
  2. `actions/setup-python`（3.13。手元と同じ版）
  3. `pip install pygbag==0.9.3`（手元と同じ版に固定する）
  4. `python tools/build_web.py`
  5. `PYTHONUTF8=1 python -m pygbag --build --PYBUILD 3.12 --template tools/web_template.tmpl web`
  6. `web/build/web` の `index.html`・`web.tar.gz`・`favicon.png` と、`docs/CNAME`・`.nojekyll` を `_site/` に集める
  7. `actions/upload-pages-artifact`（`_site`）
  8. `actions/deploy-pages`
- 権限: `pages: write`、`id-token: write`、`contents: read`
- 同時に2つ走らないように: `concurrency: pages`

### 2. ワークフローだけを push して、成功するか確かめる

- **この時点では、まだ Pages の設定は変えない。**
  ワークフローの「公開する」部分は、設定を変えるまで失敗する。そこで、まず次の2つで、作る部分だけを確かめる。
  - deploy を外したワークフローを試しに走らせる。
  - 出来上がった `web.tar.gz` を、Actions の成果物として手元に落とす。
- 確かめること:
  - pygbag が、GitHub 側で、日本語のソースを読めるか（`PYTHONUTF8=1`）。
  - ビルドの途中で、ネットから部品を取りに行って失敗しないか。
  - 出来た `web.tar.gz` が、手元で作ったものと同じくらいの大きさか（約7.6MB）。

### 3. Pages の公開元を、Actions に切り替える

- `gh api -X PUT repos/sawashow/hiraizumi-tanuki/pages -f build_type=workflow`
- 独自ドメインと HTTPS が残っているかを、`gh api repos/sawashow/hiraizumi-tanuki/pages` で確かめる。
  消えていたら、設定し直す。
- **外向きの変更なので、実行の前にユーザーに確認する。**

### 4. 公開して、確かめる

- ワークフローを走らせる（push か、手で動かす）。
- 本番の `web.tar.gz` の大きさが、Actions の成果物と同じかを確かめる（`curl -sI`）。
- 本番のページをブラウザで開いて、パソコンの大きさと、スマホの大きさ（667×375）で、画面を見る。

### 5. 後片付け

- `docs/` の `index.html`・`web.tar.gz`・`favicon.png` を、git から外す（`git rm`）。
  `CNAME` は、ワークフローが使うので残すか、ワークフローの中に書く。
- `tools/build_web.py` の先頭の説明を、新しい公開の流れに書き直す。
- `AI_CONTEXT.md` の「公開」の記述と、設計上の決定事項を更新する。

## 別に相談すること（今回はやらない）

**過去の履歴から、`docs/web.tar.gz` を消して、リポジトリを小さくする（約170MB → 数十MB の見込み）。**

- やり方: `git filter-repo`（または BFG）で、過去のコミットからも消し、強制 push する。
- 公開リポジトリの履歴の書き換えになる。コミットの番号が全部変わり、ほかの場所の写し（clone）とも合わなくなる。
- **必ずユーザーの合意を得てから行う。**

## 戻し方（うまくいかなかったとき）

- `gh api -X PUT repos/sawashow/hiraizumi-tanuki/pages -f build_type=legacy -f "source[branch]=main" -f "source[path]=/docs"` で、いまの公開の方法に戻す。
- `docs/` のファイルは、手順5までは消さない。消すまでは、いつでも戻せる。
