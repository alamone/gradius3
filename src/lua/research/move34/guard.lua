-- 改造のコードを置いた RAM に、写し終えた後で書き込みがあったら知らせる（メイン・サブ両方）
local m=manager.machine; local cpu=m.devices[":maincpu"]; local sp=cpu.spaces["program"]; local pc=cpu.state["CURPC"]; local f=0
local sub=m.devices[":sub"]; local spc=sub.state["CURPC"]; local n=0
local function ok() return sp:read_u16(0x103abe)==0x4d4f end
local R={{0x40500,0x405df},{0x42e78,0x42fff},{0x43f70,0x43fff},{0x103860,0x1038d3},{0x103966,0x1039bf},{0x1039c6,0x103abb}}
GT={}
for _,r in ipairs(R) do
  GT[#GT+1]=sp:install_write_tap(r[1],r[2],"g"..r[1],function(off) if ok() then n=n+1; if n<20 then print("GUARD main",f,string.format("%x pc=%x",off,pc.value)) end end end)
  if r[1]>=0x100000 then GT[#GT+1]=sub.spaces["program"]:install_write_tap(r[1]+0x100000,r[2]+0x100000,"s"..r[1],function(off) if ok() then n=n+1; if n<20 then print("GUARD sub",f,string.format("%x pc=%x",off,spc.value)) end end end) end
end
GF=emu.add_machine_frame_notifier(function() f=f+1 end)
GS=emu.add_machine_stop_notifier(function() print("GUARD total",n,"frames",f) end)
dofile(os.getenv("G3RUN"))
