# 順位表のサーバー（GAS）

通しのタイムを、集めて、順位にする。Google Apps Script の Web アプリ + スプレッドシート。
コードは `Code.gs`、公開の設定は `appsscript.json`（誰でも呼べる Web アプリ・自分の権限で動く）。
`clasp`（Apps Script をコマンドで扱う道具）で、送って・公開する。

## はじめて公開する（1回だけ）

1. 準備（初回のみ）
   ```
   npm install -g @google/clasp
   clasp login
   ```
   さらに、https://script.google.com/home/usersettings で、**「Google Apps Script API」をオン**にする。
2. スプレッドシートと、そこに結びついたスクリプトを作る
   ```
   cd server/gas
   clasp create --type sheets --title "平泉タヌキ侍 順位表" --rootDir .
   ```
   `.clasp.json` ができる（スクリプトの ID。`.gitignore` 済み）。
3. コードを送る（`appsscript.json` も、このリポジトリのもので上書きする）
   ```
   clasp push -f
   ```
4. 一度だけ、権限を許可する（スプレッドシートに書くため）
   ```
   clasp open-script
   ```
   エディタが開く。上のメニューの関数の選択で `setup` を選んで「実行」→ 権限の確認が出たら許可する（記録のシート `scores` も、ここでできる）。
5. Web アプリとして公開する（**エディタで行う。`clasp deploy` は使わない**: Web アプリではなく「ライブラリ」として作られて、URL が 404 になる）
   - `clasp open-script` でエディタを開き、右上の「デプロイ」→「新しいデプロイ」→ 歯車で「ウェブアプリ」。
   - 次のユーザーとして実行: **自分** / アクセスできるユーザー: **全員** → 「デプロイ」。
   - 出てきた **ウェブアプリの URL**（`https://script.google.com/macros/s/<デプロイ ID>/exec`）を、`config.py` の `ONLINE` に書く。
6. 動作を確かめる（ブラウザで、次の URL を開く。`{"ok":true,"rows":[]}` が出れば成功。失敗したら、数秒おいて、もう一度）
   ```
   https://script.google.com/macros/s/<デプロイ ID>/exec?action=ranking&level=easy
   ```

## 直したとき（URL は、変えない）

1. `clasp push`（コードを送る）
2. エディタ（`clasp open-script`）で、「デプロイ」→「デプロイを管理」→ 鉛筆 → バージョンを「新バージョン」→「デプロイ」。

**`clasp deploy`（`-i` 付きも）は、使わない。** Web アプリの設定が外れて、「ライブラリ」になり、URL が 404 を返す（2026-10-18 に、2回起きた）。
なお、起動直後の最初の呼び出しが、一時的に失敗することがある（`bad request` や 404）。ゲーム側は、通信の失敗を、最大3回くり返す。

## 確認

`node server/gas/test_check.js`（記録のチェックの処理を、GAS の外で試す）。

## 決めごと（`Code.gs` の先頭）

- 順位表は、難しさ（easy / normal / hard）ごとに、上位 20 件。各難しさで、200 件まで残す。
- あり得ない速さの通しは弾く（`MIN_FRAMES`。EASY 2:30・NORMAL と HARD は 3:30。実際の最速を知ったら見直す）。
- 開始の合図（トークン）から、送信までの実時間が、フレーム数 ÷ 60 より短い記録は、弾く。
- 名前は、半角英大文字と数字の3文字。使えない名前は `NG_NAMES`。
- 順位の取得は、60秒、使い回す（スプレッドシートの読み込みを減らす）。
- 不正は、完全には防げない（遊びの順位表と割り切る）。
