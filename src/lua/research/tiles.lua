dofile(os.getenv("G3LUA"))
local sub = manager.machine.devices[":sub"].spaces["program"]
local f=0
local used = {}
G3TL = emu.add_machine_frame_notifier(function()
  f=f+1
  if f >= 2100 and f % 30 == 0 then
    for cell = 0, 0x17ff do
      local a = sub:read_u8(0x24c000 + cell*2 + 1)
      local c = sub:read_u8(0x250000 + cell*2 + 1)
      local code = c | ((a & 1) << 8) | ((a & 0x1c) << 7)
      used[code] = true
    end
  end
  if f == tonumber(os.getenv("ENDF")) then
    local o = io.open(os.getenv("CTOUT"), "w")
    for k = 0, 0xfff do o:write(used[k] and "1" or "0") end
    o:close()
  end
end)
