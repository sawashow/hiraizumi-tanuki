# 平泉タヌキ侍

平泉（月見坂・毛越寺・金色堂）を舞台にした、2D 横スクロールアクション。Python と pygame で作っています。
刀で斬り、木の葉手裏剣を投げて進みます。

**ブラウザで遊ぶ**: https://sawashow.github.io/hiraizumi-tanuki/
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
| Esc | 終了（パソコン版のみ） |

## アイテム

| アイテム | 効果 |
|---|---|
| 団子 | スコア。全部取ると、残機が1つ増える |
| おにぎり | 体力が2回復する |
| 金の葉 | 刀を振ると、光波が出る（ダメージを受けると消える） |
| 三方手裏剣 | 手裏剣が3方向に出る（ダメージを受けると消える） |
| スーパータヌキ（星） | 8秒間、速くなって、敵に当たってもダメージを受けない |

敵を倒すと、ときどき、おにぎりや強化のアイテムを落とします。

## パソコンで動かす

```
pip install pygame
python main.py
```

`python main.py boss` で、ボスの場所の手前から、`python main.py cp` で、中間地点の手前から始められます（確認用）。

## 構成

- `main.py` / `config.py` / `sprites.py` / `stage.py`: ゲーム本体（`stage.py` は地形とアイテムの配置）。操作感の数値は `config.py` にまとめています
- `assets/images/`: ゲームで使う絵
- `tools/`: 絵の変換ツールと、画面なしの動作テスト（`python tools/smoke_test.py`）
- `docs/`: ブラウザ版の公開用ファイル（pygbag で作成）
- `assets/ドット絵基準.md`: 絵の基準
- `assets/ストーリー設定.md`: 筋書きと、ボスの設定

## 素材について

絵は、生成AI（Gemini）で作ったものを、`tools/` で、ゲーム用に変換しています。
敵・アイテム・鳥居も同じ方法で作っています。

曲名は、次のとおりです。

- 始まりの語りの曲: 「Evening at the Border Post」（`assets/audio/bgm_story.ogg`）
- 1面の曲: 「Clash of the Iron Fan」（`assets/audio/bgm_stage1.ogg`）
- ボス戦の曲: 「Crimson Temple Breach」（`assets/audio/bgm_boss.ogg`）

「無念…」などの文字の絵は、ドット風フォント DotGothic16（SIL Open Font License 1.1）で書き出したものです。
フォントのファイル自体は、ゲームにもリポジトリにも含めていません。
https://github.com/fontworks-fonts/DotGothic16
