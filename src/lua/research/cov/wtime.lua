-- 範囲への書き込みが起きたフレーム（とPC）を記録。env RANGES="40d64-41080,43872-43f00"
local m = manager.machine
local cpu = m.devices[":maincpu"]; local sp = cpu.spaces["program"]; local pc = cpu.state["CURPC"]
local fr = 0; local hits = {}
WTAPS = {}
local taps = WTAPS
for a, b in (os.getenv("RANGES")):gmatch("(%x+)-(%x+)") do
  a = tonumber(a, 16); b = tonumber(b, 16)
  taps[#taps+1] = sp:install_write_tap(a, b - 1, "wt" .. a, function(off, data)
    local k = fr .. " " .. string.format("%06x", pc.value) .. " " .. string.format("%x", a)
    hits[k] = (hits[k] or 0) + 1 end)
end
WTF = emu.add_machine_frame_notifier(function() fr = fr + 1 end)
WTS = emu.add_machine_stop_notifier(function()
  local f = io.open(os.getenv("WOUT"), "w"); for k, n in pairs(hits) do f:write(k, " ", n, "\n") end; f:close() end)
dofile(os.getenv("NEXT"))
