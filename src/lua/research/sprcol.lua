dofile(os.getenv("G3LUA"))
local sub = manager.machine.devices[":sub"].spaces["program"]
local main = manager.machine.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
local used = {}
G3CT = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f < 2900 or f % 4 ~= 0 then return end
  for i = 0, 127 do
    local b = 0x2c0800 + i * 16
    if (sub:read_u8(b + 1) & 0x80) ~= 0 then
      local c = 16 + ((sub:read_u8(b + 7) & 0x1e) >> 1)
      if not used[c] then used[c] = f; out:write(string.format("first %d pal %d\n", f, c)); out:flush() end
    end
  end
end)
