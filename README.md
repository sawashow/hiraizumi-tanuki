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
| Z | 刀 |
| X | 木の葉手裏剣 |
| Enter | 再開（ゲームオーバー時） |
| Esc | 終了（パソコン版のみ） |

## パソコンで動かす

```
pip install pygame
python main.py
```

## 構成

- `main.py` / `config.py` / `sprites.py`: ゲーム本体。操作感の数値は `config.py` にまとめています
- `assets/images/`: ゲームで使う絵
- `tools/`: 絵の変換ツールと、画面なしの動作テスト（`python tools/smoke_test.py`）
- `docs/`: ブラウザ版の公開用ファイル（pygbag で作成）
- `assets/ドット絵基準.md`: 絵の基準

## 素材について

絵は、生成AI（Gemini）で作ったものを、`tools/` で、ゲーム用に変換しています。
敵は、まだ仮の四角です。
