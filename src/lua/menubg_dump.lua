-- メニュー背景の材料（src/mods/menubg/*_<F>.bin）を、純正ROMを動かして記録する。
-- ROM 由来のデータなのでリポジトリには入れず、ビルドのたびにこのスクリプトで作る（tools/menubg_dump.sh）。
-- env: FRAME=7440（記録するフレーム）  OUTDIR=保存先  SEQ=入力列（g3run.lua と同じ形。既定は入力なし）
local m = manager.machine
local main = m.devices[":maincpu"].spaces["program"]
local sub = m.devices[":sub"].spaces["program"]
local F = tonumber(os.getenv("FRAME") or "7440")
local OUT = os.getenv("OUTDIR") or "."
local sysf = m.ioport.ports[":SYSTEM"].fields
local p1 = m.ioport.ports[":P1"].fields
local K = { COIN=sysf["Coin 1"], START=sysf["1 Player Start"], U=p1["P1 Up"], D=p1["P1 Down"], L=p1["P1 Left"], R=p1["P1 Right"],
  B1=p1["P1 Button 1"], B2=p1["P1 Button 2"], B3=p1["P1 Button 3"] }
local press, release = {}, {}
for f, k in (os.getenv("SEQ") or ""):gmatch("(%d+):(%w+)") do
  f = tonumber(f); press[f] = press[f] or {}; table.insert(press[f], k)
  release[f + 8] = release[f + 8] or {}; table.insert(release[f + 8], k)
end
local function save(name, sp, lo, hi)
  local f = io.open(OUT .. "/" .. name .. "_" .. F .. ".bin", "wb")
  f:write(sp:read_range(lo, hi, 8)); f:close()
end
local frame = 0
emu.register_frame_done(function()
  frame = frame + 1
  for _, k in ipairs(press[frame] or {}) do K[k]:set_value(1) end
  for _, k in ipairs(release[frame] or {}) do K[k]:set_value(0) end
  if frame == F then
    save("vram", main, 0x14c000, 0x153fff)   -- K052109 タイルRAM（16bit の下位バイト側）
    save("chr",  main, 0x180000, 0x19ffff)   -- 文字（タイル）RAM
    save("pal",  main, 0x080000, 0x080fff)   -- 色
    save("spr",  sub,  0x2c0800, 0x2c0fff)   -- K051960 スプライト表（16bit の下位バイト側）
    print("menubg dump done at frame " .. F)
    m:exit()
  end
end)
