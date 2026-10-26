dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
G3CT = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f < 3200 or f > 4600 then return end
  local t = {}
  for a = 0x101240, 0x10376f, 0x50 do
    if main:read_u8(a) ~= 0 then
      local h = main:read_u32(a + 0x1c)
      if h >= 0x27700 and h < 0x27a00 then
        t[#t+1] = string.format("%04x:%06x:%02x%02x%02x%02x:%02x:%02x", a & 0xffff, h, main:read_u8(a), main:read_u8(a+1), main:read_u8(a+2), main:read_u8(a+3), main:read_u8(a + 0x2a), main:read_u8(a + 0x26))
      end
    end
  end
  out:write(f .. " " .. table.concat(t, " ") .. "\n")
end)
