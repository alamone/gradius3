# 10面 ❹（脱出）の開始位置（#21）

純正でラスボスを倒して脱出に入る流れと、改造のメニューから ❹ で始めたときを比べる。

```bash
H=<リポジトリ>/src/lua/research/escape10; L=<リポジトリ>/src/lua
# 純正: 10面 ❸ のあたり（進行度 $2341）から、死なない・上下左右に動く・撃つ（../cov/covplay.lua）。位置の記録＋音の記録＋パレットの書き込み
G3RUN2=$H/poslog.lua G3RUN=$H/../cov/covplay.lua COVOUT=c.bin STG=10 PROG=2341 LOOP=1 INV=1 MOVE=1 END=11000 bash $L/run.sh <純正> $H/snd.lua x > g.log
PALOUT=pal_g.bin PA=9000 PB=10500 G3RUN2=$H/../cov/covplay.lua COVOUT=c.bin STG=10 PROG=2341 LOOP=1 INV=1 MOVE=1 END=10501 bash $L/run.sh <純正> $H/palw.lua x
# 改造: メニューで 10面・エリア 12（❹）・無敵
AF=""; for f in $(seq 2400 6 9000); do AF="$AF,$f:B2"; done
G3RUN2=$H/poslog.lua G3RUN=$L/g3run.lua SEQ="1400:COIN,1730:START,1870:B1,1950:B1,2030:B1$AF" HOLDK="1495:U:20,1500:START:5" POKE="1700:103f08:a,1700:103f0a:c,1700:103f20:1" END=4000 bash $L/run.sh <改造>/mame $H/snd.lua x > m.log
```

- `poslog.lua`: 30フレームごとに 状態・面・画面の位置（$1038de の上位）・進行度・自機。`snd.lua`: 音のキュー（$40380〜）に入った番号と位置。`palw.lua`: PA〜PB フレームのパレットの書き込み（PC ごと）、PALOUT で PB のパレットを保存。`shots.lua`: SHOTAT のフレームの画面（PPM）。`genstart.lua`: 純正で 面・進行度 を書いて始める（死なないパッチ INV=1）。
