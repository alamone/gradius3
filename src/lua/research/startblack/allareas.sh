#!/bin/bash
# usage: allareas.sh <改造の mame フォルダ> <出力> [面 ...]
# スタートメニューで 面・エリアを選び（無敵 ON）、START 表示（状態2 の 40 フレーム目）とプレイ（状態5 の 60・300・600 フレーム目）を撮る。
# 出力/<面>_<エリア>/ に shots.lua の画像とパレット。面を省くと 1〜10 面の全エリア（mod_menu.AREAS）
H=$(cd "$(dirname "$0")" && pwd); L=$H/../..
RP=$1; OUT=$2; shift 2
AREAS=(5 5 9 1 7 5 4 5 3 12)
STG=${@:-1 2 3 4 5 6 7 8 9 10}
mkdir -p "$OUT"
for s in $STG; do for a in $(seq 1 ${AREAS[$((s-1))]}); do
  d=$OUT/${s}_$a; rm -rf "$d"; mkdir -p "$d"
  SHOTDIR=$d REL=40,60,300,600 G3RUN=$L/g3run.lua SEQ="1400:COIN,1730:START,1870:B1,1950:B1,2030:B1" HOLDK="1495:U:20,1500:START:5" \
    POKE="1700:103f08:$(printf %x $s),1700:103f0a:$(printf %x $a),1700:103f20:1" END=2800 \
    bash $L/run.sh "$RP" $H/shots.lua "$d/x" >/dev/null 2>&1
  rm -rf "$d/x"
done; done
