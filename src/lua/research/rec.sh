#!/bin/bash
# usage: rec.sh <romdir> <out.wav>   env: BGM BSTART BLEN G3PAN G3PCM
RP=$1; W=$2
G3=/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/build/mame/g3
TMP=$(mktemp -d)
export LD_LIBRARY_PATH=/opt/sdl/lib SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy
"$G3" gradius3 -rompath "$RP" -video none -sound none -nothrottle -skip_gameinfo -autoboot_script ${LUA:-/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/lua/bgm.lua} \
  -homepath "$TMP" -cfg_directory "$TMP/cfg" -nvram_directory "$TMP/nv" -wavwrite "$W" > "$W.log" 2>&1
rm -rf "$TMP"
