-- メインROMの読み出しの記録（起動時のROMチェックの後から）＋自動で遊ぶ
-- env: COVOUT 出力 / END 終了フレーム / INV=1 死なない / STG=面(1..) LOOP=周回(1..) PROG=進行度(16進) : 最初の状態2で書く
--      P2=1 2人プレイ / IDLE=1 操作しない（死ぬ） / SVC=1 テストモード / MOVE=1 上下に動く / DSW="port:field:value;..."
local m = manager.machine
local sp = m.devices[":maincpu"].spaces["program"]
local cov = {}
local ram = {}
RAMT1 = sp:install_write_tap(0x40000, 0x43fff, "rw1", function(off, data, mask) if RAMON then local v = ram[off] or 0; if v & 1 == 0 then ram[off] = v | 1 end; if data ~= 0 and v & 4 == 0 then ram[off] = (ram[off]) | 4 end end end)
RAMT2 = sp:install_write_tap(0x100000, 0x103fff, "rw2", function(off, data, mask) if RAMON then local v = ram[off] or 0; if v & 1 == 0 then ram[off] = v | 1 end; if data ~= 0 and v & 4 == 0 then ram[off] = (ram[off]) | 4 end end end)
RAMT3 = sp:install_read_tap(0x40000, 0x43fff, "rr1", function(off) if RAMON then local v = ram[off] or 0; if v & 2 == 0 then ram[off] = v | 2 end end end)
RAMT4 = sp:install_read_tap(0x100000, 0x103fff, "rr2", function(off) if RAMON then local v = ram[off] or 0; if v & 2 == 0 then ram[off] = v | 2 end end end)
local ssp = m.devices[":sub"].spaces["program"]
RAMT5 = ssp:install_write_tap(0x200000, 0x203fff, "sw2", function(off, data, mask) if RAMON then off = off - 0x100000; local v = ram[off] or 0; if v & 1 == 0 then ram[off] = v | 1 end; if data ~= 0 and v & 4 == 0 then ram[off] = (ram[off]) | 4 end end end)
RAMT6 = ssp:install_read_tap(0x200000, 0x203fff, "sr2", function(off) if RAMON then off = off - 0x100000; local v = ram[off] or 0; if v & 2 == 0 then ram[off] = v | 2 end end end)
local cleared = false
COVTAP = sp:install_read_tap(0, 0x3ffff, "cov", function(off) cov[off >> 1] = true end)
local P = m.ioport.ports
local function fld(p, f) return P[p].fields[f] end
local COIN, ST1, ST2 = fld(":SYSTEM","Coin 1"), fld(":SYSTEM","1 Player Start"), fld(":SYSTEM","2 Players Start")
local B1, B2, B3 = fld(":P1","P1 Button 1"), fld(":P1","P1 Button 2"), fld(":P1","P1 Button 3")
local U, D, L, R = fld(":P1","P1 Up"), fld(":P1","P1 Down"), fld(":P1","P1 Left"), fld(":P1","P1 Right")
local Q1, Q2 = fld(":P2","P2 Button 1"), fld(":P2","P2 Button 2")
for spec in (os.getenv("DSW") or ""):gmatch("[^;]+") do
  local p, f, v = spec:match("([^:]+):([^:]+):(%d+)"); fld(":" .. p, f).user_value = tonumber(v)
end
local END = tonumber(os.getenv("END") or "20000")
local INV, IDLE, P2, MOVE = os.getenv("INV"), os.getenv("IDLE"), os.getenv("P2"), os.getenv("MOVE")
local STG, LOOP, PROG = tonumber(os.getenv("STG") or "0"), tonumber(os.getenv("LOOP") or "1"), tonumber(os.getenv("PROG") or "0", 16)
local INVOFF = tonumber(os.getenv("INVOFF") or "")
local fr, poked, lastst = 0, false, 0
local rng = 12345
local function rnd(n) rng = (rng * 1103515245 + 12345) % 2147483648; return rng % n end
local hold = {}
local function press(f, n) f:set_value(1); hold[f] = fr + (n or 4) end
COVF = emu.add_machine_frame_notifier(function()
  fr = fr + 1
  if not cleared and m.time.seconds > 12 then
    cleared = true; cov = {}; RAMON = true
    if INV then local rg = m.memory.regions[":maincpu"]
      for a, hx in ("7bc4:4268001a602a4e71,ae22:4268001a60284e71"):gmatch("(%x+):(%x+)") do
        a = tonumber(a, 16); for i = 0, #hx // 4 - 1 do rg:write_u16(a + i*2, tonumber(hx:sub(i*4+1, i*4+4), 16)) end end end
  end
  if INVOFF and fr == INVOFF then IDLE = true; local rg = m.memory.regions[":maincpu"]
    for a, hx in ("7bc4:13fc0001000400a2,ae22:13fc0001000400a2"):gmatch("(%x+):(%x+)") do
      a = tonumber(a, 16); for i = 0, #hx // 4 - 1 do rg:write_u16(a + i*2, tonumber(hx:sub(i*4+1, i*4+4), 16)) end end end
  for f, t in pairs(hold) do if fr >= t then f:clear_value(); hold[f] = nil end end
  local st = sp:read_u8(0x40029)
  if STG > 0 and not poked and st == 2 and lastst ~= 2 then
    poked = true
    for _, b in ipairs({0x101000, 0x101080}) do
      sp:write_u8(b + 0x51, STG - 1); sp:write_u8(b + 0x63, (LOOP - 1) * 2 + 1); sp:write_u16(b + 0x52, PROG) end
  end
  lastst = st
  if fr >= 1400 and fr % 900 == 0 then press(COIN, 6) end
  if fr >= 1500 and fr % 900 == 100 then press(P2 and ST2 or ST1, 6) end
  if IDLE and st == 1 and fr % 120 == 0 then press(B1, 3) end
  if not IDLE and fr > 1500 then
    if fr % 4 == 0 then press(B2, 2) end
    if fr % 8 == 2 then press(B3, 2) end
    if fr % 240 == 7 then press(B1, 3) end
    if P2 and fr % 4 == 1 then press(Q2, 2) end
    if P2 and fr % 300 == 9 then press(Q1, 3) end
    if MOVE and fr % 60 == 0 then local k = ({U, D, L, R})[rnd(4) + 1]; press(k, 10 + rnd(30)) end
  end
  if fr % 2000 == 0 then print(string.format("F %d top=%x st=%x stg=%x prog=%x loop=%x lives=%x", fr, sp:read_u8(0x40005), st, sp:read_u8(0x101051), sp:read_u16(0x101052), sp:read_u8(0x101063), sp:read_u8(0x101050))) end
  if fr >= END then m:exit() end
end)
COVSTOP = emu.add_machine_stop_notifier(function()
  local r = {}
  for a = 0x40000, 0x43fffe, 2 do end
  for _, base in ipairs({0x40000, 0x100000}) do for a = base, base + 0x3ffe, 2 do r[#r+1] = string.char(ram[a] or 0) end end
  local g = io.open(os.getenv("COVOUT") .. ".ram", "wb"); g:write(table.concat(r)); g:close()
  local t = {}
  for i = 0, 0x1ffff do t[#t+1] = cov[i] and "\1" or "\0" end
  local f = io.open(os.getenv("COVOUT"), "wb"); f:write(table.concat(t)); f:close()
end)
