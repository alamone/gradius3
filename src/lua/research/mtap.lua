dofile(os.getenv("G3LUA"))
local cpu = manager.machine.devices[":maincpu"]
local sp = cpu.spaces["program"]
local fc = 0
G3MF = emu.add_machine_frame_notifier(function() fc = fc + 1 end)
local o = io.open(os.getenv("MOUT"), "w")
local lo = tonumber(os.getenv("MLO") or "e8000", 16); local hi = tonumber(os.getenv("MHI") or "e8001", 16)
local f0 = tonumber(os.getenv("MFROM") or "0")
G3MT = sp:install_write_tap(lo, hi, "mt", function(off, data, mask)
  if fc >= f0 then o:write(string.format("%d %06x %04x pc=%06x\n", fc, off, data, cpu.state["CURPC"].value)); o:flush() end
end)
