-- 汎用: 入力列(SEQ) / RAM書込(POKE) / 値監視(WATCH) / スナップ(SNAP) / 書込み集合(WSET) / RAMダンプ(DUMPAT)
-- env: SEQ="f:KEY,..."  KEY=COIN START START2 U D L R B1 B2 B3 COIN3 SVC; hold=HOLD(既定8)
--      POKE="f:addr:val[:w],..." (16進, メインCPU空間; :w で16bit)
--      WATCH="addr,addr"  (メイン空間 u8)   END=終了フレーム
--      WSET=out.txt  : 全期間のメイン/サブ共有RAM・メインRAMの書込みバイト集合(最初と最後のフレーム付き)を出力
--      DUMPAT="f,f" OUT=prefix  : f フレーム時点でメインRAM(0x40000-0x43fff)+共有RAM(0x100000-0x103fff)を保存
--      SNAP="s:e:i"  OUTLOG=file (printの代わりにファイルへ)
local m = manager.machine
local sysf = m.ioport.ports[":SYSTEM"].fields
local p1 = m.ioport.ports[":P1"].fields
local dsw3 = m.ioport.ports[":DSW3"].fields
local F = { COIN=sysf["Coin 1"], COIN3=sysf["Coin 3"], START=sysf["1 Player Start"], START2=sysf["2 Players Start"],
  U=p1["P1 Up"], D=p1["P1 Down"], L=p1["P1 Left"], R=p1["P1 Right"],
  B1=p1["P1 Button 1"], B2=p1["P1 Button 2"], B3=p1["P1 Button 3"] }
local main = m.devices[":maincpu"].spaces["program"]
local sub = m.devices[":sub"] and m.devices[":sub"].spaces["program"]
local HOLD = tonumber(os.getenv("HOLD") or "8")
local press, release = {}, {}
for f, k in (os.getenv("SEQ") or ""):gmatch("(%d+):(%w+)") do
  f = tonumber(f); press[f] = press[f] or {}; table.insert(press[f], k)
  release[f+HOLD] = release[f+HOLD] or {}; table.insert(release[f+HOLD], k)
end
-- HOLDK: "f:KEY:len" 形式で保持長指定
for f, k, l in (os.getenv("HOLDK") or ""):gmatch("(%d+):(%w+):(%d+)") do
  f = tonumber(f); l = tonumber(l)
  press[f] = press[f] or {}; table.insert(press[f], k)
  release[f+l] = release[f+l] or {}; table.insert(release[f+l], k)
end
local pokes = {}
for f, a, v, w in (os.getenv("POKE") or ""):gmatch("(%d+):(%x+):(%x+):?(w?)") do
  table.insert(pokes, {tonumber(f), tonumber(a, 16), tonumber(v, 16), w == "w"}) end
local swatch = {}
for a in (os.getenv("SWATCH") or ""):gmatch("[^,]+") do table.insert(swatch, tonumber(a, 16)) end
local watch = {}
for a in (os.getenv("WATCH") or ""):gmatch("[^,]+") do table.insert(watch, tonumber(a, 16)) end
local s0, s1, si = (os.getenv("SNAP") or "0:0:1"):match("(%d+):(%d+):(%d+)")
s0, s1, si = tonumber(s0), tonumber(s1), tonumber(si)
local END = tonumber(os.getenv("END") or "3000")
local at = {}
for f in (os.getenv("DUMPAT") or ""):gmatch("%d+") do at[tonumber(f)] = true end
local OUT = os.getenv("DUMPPREFIX") or os.getenv("OUT") or "dump"
local logf = os.getenv("OUTLOG") and io.open(os.getenv("OUTLOG"), "w") or nil
local function P(...) local s = table.concat({...}, " "); if logf then logf:write(s, "\n") else print(s) end end

local frame = 0
-- write-set tracking (サンプリング差分方式)
local wset = os.getenv("WSET")
local SAMP = tonumber(os.getenv("WSAMP") or "2")
local W = {}
local prev = {}
local regions = {
  {"M", main, 0x40000, 0x43fff},
  {"S", main, 0x100000, 0x103fff},
}
if sub then table.insert(regions, {"R", sub, 0x100000, 0x103fff}) end
local function sample()
  for _, r in ipairs(regions) do
    local tag, sp, lo, hi = r[1], r[2], r[3], r[4]
    local cur = sp:read_range(lo, hi, 8)
    local pv = prev[tag]
    if pv and pv ~= cur then
      for i = 1, #cur do
        local c = cur:byte(i)
        if c ~= pv:byte(i) then
          local k = tag .. string.format("%06x", lo + i - 1)
          local e = W[k]
          if e then e[2] = frame; e[3] = e[3] + 1 else W[k] = {frame, frame, 1} end
        end
      end
    end
    prev[tag] = cur
  end
end

local notif = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  for _, k in ipairs(press[frame] or {}) do F[k]:set_value(1) end
  for _, k in ipairs(release[frame] or {}) do F[k]:clear_value() end
  for _, p in ipairs(pokes) do if p[1] == frame then
    if p[4] then main:write_u16(p[2], p[3]) else main:write_u8(p[2], p[3]) end end end
  if #watch > 0 then
    local t = {}
    for _, a in ipairs(watch) do t[#t+1] = string.format("%x=%02x", a, main:read_u8(a)) end
    for _, a in ipairs(swatch) do t[#t+1] = string.format("s%x=%02x", a, sub:read_u8(a)) end
    local s = table.concat(t, " ")
    if s ~= (G3LAST or "") then P(frame, s); G3LAST = s end
  end
  if wset and frame % SAMP == 0 then sample() end
  if at[frame] then
    local f = io.open(string.format("%s_%d.bin", OUT, frame), "wb"); local t = {}
    for a = 0x40000, 0x43fff do t[#t+1] = string.char(main:read_u8(a)) end
    for a = 0x100000, 0x103fff do t[#t+1] = string.char(main:read_u8(a)) end
    f:write(table.concat(t)); f:close()
    local g = io.open(OUT .. string.format('_gfx_%d.bin', frame), 'wb'); g:write(main:read_range(0x14c000, 0x153fff, 8)); g:close()
    local q = io.open(OUT .. string.format('_pal_%d.bin', frame), 'wb'); q:write(main:read_range(0x80000, 0x80fff, 8)); q:close()
  end
  if frame >= s0 and frame <= s1 and (frame - s0) % si == 0 then m.video:snapshot() end
  if frame >= END then
    if wset then
      local f = io.open(wset, "w")
      for k, e in pairs(W) do f:write(string.format("%s %d %d %d\n", k, e[1], e[2], e[3])) end
      f:close()
    end
    if logf then logf:close() end
    m:exit()
  end
end)
G3NOTIF = notif

-- SHOTAT="f,f": 画面を PPM で保存 (runs/shot_<f>.ppm)  ※ video none でも scr:pixels() で取得可
local shots = {}
for f in (os.getenv("SHOTAT") or ""):gmatch("%d+") do shots[tonumber(f)] = true end
local scr
for k, v in pairs(m.screens) do scr = v; break end
local shotdir = os.getenv("SHOTDIR") or "runs"
G3SHOT = emu.add_machine_frame_notifier(function()
  if shots[frame] then
    local w, h = scr.width, scr.height
    local px = scr:pixels()
    local o = io.open(string.format("%s/shot_%d.ppm", shotdir, frame), "wb")
    o:write(string.format("P6\n%d %d\n255\n", w, h))
    local t = {}
    for i = 0, w*h-1 do
      local v = string.unpack("<I4", px, i*4+1)
      t[#t+1] = string.char((v>>16)&255, (v>>8)&255, v&255)
    end
    o:write(table.concat(t)); o:close()
  end
end)
