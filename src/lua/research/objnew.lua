dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
local last = {}
G3CT = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f < 4150 or f > 4300 then return end
  for a = 0x101000, 0x103f00, 0x50 do
    local s = string.format("%02x %04x %04x %02x", main:read_u8(a), main:read_u16(a+0x28), main:read_u16(a+2), main:read_u8(a+4))
    if last[a] ~= s then out:write(string.format("%d %06x %s\n", f, a, s)); last[a] = s end
  end
end)
