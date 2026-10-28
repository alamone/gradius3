#!/bin/bash
REPO=${REPO:-$(cd "$(dirname "$0")/../../../.." && pwd)}   # リポジトリの場所（既定はこのファイルから4つ上）
# 純正: 普通に START → 状態2に入ったフレームで 面・進行度を書き込む（メニューの ApplyStage と同じ書き方）
# usage: plain_start.sh <romdir> <name> <stage> <progress hex> <shot> [END] [SNAP]
RD=$1; N=$2; ST=$3; PR=$4; SH=$5; END=${6:-4300}; SNAPR=${7:-2200:4300:150}
T=${T2:-1821}
SEQ="1400:COIN,1500:START,1640:B1,1720:B1,1800:B1"
[ -z "$NOFIRE" ] && for f in $(seq 1950 6 $END); do SEQ="$SEQ,$f:B2"; done
s=$(printf %x $((ST-1)))
P="$T:101051:$s,$T:1010d1:$s,$T:101063:1,$T:1010e3:1,$T:101052:$PR:w,$T:1010d2:$PR:w"
for f in $(seq 1950 100 $END); do P="$P,$f:10106c:$SH"; done
S=$(echo $SNAPR | tr : ' '); set -- $S
mkdir -p runs/$N
HOLD=3 HOLDK="${HOLDX:-}" SEQ="$SEQ" POKE="$P$XP" SHOTAT="$(seq -s, $1 $3 $2)" SHOTDIR=$PWD/runs/$N WATCH="${WATCH:-40029,101001,101051,101052}" END=$END OUTLOG=$PWD/runs/$N/w.log G3=${G3:-$HOME/g3/g3} \
 G3RUN=$REPO/src/lua/g3run.lua bash $REPO/src/lua/run.sh $RD ${LUAF:-$REPO/src/lua/g3run.lua} $PWD/runs/${N}_x > runs/$N/stdout.txt 2>&1
rm -rf runs/${N}_x
python3 - runs/$N <<'P'
import sys,glob,re
from PIL import Image
d=sys.argv[1]; fs=sorted(glob.glob(d+'/shot_*.ppm'),key=lambda f:int(re.findall(r'\d+',f.split('/')[-1])[0]))
for f in fs: Image.open(f).save(f[:-4]+'.png')
ims=[Image.open(f) for f in fs]; w,h=ims[0].size; cols=5; rows=(len(ims)+cols-1)//cols
c=Image.new('RGB',(w*cols,h*rows))
for i,im in enumerate(ims): c.paste(im,((i%cols)*w,(i//cols)*h))
c.save(d+'/sheet.png'); print(len(ims),'shots')
P
