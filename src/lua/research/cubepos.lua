dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
G3CT = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f ~= tonumber(os.getenv("AT")) then return end
  local cam = main:read_u32(0x1038de); local camy = main:read_u32(0x1038e2)
  for a = 0x102320, 0x102320 + 31*0x50, 0x50 do
    if main:read_u8(a) ~= 0 and main:read_u16(a+0x28) == 0x3301 then
      out:write(string.format("%d %d %d %d\n", (main:read_u32(a+8)-cam)>>8, (main:read_u32(a+12))>>8, main:read_u8(a+0x2a), (camy)>>8))
    end
  end
  out:close()
end)
