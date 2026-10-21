#!/bin/bash
# usage: t_start.sh <rom> <name> "<mbpokes like 08:05,09:02>" [END] [SHOTS]  → メニューを開き MB に値を書いて START
cd /tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad
ROM=$1; N=$2; PK=$3; END=${4:-2600}; SH=${5:-2400}
mkdir -p runs/$N
P=$(python3 -c "import sys;print(','.join('1700:103f%s:%s'%tuple(x.split(':')) for x in sys.argv[1].split(',') if x))" "$PK")
HOLDX="1730:START:8${HOLDX:+,$HOLDX}" POKE="$P${XPOKE:+,$XPOKE}" WATCH="${WATCH:-40005,40029,4002b,101051,101063,1039c0,101050,101052}" OUTLOG=runs/$N.log SHOTAT="$SH" SHOTDIR=runs/$N DUMPAT="${DUMPAT:-}" END=$END SNAPNAME=runs/${N}_s mods/t_menu.sh $ROM
mkdir -p runs/$N
