# #34 メインの改造コードの引っ越しの確かめ方

```bash
H=<リポジトリ>/src/lua/research/move34
# 1) 改造前（main の古いビルド）と後で、同じ操作の RAM を比べる（RAM に置いたコード・スタックは除く）
$H/reg.sh <前のビルド出力> reg/before ; $H/reg.sh <後のビルド出力> reg/after
python3 $H/cmp.py reg/before reg/after
# 2) RAM に置いたコードに、写し終えた後で書き込みが無いか（通しプレイ・2P・テスト・ゲームオーバー・隠し面・キューブ/ボスラッシュ）
$H/guardall.sh <後のビルド出力>
# 3) RAM のコードを写し終える前に、そこが実行されていないか
SEQ="1400:COIN,1500:START,1640:B1,1720:B1,1800:B1" END=3000 G3RUN=<リポジトリ>/src/lua/g3run.lua bash <リポジトリ>/src/lua/run.sh <後のビルド出力>/mame $H/early.lua x
```

- `cmp.py` は main RAM・共有RAM・グラフィック・パレットを比べる。3面H（`m3h`）は自機の弾が地形を掘るので、掘り跡が直った分（#6）だけ違いが出る。弾を撃たない同じ操作では一致する。
- `dumpall.lua`（毎フレームの RAM＋サブの RAM＋パレット、CHR=1 で文字RAMも）・`trc2.lua`（TF のフレームに通った PC）は違いの出どころを探すのに使った。
