-- キューブ($3301)の出現を記録: プール 0x102870-0x102d20 (0x50刻み) で新規に有効になった枠の Y と種別を出力
local m = manager.machine
local main = m.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("CUBEOUT") or "runs/cube.txt", "w")
local prev = {}
local f = 0
G3CB = emu.add_machine_frame_notifier(function()
  f = f + 1
  local n = 0
  for a = 0x101240, 0x10376f, 0x50 do
    local act = main:read_u8(a)
    if act ~= 0 and (prev[a] or 0) == 0 and (function() local h = main:read_u32(a + 0x1c); return h >= 0x27700 and h < 0x27a00 end)() then
      out:write(string.format("%d @%06x h=%05x Y=%05x X-scr=%05x t=%02x\n", f, a, main:read_u32(a+0x1c), main:read_u32(a + 0xc), main:read_u32(a + 8) - main:read_u32(0x1038de), main:read_u8(a + 0x2e)))
      out:flush()
    end
    prev[a] = act
  end
end)
