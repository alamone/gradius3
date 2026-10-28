#!/bin/bash
# covmod.sh <name> <面(16進)> <END> : 改造ROM（MODDIR = ビルド出力/mame）のメニューから面を選んで無敵で遊び、読み出しを記録（XP=",f:番地:値" で書き込みを足す）
H=$(cd "$(dirname "$0")" && pwd); REPO=$(cd "$H/../../../.." && pwd); WORK=${WORK:-$PWD}
N=$1; ST=$2; END=$3
AF=""; for f in $(seq 2400 5 $END); do AF="$AF,$f:B2"; [ $((f%40)) = 0 ] && AF="$AF,$f:B3"; [ $((f%600)) = 0 ] && AF="$AF,$f:B1"; done
SEQ="1400:COIN,1730:START,1870:B1,1950:B1,2030:B1$AF" HOLDK="1495:U:20,1500:START:5" POKE="1700:103f08:$ST,1700:103f20:1${XP:-}" END=$END \
COVOUT=$WORK/$N.bin G3RUN=$REPO/src/lua/g3run.lua bash $REPO/src/lua/run.sh $MODDIR $H/cov.lua $WORK/x_$N > $WORK/$N.log 2>&1
rm -rf $WORK/x_$N
