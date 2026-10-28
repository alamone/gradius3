-- 60フレームごとに 状態・面・画面の位置($1038de)・進行度($101052)・自機の状態 を出す
local m=manager.machine; local sp=m.devices[":maincpu"].spaces["program"]; local f=0
PL=emu.add_machine_frame_notifier(function() f=f+1
  if f%30==0 then print(string.format("POS %d st=%x/%x stg=%x x=%06x prog=%04x ship=%x lives=%x", f, sp:read_u8(0x40029), sp:read_u8(0x4002b), sp:read_u8(0x101051), sp:read_u32(0x1038de)>>8, sp:read_u16(0x101052), sp:read_u8(0x101001), sp:read_u8(0x101050))) end end)
dofile(os.getenv("G3RUN"))
