#!/bin/bash
# usage: run.sh <rompath> <lua> <outdir> [extra mame args]   (env: SEQ POKE WATCH END ... は g3run.lua 参照)
RP=$1; LUA=$2; OUT=$3; shift 3
G3=${G3:-$HOME/g3/g3}   # ビルド済み: CLAUDE.md の手順で $HOME/g3 に展開
TMP=$(mktemp -d)
export LD_LIBRARY_PATH=/opt/sdl/lib SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy
rm -rf "$OUT"; mkdir -p "$OUT"; export DUMPPREFIX="$OUT"
# セット: DRIVER で指定、なければ rompath にある zip で選ぶ（gradius3.zip があれば gradius3、gradius3j.zip だけなら gradius3j）
if [ -z "$DRIVER" ]; then DRIVER=gradius3; [ ! -e "$RP/gradius3.zip" ] && [ -e "$RP/gradius3j.zip" ] && DRIVER=gradius3j; fi
"$G3" "$DRIVER" -rompath "$RP" -video none -sound none -nothrottle -skip_gameinfo \
  -snapshot_directory "$OUT" -snapname "%i" -autoboot_script "$LUA" \
  -homepath "$TMP" -cfg_directory "$TMP/cfg" -nvram_directory "$TMP/nv" "$@" ${MAME_EXTRA}
rm -rf "$TMP"
