dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
local last = {}
G3CT = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f < 3200 or f > 4400 then return end
  for i = 0, 31 do
    local a = 0x102320 + i * tonumber(os.getenv("STRIDE") or "80")
    local s = string.format("%02x %02x%02x %02x %02x %02x %08x", main:read_u8(a), main:read_u8(a+0x28), main:read_u8(a+0x29), main:read_u8(a+0x2a), main:read_u8(a+0x26), main:read_u8(a+0x27), main:read_u32(a+0x1c))
    if last[i] ~= s then out:write(f .. " " .. i .. " " .. s .. "\n"); last[i] = s end
  end
end)
