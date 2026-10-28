local m=manager.machine; local cpu=m.devices[":maincpu"]; local sp=cpu.spaces["program"]; local pc=cpu.state["CURPC"]; local f=0; local L={}
local function rec(off) if f==tonumber(os.getenv("TF")) then local p=pc.value; if L[#L]~=p then L[#L+1]=p end end end
T1=sp:install_read_tap(0,0x3ffff,"t1",rec); T2=sp:install_read_tap(0x40000,0x43fff,"t2",rec); T3=sp:install_read_tap(0x100000,0x103fff,"t3",rec)
TF=emu.add_machine_frame_notifier(function() f=f+1; if f==tonumber(os.getenv("TF"))+1 then local t={} for i=1,#L do t[#t+1]=string.format("%x",L[i]) end print("TRACE "..table.concat(t," ")) end end)
dofile(os.getenv("G3RUN"))
