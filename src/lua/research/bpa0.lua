local d=manager.machine.debugger
d:command('focus maincpu')
d:command('bpset 7ba8,1,{logerror "A0=%x\n",a0; bpclear; go}')
d:command('go')
dofile("/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/lua/g3run.lua")
