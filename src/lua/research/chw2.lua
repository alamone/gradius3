dofile(os.getenv("G3LUA"))
local sub = manager.machine.devices[":sub"]
local sp = sub.spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
G3F = emu.add_machine_frame_notifier(function() f = f + 1 end)
G3W = sp:install_write_tap(0x28c060, 0x28d2ff, "cw", function(off, data, mask)
  if f > 2400 and f < 3070 then out:write(string.format("%d off=%x data=%04x pc=%x a0=%x d5=%x a4=%x a5=%x\n", f, off, data, sub.state["PC"].value, sub.state["A0"].value, sub.state["D5"].value, sub.state["A4"].value, sub.state["A5"].value)) end
end)
