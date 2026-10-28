-- #32: 面クリアで サブが段14・桁21 の文字を「番号→属性」の順に書き換える間に、メインの地形の判定が入ったらどうなるか
-- DELAY=1 のとき、その属性の書き込みを1フレーム遅らせる（＝サブの割り込み処理が長くかかった場合の再現）
-- RESTORE_AT=フレーム: そのフレームで無敵（ROM 書き換え）を外す
local m = manager.machine
local sub = m.devices[":sub"].spaces["program"]
local main = m.devices[":maincpu"].spaces["program"]
local rg = m.memory.regions[":maincpu"]
local fr = 0
local RA = tonumber(os.getenv("RESTORE_AT") or "0")
local DL = os.getenv("DELAY") == "1"
local pend = nil
DL_N = emu.add_machine_frame_notifier(function()
  fr = fr + 1
  if fr == RA then rg:write_u16(0x7bc4, 0x13fc); rg:write_u16(0x7bc6, 0x0001); rg:write_u16(0x7bc8, 0x0004); rg:write_u16(0x7bca, 0x00a2)
    rg:write_u16(0xae22, 0x13fc); rg:write_u16(0xae24, 0x0001); rg:write_u16(0xae26, 0x0004); rg:write_u16(0xae28, 0x00a2) end
  if pend and fr == pend[1] then sub:write_u8(0x24e72b, pend[2]); print(string.format("frame %d: 遅らせた属性 %02x を書いた", fr, pend[2])); pend = nil end
end)
DL_T = sub:install_write_tap(0x24e72a, 0x24e72b, "dl", function(o, d, mask)
  if DL and main:read_u8(0x40029) == 7 and not pend and (d & 0xff) == 0x0d then
    pend = {fr + 2, d & 0xff}
    print(string.format("frame %d: サブの属性の書き込み %x を遅らせる (pc=%x)", fr + 1, d, m.devices[":sub"].state["PC"].value))
    return 0
  end
end)
dofile(os.getenv("G3RUN2"))
