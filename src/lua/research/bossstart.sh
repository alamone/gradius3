#!/bin/bash
# usage: bossstart.sh <name> <romdir> <stage row 1..10>  : MODE=BOSS RUSH, INVINCIBLE ON, 指定面から開始して 200 フレームごとに撮影
S=/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad
N=$1; RD=$2; ROW=$3
SEQ="1400:COIN,1500:START,1620:R,1640:R"; f=1660
for i in $(seq 1 $ROW); do SEQ="$SEQ,$f:D"; f=$((f+20)); done
SEQ="$SEQ,$f:R"; f=$((f+20))
for i in $(seq 1 $((20-ROW))); do SEQ="$SEQ,$f:D"; f=$((f+20)); done
SEQ="$SEQ,$f:R,$((f+40)):START,$((f+160)):B1,$((f+460)):B1,$((f+760)):B1"; g=$((f+900))
rm -rf $S/runs/$N; mkdir -p $S/runs/$N
HOLDK="1495:U:20" SEQ="$SEQ" WATCH="101051,1038df,40029" SHOTAT="$(seq -s, $g 150 $((g+2100)))" SHOTDIR=$S/runs/$N OUTLOG=$S/runs/$N/w.log END=$((g+2110)) bash $S/lua/run.sh $RD $S/lua/g3run.lua $S/runs/${N}x >/dev/null 2>&1
