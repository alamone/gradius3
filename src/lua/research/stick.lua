dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
local prev = {}
G3ST = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f < 2300 then return end
  for i = 0, 31 do
    local a = 0x102320 + i * 0x50
    local s = main:read_u8(a+0x26)
    local t = main:read_u16(a+0x28)
    local k = string.format("%02x %04x %02x %04x", s, t, main:read_u8(a+4), main:read_u16(a+2))
    if prev[i] ~= k then out:write(string.format("%d slot%d st26=%s\n", f, i, k)); prev[i] = k end
  end
end)
