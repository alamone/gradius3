dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
local seen = {}
G3CT = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f < 2300 then return end
  for a = 0x100000, 0x103fb0, 0x10 do
    if main:read_u16(a+0x28) == 0x4200 and main:read_u8(a) ~= 0 then
      if not seen[a] then seen[a] = true; out:write(string.format("%d obj %06x b0=%02x 42e70=%04x opts=%02x\n", f, a, main:read_u8(a), main:read_u16(0x42e70), main:read_u8(0x101068))); out:flush() end
    else seen[a] = nil end
  end
end)
