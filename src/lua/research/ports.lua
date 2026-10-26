local m = manager.machine
local o = io.open("runs/ports.txt","w")
for tag, p in pairs(m.ioport.ports) do
  for n, f in pairs(p.fields) do o:write(tag, " | ", n, "\n") end
end
o:close()
G3N = emu.add_machine_frame_notifier(function() m:exit() end)
