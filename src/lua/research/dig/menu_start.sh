#!/bin/bash
REPO=${REPO:-$(cd "$(dirname "$0")/../../../.." && pwd)}   # リポジトリの場所（既定はこのファイルから4つ上）
# usage: menu_start.sh <romdir> <name> <stage> <area> <shot:0|3|4> [END] [SNAP s:e:i]
# メニューで面・エリアを選んで開始、無敵、（HOLDX="f:KEY:長さ,..." で入力を足す）ショットの種類を書き込み、ショットを連打（右へ少し進む）
RD=$1; N=$2; ST=$3; AR=$4; SH=$5; END=${6:-5000}; SNAPR=${7:-2500:5000:100}
G=1730
SEQ="1400:COIN,1500:START,$G:START,$((G+140)):B1,$((G+220)):B1,$((G+300)):B1"
[ -z "$NOFIRE" ] && for f in $(seq $((G+400)) 6 $END); do SEQ="$SEQ,$f:B2"; done
P="1700:103f08:$(printf %x $ST),1700:103f0a:$(printf %x $AR)"
# 無敵とショット種類は毎200フレーム書き込む
[ -z "$NOINV" ] && for f in $(seq $((G+400)) 200 $END); do P="$P,$f:103f20:1,$f:10106c:$SH"; done; P="$P${XP:-}"   # NOINV=1 で無敵なし、XP=",f:番地:値" で書き込みを足す
S=$(echo $SNAPR | tr : ' '); set -- $S
SHOTS=$(seq -s, $1 $3 $2)
mkdir -p runs/$N
HOLD=3 HOLDK="1000:U:12,1000:B1:12,1040:D:12,1040:B1:12,1495:U:20${HOLDX:+,$HOLDX}" SEQ="$SEQ" POKE="$P" SHOTAT="$SHOTS" SHOTDIR=$PWD/runs/$N \
 WATCH="${WATCH:-40029,10106c,103f20}" END=$END OUTLOG=$PWD/runs/$N/w.log G3=${G3:-$HOME/g3/g3} \
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
