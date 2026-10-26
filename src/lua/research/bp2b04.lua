local dbg=manager.machine.devices[":maincpu"].debug
dbg:bpset(0x2b04, "1", 'logerror "B04 d7=%x f48=%x f49=%x cam=%x\\n",d7&ff,b@40048,b@40049,d@1038de; go')
dbg:bpset(0x2afc, "1", 'logerror "AFC d7=%x f48=%x f49=%x cam=%x\\n",d7&ff,b@40048,b@40049,d@1038de; go')
manager.machine.debugger:command('go')
dofile("/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/lua/g3run.lua")
