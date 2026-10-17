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
5. Web アプリとして公開する
   ```
   clasp deploy --description "v1"
   clasp deployments
   ```
   出てきた **デプロイ ID**（`AKfycb…`）から、URL ができる: `https://script.google.com/macros/s/<デプロイ ID>/exec`
6. 動作を確かめる（ブラウザで、次の URL を開く。`{"ok":true,"rows":[]}` が出れば成功）
   ```
   https://script.google.com/macros/s/<デプロイ ID>/exec?action=ranking&level=easy
   ```

## 直したとき（URL は、変えない）

```
clasp push
clasp deploy -i <デプロイ ID> --description "v2"
```
`-i` を付けると、同じ URL のまま、中身だけが入れ替わる（付けないと、新しい URL ができる）。

## 確認

`node server/gas/test_check.js`（記録のチェックの処理を、GAS の外で試す）。

## 決めごと（`Code.gs` の先頭）

- 順位表は、難しさ（easy / normal / hard）ごとに、上位 20 件。各難しさで、200 件まで残す。
- 2分未満の通しは、あり得ないとみなして弾く（`MIN_FRAMES`。実際の最短を知ったら見直す）。
- 開始の合図（トークン）から、送信までの実時間が、フレーム数 ÷ 60 より短い記録は、弾く。
- 名前は、半角英大文字と数字の3文字。使えない名前は `NG_NAMES`。
- 順位の取得は、60秒、使い回す（スプレッドシートの読み込みを減らす）。
- 不正は、完全には防げない（遊びの順位表と割り切る）。
