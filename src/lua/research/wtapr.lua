dofile(os.getenv("G3LUA"))
local cpu = manager.machine.devices[":maincpu"]
local sp = cpu.spaces["program"]
local fcount = 0
local o = io.open(os.getenv("WOUT"), "w")
G3WF = emu.add_machine_frame_notifier(function() fcount = fcount + 1 end)
local lo = tonumber(os.getenv("WLO"), 16); local hi = tonumber(os.getenv("WHI"), 16)
local f0 = tonumber(os.getenv("WF0") or "0")
G3WT = sp:install_write_tap(lo, hi, "wt", function(off, data, mask)
  if fcount < f0 then return end
  local ok, a7 = pcall(function() return cpu.state["SP"].value end)
  if not ok then o:write("ERR "..tostring(a7).."\n"); o:flush(); return end
  local r = {}
  for i = 0, 7 do r[#r+1] = string.format("%08x", sp:read_u32(a7 + i*4)) end
  o:write(string.format("%d %06x %04x pc=%06x st=%s\n", fcount, off, data, cpu.state["CURPC"].value, table.concat(r, " ")))
  o:flush()
end)
