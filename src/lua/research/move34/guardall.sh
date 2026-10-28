#!/bin/bash
# guardall.sh <改造のビルド出力> : RAM に置いた改造のコードに、写し終えた後で書き込みが無いかを色々な場面で調べる（guard.lua）
# 結果は ./guard/*.log の「GUARD total 0」。0 以外なら、どの PC が書いたかが出る
H=$(cd "$(dirname "$0")" && pwd); L=$(cd "$H/../.." && pwd); ROM=$1/mame; mkdir -p guard
G=$H/guard.lua
rg() { n=$1; shift; env "$@" G3RUN=$H/../cov/covplay.lua COVOUT=$PWD/guard/$n.cov bash $L/run.sh $ROM $G guard/x_$n > guard/$n.log 2>&1; rm -rf guard/x_$n; }
rm2() { n=$1; st=$2; e=$3; shift 3; AF=""; for f in $(seq 2400 5 $e); do AF="$AF,$f:B2"; [ $((f%600)) = 0 ] && AF="$AF,$f:B1,$((f+300)):START"; done
  env "$@" SEQ="1400:COIN,1730:START,1870:B1,1950:B1,2030:B1$AF" HOLDK="1495:U:20,1500:START:5,4000:START:70" POKE="1700:103f08:$st,1700:103f20:1${XP:-}" END=$e \
  G3RUN=$L/g3run.lua bash $L/run.sh $ROM $G guard/x_$n > guard/$n.log 2>&1; rm -rf guard/x_$n; }
( rg A END=200000 INV=1 MOVE=1; rg B END=30000 IDLE=1; rm2 m11 b 40000; XP=",1700:103f0b:2" rm2 boss 1 40000 ) &
( rg C END=40000 P2=1 MOVE=1; rg H END=70000 INV=1 MOVE=1 INVOFF=45000; rg D END=20000 MOVE=1 DSW="DSW3:Service Mode:0"; rm2 m12 c 40000; XP=",1700:103f0b:1" rm2 cube 1 40000; XP=",1700:103f0a:8,1700:1039c4:1" rm2 m3 3 30000 ) &
wait; grep -h "GUARD" guard/*.log
