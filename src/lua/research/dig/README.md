# 地形を掘る跡（#6）の再現

純正と改造で、3面 H・6面 C の掘れる地形を同じ条件で撃ち、スナップを比べる。
作業用の空フォルダで動かす（`runs/<名前>/shot_<フレーム>.png` と `sheet.png` ができる）。`G3` は CLAUDE.md の手順の MAME。

```bash
R=<リポジトリ>/src/lua/research/dig
# 改造（メニューから 3面 H・ノーマル=0 / ダブル=3 / レーザー=4。無敵）
$R/menu_start.sh <改造のromフォルダ> m3h_0 3 8 0 2650 2245:2645:100
# 純正（START だけ。状態2に入ったフレームで 面・進行度 0x1641 を書く。6面 C は 6 0601）
$R/plain_start.sh <純正のromフォルダ> g3h_0 3 1641 0 2420 2014:2414:100
# 純正 + 改造が $D4AA〜$DB09 に書いている中身（= 掘り跡のマスクを壊す）→ 改造と同じ四角い跡になる
MP=d4aa:$(python3 -c "import sys;f,e=open(sys.argv[1],'rb').read(),open(sys.argv[2],'rb').read();m=bytes(x for p in zip(f,e) for x in p);print(m[0xd4aa:0xdb0a].hex())" <改造の945_r13.f15> <改造の945_r12.e15>)
INV=7bc4:4268001a602a4e71,ae22:4268001a60284e71     # 純正で死なないようにする（6面で使う）
MAINPATCH=$MP LUAF=$R/rompatch.lua $R/plain_start.sh <純正のromフォルダ> gp3h_0 3 1641 0 2420 2014:2414:100
```

- 改造のプレイ開始は 2145 フレーム、純正は 1914 フレームなので、比べるフレームは 231 ずらす（2245 ↔ 2014）。
- `rompatch.lua` は起動時の ROM チェックの後（12秒）に ROM を書き換える（`MAINPATCH` / `SUBPATCH` = "番地:16進,..."）。
