local d=manager.machine.debugger
d:command('focus sub')
d:command('wpset 202324:sub,1,r,1,{logerror "R4 pc=%x\\n",pc; go}')
d:command('wpset 202324:sub,1,w,1,{logerror "W4 pc=%x d=%x\\n",pc,wpdata; go}')
d:command('go')
dofile("/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/lua/g3run.lua")
