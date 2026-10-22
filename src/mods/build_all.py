import sys
B='/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad'
sys.path[:0]=[B+'/tools',B+'/mods']
import g3build, mod_main, mod_sub, mod_boot, mod_sound, os
out=sys.argv[1]
r=g3build.Rom()
la,lb=mod_main.apply(r)
ls,n=mod_sub.apply(r)
if not os.environ.get("NOSNDVOL"): mod_sound.apply(r); mod_sound.fix_sum(r)
print('sub core bytes',n)
be=mod_boot.apply(r, os.environ.get('BOOTTEXT'))
print('boot text', mod_boot.blob(os.environ.get('BOOTTEXT')))
r.finalize(out, filler_main=[(be + (be & 1), 0x3fff0)] + r.free_main)
print('built',out)
