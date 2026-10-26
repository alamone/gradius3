dofile(os.getenv("G3LUA"))
local m = manager.machine
local main = m.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
local F0, F1 = tonumber(os.getenv("CT0") or "3000"), tonumber(os.getenv("CT1") or "7600")
G3CT = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f < F0 or f > F1 or f % 4 ~= 0 then return end
  local t = {}
  for a = 0x101240, 0x10376f, 0x50 do
    if main:read_u8(a) ~= 0 then
      local h = main:read_u32(a + 0x1c)
      if h >= 0x27700 and h < 0x27a00 then
        t[#t+1] = string.format("%04x:%05x,%05x,%02x,%02x", a & 0xffff, (main:read_u32(a + 8) - main:read_u32(0x1038de)) & 0xfffff, main:read_u32(a + 0xc) & 0xfffff, main:read_u8(a + 0x2a), main:read_u8(a + 0x26))
      end
    end
  end
  out:write(f .. " " .. table.concat(t, " ") .. "\n")
end)
