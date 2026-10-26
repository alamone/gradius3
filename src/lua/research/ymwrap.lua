dofile("/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/lua/g3run.lua")
local snd = manager.machine.devices[":audiocpu"].spaces["program"]
local f = 0; local addr = 0
local out = io.open(os.getenv("YMOUT"), "w")
_G.ymtap = snd:install_write_tap(0xf030, 0xf031, "ym", function(off, data, mask)
  if off == 0xf030 then addr = data else
    if (addr >= 0x20 and addr <= 0x27) or addr == 0x08 then out:write(string.format("%d %02x %02x\n", f, addr, data)) end
  end
end)
emu.register_frame_done(function() f = f + 1; out:flush() end)
