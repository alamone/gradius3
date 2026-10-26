dofile(os.getenv("G3LUA"))
local cpu = manager.machine.devices[":maincpu"]
local sp = cpu.spaces["program"]
local fc = 0
G3PF = emu.add_machine_frame_notifier(function() fc = fc + 1 end)
local o = io.open(os.getenv("POUT"), "w")
local want = tonumber(os.getenv("PCW"), 16)
local lo = tonumber(os.getenv("PLO"), 16); local hi = tonumber(os.getenv("PHI"), 16)
G3PT = sp:install_write_tap(lo, hi, "pt", function(off, data, mask)
  local pc = cpu.state["CURPC"].value
  if pc == want then o:write(string.format("%d %06x %04x %04x\n", fc, off, data, sp:read_u16(0x40032))); o:flush() end
end)
