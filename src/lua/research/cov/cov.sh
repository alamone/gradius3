#!/bin/bash
# cov.sh <name> [env...] : 純正ROM（ROMDIR に gradius3.zip）を covplay.lua で自動プレイし、$WORK/<name>.bin（ROM の読み出し）・.ram（RAM）を作る
H=$(cd "$(dirname "$0")" && pwd); REPO=$(cd "$H/../../../.." && pwd); WORK=${WORK:-$PWD}
N=$1; shift
env "$@" COVOUT=$WORK/$N.bin bash $REPO/src/lua/run.sh $ROMDIR $H/covplay.lua $WORK/x_$N > $WORK/$N.log 2>&1
rm -rf $WORK/x_$N
