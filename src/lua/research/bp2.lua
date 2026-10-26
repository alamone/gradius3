local dbg=manager.machine.devices[":sub"].debug
manager.machine.debugger:command('focus sub')
dbg:bpset(0xafe6, "1", 'focus sub; logerror "STK a0=%x d5=%x a5=%x m2=%x\\n",a0,d5,a5,w@(a0+2); go')
dbg:bpset(0xafd4, "1", 'focus sub; logerror "PRE a0=%x m2=%x d0=%x\\n",a0,w@(a0+2),d0; go')
manager.machine.debugger:command('go')
dofile("/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/lua/g3run.lua")
