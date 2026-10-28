local m=manager.machine; local f=0; local shots={}
for x in (os.getenv("SHOTAT") or ""):gmatch("%d+") do shots[tonumber(x)]=true end
local scr; for k,v in pairs(m.screens) do scr=v; break end
SH=emu.add_machine_frame_notifier(function() f=f+1
  if shots[f] then local w,h=scr.width,scr.height; local px=scr:pixels(); local o=io.open(string.format("%s/shot_%d.ppm",os.getenv("SHOTDIR"),f),"wb")
    o:write(string.format("P6\n%d %d\n255\n",w,h)); local t={}
    for i=0,w*h-1 do local v=string.unpack("<I4",px,i*4+1); t[#t+1]=string.char((v>>16)&255,(v>>8)&255,v&255) end
    o:write(table.concat(t)); o:close() end end)
dofile(os.getenv("G3RUN2"))
