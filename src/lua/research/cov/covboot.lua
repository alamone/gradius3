-- 起動から T 秒までのメインROMの読み出し。読んだ命令の PC ごとの数も出す（ROM チェックのループを見分ける）
local m = manager.machine
local cpu = m.devices[":maincpu"]
local sp = cpu.spaces["program"]
local cov, pcs = {}, {}
local st = cpu.state["CURPC"]
COVTAP = sp:install_read_tap(0, 0x3ffff, "cov", function(off)
  local pc = st.value
  pcs[pc] = (pcs[pc] or 0) + 1
  if pc < 0x384 or pc > 0x3bc then cov[off >> 1] = true end
end)
local T = tonumber(os.getenv("COVT") or "13")
COVF = emu.add_machine_frame_notifier(function() if m.time.seconds > T then m:exit() end end)
COVSTOP = emu.add_machine_stop_notifier(function()
  local t = {}
  for i = 0, 0x1ffff do t[#t+1] = cov[i] and "\1" or "\0" end
  local f = io.open(os.getenv("COVOUT"), "wb"); f:write(table.concat(t)); f:close()
  local g = io.open(os.getenv("COVOUT") .. ".pc", "w")
  for pc, n in pairs(pcs) do if n > 1000 then g:write(string.format("%06x %d\n", pc, n)) end end
  g:close()
end)
