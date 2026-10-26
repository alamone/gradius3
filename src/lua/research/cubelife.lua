dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f, n = 0, 0
local st = {}
local function pos(a)
  local sx, sy = main:read_u32(0x1038de), main:read_u32(0x1038e2)
  return ((main:read_u32(a+8) - sx) >> 8) & 0xffff, ((main:read_u32(a+12) - sy) >> 8) & 0xffff
end
G3CT = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f < 3000 then return end
  for i = 0, 31 do
    local a = 0x102320 + i * 0x50
    local act = main:read_u8(a) ~= 0 and main:read_u8(a+0x28) == 0x33 and main:read_u8(a+0x29) == 0x01
    local s = st[i]
    if act and not s then
      n = n + 1; local x, y = pos(a)
      st[i] = {n = n, f0 = f, x0 = x, y0 = y, r = false}
    elseif act and s and not s.r and main:read_u8(a+0x2a) == 1 then
      s.r = true; local x, y = pos(a)
      s.fr, s.xr, s.yr = f, x, y
      s.px = (main:read_u32(0x101008) - main:read_u32(0x1038de)) >> 8
      s.py = (main:read_u32(0x10100c) - main:read_u32(0x1038e2)) >> 8
    elseif not act and s then
      out:write(string.format("%d spawn=%d y0=%d x0=%d react=%s stick=%d xe=%d ye=%d\n", s.n, s.f0, s.y0, s.x0,
        s.r and string.format("%d@%d,%d(+%d) ship=%d,%d", s.fr, s.xr, s.yr, s.fr - s.f0, s.px, s.py) or "none", f, s.xe or 0, s.ye or 0, 0))
      st[i] = nil
    end
    if act and st[i] then local x, y = pos(a); st[i].xe, st[i].ye = x, y end
  end
  out:flush()
end)
