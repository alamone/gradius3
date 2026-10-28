#!/bin/bash
# reg.sh <romdir(mame/ を含む出力)> <outdir>  : 改造の機能の場面を順に動かして RAM を保存（前後のビルドで比べる）
RD=$1/mame; O=$2; mkdir -p $O
L=$(cd "$(dirname "$0")/../.." && pwd)
run() { local n=$1; shift; env "$@" DUMPPREFIX=$O/$n bash $L/run.sh $RD $L/g3run.lua $O/x_$n >/dev/null 2>&1; mv $O/x_$n/* $O/ 2>/dev/null; rm -rf $O/x_$n; }
AF=""; for f in $(seq 2400 6 7000); do AF="$AF,$f:B2"; done
MENU="1400:COIN,1730:START,1870:B1,1950:B1,2030:B1"
# 1 通常プレイ（メニューなし）
run plain SEQ="1400:COIN,1500:START,1640:B1,1720:B1,1800:B1$AF" END=7000 DUMPAT=3000,5000,7000
# 2 3面H 無敵・ポーズ（長押し）・装備コマンド（短押し）・STAGE DISP
run m3h SEQ="$MENU$AF,4600:START" HOLDK="1495:U:20,1500:START:5,3600:START:70,3800:B1:4" POKE="1700:103f08:3,1700:103f0a:8,1700:103f20:1,1700:1039c4:1" END=7000 DUMPAT=3000,3700,5000,7000
# 3 キューブラッシュ
run cube SEQ="$MENU$AF" HOLDK="1495:U:20,1500:START:5" POKE="1700:103f0b:1" END=7000 DUMPAT=3000,5000,7000
# 4 ボスラッシュ
run boss SEQ="$MENU$AF" HOLDK="1495:U:20,1500:START:5" POKE="1700:103f0b:2,1700:103f20:1" END=7000 DUMPAT=3000,5000,7000
# 5 10面 ❹ / 隠し面
run s10 SEQ="$MENU$AF" HOLDK="1495:U:20,1500:START:5" POKE="1700:103f08:a,1700:103f0a:c,1700:103f20:1" END=6000 DUMPAT=3000,6000
run s11 SEQ="$MENU$AF" HOLDK="1495:U:20,1500:START:5" POKE="1700:103f08:b,1700:103f20:1" END=6000 DUMPAT=3000,6000
# 6 メニューを開いてキャンセル→通常START
run cancel SEQ="1400:COIN,1730:B2,1900:START,2040:B1,2120:B1,2200:B1$AF" HOLDK="1495:U:20,1500:START:5" END=6000 DUMPAT=1720,3000,6000
