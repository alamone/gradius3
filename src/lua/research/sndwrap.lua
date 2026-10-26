dofile("/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/lua/g3run.lua")
local mainsp = manager.machine.devices[":maincpu"].spaces["program"]
local f = 0
local out = io.open(os.getenv("SNDOUT"), "w")
_G.sndtap = mainsp:install_write_tap(0xe8000, 0xe8001, "sl", function(off, data, mask)
  out:write(string.format("%d %x %04x %04x\n", f, off, data, mask)); out:flush()
end)
emu.register_frame_done(function() f = f + 1 end)
