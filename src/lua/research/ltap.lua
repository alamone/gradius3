dofile(os.getenv("G3LUA"))
local cpu = manager.machine.devices[":maincpu"]
local sp = cpu.spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
G3F = emu.add_machine_frame_notifier(function() f = f + 1 end)
G3Q = sp:install_write_tap(0xe8000, 0xe8001, "q", function(off, data, mask)
  if f > 2400 then
    local a7 = cpu.state["SP"].value
    out:write(string.format("%d off=%x data=%04x mask=%04x pc=%x s0=%x s1=%x s2=%x s3=%x\n", f, off, data, mask, cpu.state["PC"].value, sp:read_u32(a7), sp:read_u32(a7+4), sp:read_u32(a7+8), sp:read_u32(a7+12))); out:flush()
  end
end)
