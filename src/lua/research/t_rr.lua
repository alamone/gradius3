local m = manager.machine
local main = m.devices[":maincpu"].spaces["program"]
print("read_range exists:", main.read_range ~= nil)
local ok, s = pcall(function() return main:read_range(0x100000, 0x103fff, 8) end)
print(ok, ok and #s or s)
for k,v in pairs(m.devices) do print("dev", k) end
local f = 0
emu.add_machine_frame_notifier(function() f = f + 1; if f == 5 then m:exit() end end)
