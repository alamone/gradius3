-- RAM のコードが写し終わる前に実行されたら知らせる
local m=manager.machine; local cpu=m.devices[":maincpu"]; local sp=cpu.spaces["program"]; local pc=cpu.state["CURPC"]; local f=0; local bad=0
local function chk(off) local p=pc.value; if p==off and sp:read_u16(0x103abe)~=0x4d4f then bad=bad+1; if bad<5 then print("EARLY",f,string.format("%x",p)) end end end
E1=sp:install_read_tap(0x40500,0x405df,"e1",chk); E2=sp:install_read_tap(0x42e78,0x42fff,"e2",chk); E3=sp:install_read_tap(0x43f70,0x43fff,"e3",chk); E4=sp:install_read_tap(0x103812,0x103abb,"e4",chk)
EF=emu.add_machine_frame_notifier(function() f=f+1; if f==900 then print("magic", string.format("%x", sp:read_u16(0x103abe)), "bad", bad) end end)
dofile(os.getenv("G3RUN"))
