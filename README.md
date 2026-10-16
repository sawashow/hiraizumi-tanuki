# 平泉タヌキ侍

平泉（月見坂・毛越寺・金色堂）を舞台にした、2D 横スクロールアクション。Python と pygame で作っています。
刀で斬り、木の葉手裏剣を投げて進みます。

**ブラウザで遊ぶ**: https://hiraizumi-tanuki.ponpoco-works.com/
（初回は実行環境の読み込みに 20〜30 秒かかります。開いたら、画面を一度クリックして始めます）

## 操作

| キー | 動作 |
|---|---|
| ← → | 移動 |
| Space / ↑ | ジャンプ（押し続けるほど高く跳ぶ） |
| ↓ | しゃがむ（ボスの高い光波をくぐる。しゃがんだまま、刀・手裏剣も使える） |
| Z | 刀 |
| X | 木の葉手裏剣 |
| Enter | 再開（ゲームオーバー・クリア時） |
| P | ポーズ（もう一度押すと、続きから）。窓がうしろに回ったときも、止まります |
| Esc | 終了（パソコン版のみ） |

スタート画面で Enter（または刀・ジャンプのキー）を押すと、メニューが出ます。上下で項目を選び、決定で進みます。

| 項目 | 内容 |
|---|---|
| STORY | 始める |
| OPTION | 設定の画面へ。LEVEL（難しさ。EASY / NORMAL / HARD）、MUSIC（曲の音量）、SOUND（効果音の音量）を、左右で変える。BACK で戻る |
| HOW TO PLAY | 操作説明を出す（決定で、メニューに戻る） |

コントローラ（Xbox・PlayStation・Switch Pro・8BitDoなど）を挿すと、そのまま使えます（起動したあとに挿しても大丈夫です）。

| コントローラ | 操作 |
|---|---|
| 十字キー・左スティック | 移動（下でしゃがむ） |
| A（PlayStationは×） | ジャンプ（押し続けるほど高く）・決定 |
| X（□） | 刀 |
| B・Y（○・△） | 木の葉手裏剣（B＝○は決定にも使えます） |
| Start | ポーズ（遊んでいる間）・再開（ゲームオーバー・クリア時） |

## アイテム

| アイテム | 効果 |
|---|---|
| 団子 | 手裏剣を投げられる数が1つ増える（12まで持てる。団子は、足場の上にだけ置いてある。画面の左上の、団子の串が、その数）。スコアも入る |
| おにぎり | 体力が2回復する |
| 金の葉 | 刀を振ると、光波が出る（ダメージを受けると消える） |
| 三方手裏剣 | 手裏剣が3方向に出る（ダメージを受けると消える） |
| スーパータヌキ（星） | いまは出ない（試しに外している）。8秒間、速くなって、敵に当たってもダメージを受けない |

敵を倒すと、ときどき、おにぎりや強化のアイテムを落とします。
道ばたの、火のともった石灯籠は、刀や手裏剣で壊せます。中から、おにぎりや強化のアイテムが出ます。

## パソコンで動かす

仮想環境（`.venv`）を作って、動かします（Windows の例）。

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

遊ぶだけなら `pip install pygame` だけでも動きます。`requirements.txt` には、絵や音を作る道具（Pillow）と、ブラウザ版を作る道具（pygbag）も入っています。動作テストは `python tools/smoke_test.py` です。

`python main.py s2` で2面から、`python main.py boss` で、ボスの場所の手前から、`python main.py cp` で、中間地点の手前から始められます（確認用）。

## 構成

- `main.py` / `config.py` / `sprites.py` / `stage.py`: ゲーム本体（`stage.py` は地形とアイテムの配置）。操作感の数値は `config.py` にまとめています
- `assets/images/`: ゲームで使う絵
- `tools/`: 絵の変換ツールと、画面なしの動作テスト（`python tools/smoke_test.py`）
- `.github/workflows/pages.yml`: ブラウザ版を作って公開する（push で自動）。`docs/CNAME` は独自ドメイン名
- `assets/ドット絵基準.md`: 絵の基準
- `assets/ストーリー設定.md`: 筋書きと、ボスの設定
- `assets/ステージコンセプト.md`: 面ごとのコンセプトと、面を作る手順

## 素材について

絵は、生成AIで作ったものを、`tools/` で、ゲーム用に変換しています。
1面と、キャラクター・アイテム・ボスは Gemini、2面の背景（空・中景）と地面タイルは ChatGPT で作りました。
変換のとき、ドットの粗さと色数を、1面にそろえています。
敵・アイテム・鳥居も同じ方法で作っています。

変換の元になる絵と試作（`assets/concept/`）は、容量が増え続けるので、リポジトリには含めていません（`.gitignore`）。
Google Drive（s.sawada@ponpoco-works.com）に置いてあります。元絵を増やしたら、Drive にも上げ直してください。

曲は、生成AI（Gemini）で作りました。曲名は、次のとおりです。

- 始まりの語りの曲: 「Evening at the Border Post」（`assets/audio/bgm_story.ogg`）
- 1面の曲: 「Clash of the Iron Fan」（`assets/audio/bgm_stage1.ogg`）
- ボス戦の曲: 「Crimson Temple Breach」（`assets/audio/bgm_boss.ogg`）
- スーパータヌキの曲: 「Seven Blades High」（`assets/audio/bgm_super.ogg`）
- 地図の曲: 「Steps Into the Morning Sun」（`assets/audio/bgm_map.ogg`）

効果音は、`tools/make_sfx.py` で、計算して作っています。
ただし、ロゴ画面の音（`assets/audio/sfx_logo.ogg`）は、「Springin’ Sound Stock」の素材「チェレスタグリッサンド1」を、切り出して使っています。
効果音：Springin’ Sound Stock（https://www.springin.org/sound-stock/）

「無念…」などの文字の絵は、ドット風フォント DotGothic16（SIL Open Font License 1.1）で書き出したものです。
フォントのファイル自体は、ゲームにもリポジトリにも含めていません。
https://github.com/fontworks-fonts/DotGothic16
