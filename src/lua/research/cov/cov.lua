-- メインROM(0〜0x3ffff)の読み出し(命令の取り込みも含む)を数える。COVOUT=出力ファイル（1語=1バイト 0/1）
local m = manager.machine
local sp = m.devices[":maincpu"].spaces["program"]
local cov = {}
COVTAP = sp:install_read_tap(0, 0x3ffff, "cov", function(off, data, mask) cov[off >> 1] = true end)
local ram = {}
RAMT1 = sp:install_write_tap(0x40000, 0x43fff, "rw1", function(off, data, mask) if RAMON then local v = ram[off] or 0; if v & 1 == 0 then ram[off] = v | 1 end; if data ~= 0 and v & 4 == 0 then ram[off] = (ram[off]) | 4 end end end)
RAMT2 = sp:install_write_tap(0x100000, 0x103fff, "rw2", function(off, data, mask) if RAMON then local v = ram[off] or 0; if v & 1 == 0 then ram[off] = v | 1 end; if data ~= 0 and v & 4 == 0 then ram[off] = (ram[off]) | 4 end end end)
RAMT3 = sp:install_read_tap(0x40000, 0x43fff, "rr1", function(off) if RAMON then local v = ram[off] or 0; if v & 2 == 0 then ram[off] = v | 2 end end end)
RAMT4 = sp:install_read_tap(0x100000, 0x103fff, "rr2", function(off) if RAMON then local v = ram[off] or 0; if v & 2 == 0 then ram[off] = v | 2 end end end)
local ssp = m.devices[":sub"].spaces["program"]
RAMT5 = ssp:install_write_tap(0x200000, 0x203fff, "sw2", function(off, data, mask) if RAMON then off = off - 0x100000; local v = ram[off] or 0; if v & 1 == 0 then ram[off] = v | 1 end; if data ~= 0 and v & 4 == 0 then ram[off] = (ram[off]) | 4 end end end)
RAMT6 = ssp:install_read_tap(0x200000, 0x203fff, "sr2", function(off) if RAMON then off = off - 0x100000; local v = ram[off] or 0; if v & 2 == 0 then ram[off] = v | 2 end end end)
local cleared=false
COVCLR = emu.add_machine_frame_notifier(function() if not cleared and m.time.seconds > (tonumber(os.getenv("COVT") or "12")) then cleared=true; cov={}; RAMON=true end end)
COVSTOP = emu.add_machine_stop_notifier(function()
  local r = {}
  for a = 0x40000, 0x43fffe, 2 do end
  for _, base in ipairs({0x40000, 0x100000}) do for a = base, base + 0x3ffe, 2 do r[#r+1] = string.char(ram[a] or 0) end end
  local g = io.open(os.getenv("COVOUT") .. ".ram", "wb"); g:write(table.concat(r)); g:close()
  local t = {}
  for i = 0, 0x1ffff do t[#t+1] = cov[i] and "\1" or "\0" end
  local f = io.open(os.getenv("COVOUT"), "wb"); f:write(table.concat(t)); f:close()
end)
dofile(os.getenv("G3RUN"))
