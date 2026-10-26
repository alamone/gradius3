dofile(os.getenv("G3LUA"))
local sub = manager.machine.devices[":sub"].spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
local seen = {}
G3CT = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f < 2000 or f % 2 ~= 0 then return end
  for i = 0, 127 do
    local b = 0x2c0800 + i * 16
    if (sub:read_u8(b + 1) & 0x80) ~= 0 then
      local c = 16 + ((sub:read_u8(b + 7) & 0x1e) >> 1)
      local code = sub:read_u16(b + 2) & 0x3fff
      local k = c .. ":" .. code
      if not seen[k] then seen[k] = f; out:write(string.format("%d pal %d code %04x\n", f, c, code)); out:flush() end
    end
  end
end)
