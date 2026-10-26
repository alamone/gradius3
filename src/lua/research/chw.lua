dofile(os.getenv("G3LUA"))
local sub = manager.machine.devices[":sub"]
local sp = sub.spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
G3F = emu.add_machine_frame_notifier(function() f = f + 1 end)
G3W = sp:install_write_tap(0x280000 + 0x784*32, 0x280000 + 0x784*32 + 31, "cw", function(off, data, mask)
  if f > 2400 and f < 2600 then out:write(string.format("%d off=%x data=%04x pc=%x a0=%x\n", f, off, data, sub.state["PC"].value, sub.state["A0"].value)) end
end)
