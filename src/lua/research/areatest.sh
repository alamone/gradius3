#!/bin/bash
# usage: areatest.sh <name> <row(1..12)> <rightpresses>  env: ST10X ST9X MK3X など(ビルドに渡す) SHOTS
S=/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad
N=$1; ROW=$2; RI=$3
cd $S; python3 mods/build_all.py $S/out_at_$N >/dev/null 2>&1 || { echo build fail; exit 1; }
f=1620; SEQ="1400:COIN,1500:START"
for i in $(seq 1 $ROW); do SEQ="$SEQ,$f:D"; f=$((f+20)); done
for i in $(seq 0 $RI); do SEQ="$SEQ,$f:R"; f=$((f+20)); done
if [ -n "$INV" ]; then for i in $(seq 1 $((22-ROW))); do SEQ="$SEQ,$f:D"; f=$((f+20)); done; SEQ="$SEQ,$f:R"; f=$((f+20)); fi
SEQ="$SEQ,$((f+20)):START,$((f+140)):B1,$((f+220)):B1,$((f+300)):B1"
rm -rf $S/runs/at_$N; mkdir -p $S/runs/at_$N
G=$((f+20))
SH=${SHOTS:-$(seq -s, $((G+500)) 50 $((G+1500)))}
HOLDK="1000:U:12,1000:B1:12,1040:D:12,1040:B1:12,1495:U:20" SEQ="$SEQ" SHOTAT="$SH" SHOTDIR=$S/runs/at_$N \
 WATCH="${WATCHX:-1038de,1038df,1038e0,101051}" END=$((G+${ENDX:-1700})) OUTLOG=$S/runs/at_$N/w.log bash lua/run.sh $S/out_at_$N/mame ${LUAF:-$S/lua/g3run.lua} $S/runs/at_${N}x >/dev/null 2>&1
python3 - $S/runs/at_$N <<'P'
import sys,glob,re
from PIL import Image
d=sys.argv[1]; fs=sorted(glob.glob(d+'/shot_*.ppm'),key=lambda f:int(re.findall(r'\d+',f.split('/')[-1])[0]))
ims=[Image.open(f) for f in fs]; w,h=ims[0].size; cols=7; rows=(len(ims)+cols-1)//cols
c=Image.new('RGB',(w*cols,h*rows))
for i,im in enumerate(ims): c.paste(im,((i%cols)*w,(i//cols)*h))
c.save(d+'/sheet.png')
P
rm -rf $S/out_at_$N $S/runs/at_${N}x
echo done $N
