dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
G3ST = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f < 2400 or f > 3070 then return end
  local t = {}
  for i = 0, 31 do
    local a = 0x102320 + i * 0x50
    if main:read_u8(a) ~= 0 then t[#t+1] = string.format("%d:%04x,%08x,%08x,%02x,%04x", i, main:read_u16(a+0x28), main:read_u32(a+8), main:read_u32(a+12), main:read_u8(a+0x2a), main:read_u16(a+2)) end
  end
  out:write(f .. " " .. table.concat(t, " ") .. "\n")
end)
