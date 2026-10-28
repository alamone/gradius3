-- 純正: 状態2に入った最初のフレームで 面・進行度(PROG)・周回 を書き、起動12秒後に死なないパッチ（INV=1）
local m=manager.machine; local sp=m.devices[":maincpu"].spaces["program"]; local f=0; local done=false; local last=0; local p=false
GS=emu.add_machine_frame_notifier(function() f=f+1
  if os.getenv("INV") and not p and m.time.seconds>12 then p=true; local rg=m.memory.regions[":maincpu"]
    for a,hx in ("7bc4:4268001a602a4e71,ae22:4268001a60284e71"):gmatch("(%x+):(%x+)") do a=tonumber(a,16); for i=0,#hx//4-1 do rg:write_u16(a+i*2,tonumber(hx:sub(i*4+1,i*4+4),16)) end end end
  local st=sp:read_u8(0x40029)
  if not done and st==2 and last~=2 then done=true; local s=tonumber(os.getenv("STG"))-1; local pr=tonumber(os.getenv("PROG"),16)
    for _,b in ipairs({0x101000,0x101080}) do sp:write_u8(b+0x51,s); sp:write_u8(b+0x63,1); sp:write_u16(b+0x52,pr) end end
  last=st end)
dofile(os.getenv("NEXT"))
