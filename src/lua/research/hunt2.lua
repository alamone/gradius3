dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
local cnt = 0
G3CT = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f < 2300 then return end
  for a = 0x102320, 0x102320 + 31*0x50, 0x50 do
    if main:read_u16(a+0x28) == 0x4200 and main:read_u8(a) ~= 0 then cnt = cnt + 1 end
  end
  if f % 100 == 0 then if cnt > 0 then out:write(string.format("%d hunterframes=%d opts=%02x\n", f, cnt, main:read_u8(0x101068))); out:flush() end; cnt = 0 end
end)
