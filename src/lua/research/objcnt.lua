dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
G3CT = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f < 6700 or f % 10 ~= 0 then return end
  local t = {}
  for a = 0x101240, 0x103e00, 0x50 do
    if main:read_u8(a) ~= 0 then local ty = main:read_u16(a+0x28); t[ty] = (t[ty] or 0) + 1 end
  end
  local s = {}
  for k, v in pairs(t) do s[#s+1] = string.format("%04x:%d", k, v) end
  table.sort(s)
  out:write(f .. " de=" .. string.format("%x", main:read_u32(0x1038de)) .. " " .. table.concat(s, " ") .. "\n")
end)
