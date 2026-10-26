local dbg=manager.machine.devices[":maincpu"].debug
dbg:bpset(0x2b0c, "(d7&ff)>=a0 || (d7&ff)==5b", 'logerror "MUS d7=%x ret=%x ret2=%x\\n",d7,d@(sp),d@(sp+4); go')
manager.machine.debugger:command('go')
dofile("/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/lua/g3run.lua")
