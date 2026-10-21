#!/bin/bash
# usage: run.sh <rompath> <lua> <outdir> [extra mame args]   (env: SEQ POKE WATCH END ... は g3run.lua 参照)
RP=$1; LUA=$2; OUT=$3; shift 3
G3=${G3:-/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/build/mame/g3}
TMP=$(mktemp -d)
export LD_LIBRARY_PATH=/opt/sdl/lib SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy
rm -rf "$OUT"; mkdir -p "$OUT"; export DUMPPREFIX="$OUT"
"$G3" gradius3 -rompath "$RP" -video none -sound none -nothrottle -skip_gameinfo \
  -snapshot_directory "$OUT" -snapname "%i" -autoboot_script "$LUA" \
  -homepath "$TMP" -cfg_directory "$TMP/cfg" -nvram_directory "$TMP/nv" "$@" ${MAME_EXTRA}
rm -rf "$TMP"
