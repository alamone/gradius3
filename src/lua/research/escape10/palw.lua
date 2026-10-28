local m=manager.machine; local cpu=m.devices[":maincpu"]; local sp=cpu.spaces["program"]; local pc=cpu.state["CURPC"]; local f=0; local H={}
local A,B=tonumber(os.getenv("PA")),tonumber(os.getenv("PB"))
PW=sp:install_write_tap(0x80000,0x80fff,"pw",function(off,d) if f>=A and f<=B then local k=string.format("%06x",pc.value); local e=H[k]; if not e then H[k]={f,f,1,off,off} else e[2]=f; e[3]=e[3]+1; if off<e[4] then e[4]=off end; if off>e[5] then e[5]=off end end end end)
PF=emu.add_machine_frame_notifier(function() f=f+1; if f==B and os.getenv("PALOUT") then local o=io.open(os.getenv("PALOUT"),"wb"); o:write(sp:read_range(0x80000,0x80fff,8)); o:close() end; if f==B then for k,e in pairs(H) do print(string.format("PALW pc=%s first=%d last=%d n=%d range=%x-%x",k,e[1],e[2],e[3],e[4],e[5])) end end end)
dofile(os.getenv("G3RUN2"))
