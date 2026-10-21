#!/bin/bash
# usage: t_menu.sh <outdir> <extra env assignments...>   (menu起動シナリオ: 解除→COIN→UP+START)
cd /tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad
ROM=$1; shift
env HOLDK="1200:U:10,1200:B1:10,1240:D:10,1240:B1:10,1400:COIN:8,1500:U:30,1500:START:8,$HOLDX" SHOTDIR=${SHOTDIR:-runs} "$@" timeout ${TMO:-200} lua/run.sh $ROM/mame ${LUAFILE:-$PWD/lua/g3run.lua} ${SNAPNAME:-runs/menusnap} > ${SNAPNAME:-runs/menusnap}.out 2>&1
