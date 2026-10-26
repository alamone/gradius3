dofile(os.getenv("G3LUA"))
local sub = manager.machine.devices[":sub"]
local sp = sub.spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
local last = -1
G3F = emu.add_machine_frame_notifier(function() f = f + 1 end)
G3W = sp:install_write_tap(0x280000, 0x29ffff, "cw", function(off, data, mask)
  local pc = sub.state["PC"].value
  if f > 2400 and f < 6800 and pc == 0x7f34 then
    local a0 = sub.state["A0"].value; local a5 = sub.state["A5"].value
    if a5 ~= last then last = a5
      out:write(string.format("%d a0=%x a5=%x obj0=%02x m2=%04x m4=%02x m26=%02x m28=%04x\n", f, a0, a5, sp:read_u8(a0), sp:read_u16(a0+2), sp:read_u8(a0+4), sp:read_u8(a0+0x26), sp:read_u16(a0+0x28)))
    end
  end
end)
