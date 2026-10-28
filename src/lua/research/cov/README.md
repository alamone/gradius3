# メインROM・RAM の「使われ方」の記録（#34）

メインROMのどこが読まれるか（命令の取り込みも含む）と、メインRAM・共有RAMのどこが読み書きされるかを、MAME で自動プレイしながら記録する。
**「読まれなかった」＝「使われていない」ではない**（隠し面の出口・まれな敵など、通らなかっただけの所が混ざる）。候補を見つける道具として使い、最後は番地の参照（refs.py）や処理の中身で確かめる。

```bash
H=<リポジトリ>/src/lua/research/cov
export ROMDIR=<純正の gradius3.zip を置いたフォルダ> WORK=$PWD
$H/cov.sh A END=400000 INV=1 MOVE=1          # 通しプレイ（死なない・上下左右に動く）→ 10面・エンディング・2周目まで
$H/cov.sh C END=40000 P2=1 MOVE=1            # 2人プレイ（死ぬ・交代・コンティニュー）
$H/cov.sh D END=20000 MOVE=1 DSW="DSW3:Service Mode:0"   # テストモード
$H/cov.sh H END=70000 INV=1 MOVE=1 INVOFF=45000          # 途中から死ぬようにしてゲームオーバー・ネームエントリー
$H/cov.sh E5 END=25000 INV=1 MOVE=1 STG=5 LOOP=3         # 3周目の5面から
MODDIR=<改造のビルド>/mame $H/covmod.sh S11 b 45000      # 改造のメニューから隠し面（b=11, c=12）
# 起動から13秒（ROM チェックの読み出しは除く）
COVOUT=$WORK/boot.bin bash <リポジトリ>/src/lua/run.sh $ROMDIR $H/covboot.lua $WORK/x
python3 $H/gaps.py <main313.bin> $WORK/*.bin        # 一度も読まれなかった範囲（大きい順）
```

- `<name>.bin` = メインROMの語ごとに 1（読まれた）/0。`<name>.bin.ram` = メインRAM 0x40000〜・共有RAM 0x100000〜 の語ごとに bit0 書いた・bit1 読んだ（サブからの読み書きも含む）・bit2 0 以外を書いた。いずれも起動から12秒（ROM・RAM チェックの後）から数える。
- `refs.py <main313.bin> refs.txt`：ROM の中の番地らしい値の一覧。`gapref.py <main313.bin> <全部を合わせた .bin> [最小バイト数]`：読まれなかった範囲ごとに、そこを指している場所（読まれた所から指されているか）。
- `wtime.lua`：指定した範囲（RANGES="40d64-41080,..."）に書いたフレームと PC。`NEXT=` に続けて動かすスクリプトを指定する。
- `main313.bin` は純正313のメイン（945_313.f15 と 945_312.e15 を1バイトずつ交互に並べたもの）。

分かったこと（2026-10-28）は dev/TECH.md の「ROM の空き」「RAM の空き」。
