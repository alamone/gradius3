dofile(os.getenv("G3LUA"))
local sub = manager.machine.devices[":sub"]
local sp = sub.spaces["program"]
local hist, fr = {}, {}
local fcount = 0
G3WF = emu.add_machine_frame_notifier(function() fcount = fcount + 1 end)
local lo = tonumber(os.getenv("WLO") or "288000", 16); local hi = tonumber(os.getenv("WHI") or "29ffff", 16)
G3WT = sp:install_write_tap(lo, hi, "wt", function(off, data, mask)
  local pc = sub.state["CURPC"].value
  local k = string.format("%06x", pc)
  hist[k] = (hist[k] or 0) + 1
  if not fr[k] then fr[k] = fcount end
end)
G3WE = emu.add_machine_frame_notifier(function()
  if fcount == tonumber(os.getenv("WEND") or "3000") then
    local o = io.open(os.getenv("WOUT"), "w")
    for k, v in pairs(hist) do o:write(k .. " " .. v .. " first " .. fr[k] .. "\n") end
    o:close()
  end
end)
