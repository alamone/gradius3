# usage: VERSION=0.4.17 [G3BASE=<ROMの置き場>] python3 src/mods/build_all.py <出力フォルダ>
#   G3BASE の中に rom/genuine/313_main/945_313.f15・945_312.e15, rw/945_m09.r17・945_m08.n17,
#   rom/gradius3_313_for_MAME.zip を置く（src/tools/g3build.py の先頭を参照）
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(os.path.dirname(HERE), 'tools'), HERE]
import g3build, mod_main, mod_sub, mod_boot, mod_sound, os
out=sys.argv[1]
r=g3build.Rom()
mod_main.apply(r)
ls,n=mod_sub.apply(r)
if not os.environ.get("NOSNDVOL"): mod_sound.apply(r); mod_sound.fix_sum(r)
print('sub core bytes',n)
be=mod_boot.apply(r, os.environ.get('BOOTTEXT'))
print('boot text', mod_boot.blob(os.environ.get('BOOTTEXT')))
r.finalize(out, filler_main=[(be + (be & 1), 0x3fff0)] + r.free_main)
print('built',out)
