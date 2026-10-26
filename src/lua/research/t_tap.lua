local m = manager.machine
local main = m.devices[":maincpu"].spaces["program"]
local cnt = 0
print("devices:")
for k,v in pairs(m.devices) do print(k) end
local ok, err = pcall(function()
  main:install_write_tap(0x40000, 0x43fff, "m_ram", function(offset, data, mask) cnt = cnt + 1 end)
end)
print("tap main", ok, err)
local f = 0
emu.add_machine_frame_notifier(function() f = f + 1; if f == 300 then print("count", cnt); m:exit() end end)
