local cpu = manager.machine.devices[":maincpu"]
local sp = cpu.spaces["program"]
local hits = {}
local f = 0
local tap = sp:install_read_tap(0xd650, 0xd8f7, "rt", function(off, data, mask)
  local k = string.format("%x", off)
  if not hits[k] then hits[k] = f end
end)
local END = tonumber(os.getenv("END") or "20000")
local done = false
emu.register_frame_done(function()
  f = f + 1
  if f >= END and not done then
    done = true
    local out = io.open(os.getenv("TAPOUT"), "w")
    if out then
      out:write("frames " .. f .. "\n")
      for k, v in pairs(hits) do out:write(k .. " " .. v .. "\n") end
      out:close()
    end
    manager.machine:exit()
  end
end)
