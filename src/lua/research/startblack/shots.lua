-- 状態が変わるたびに st.log に記録し、状態2（START 表示）・5（プレイ）に入ってから REL のフレーム後に
-- 画面（PPM）とパレットRAM（.pal）を SHOTDIR に保存する。名前は s<何回目の状態2>_<状態>_<フレーム>。
-- env: SHOTDIR, REL="40,60,300", G3RUN=次に読む Lua（g3run.lua など）
local m=manager.machine; local sp=m.devices[":maincpu"].spaces["program"]; local f=0; local last=-1; local ent=0; local n2=0
local REL={}; for x in (os.getenv("REL") or "40"):gmatch("%d+") do REL[tonumber(x)]=true end
local scr; for k,v in pairs(m.screens) do scr=v; break end
local dir=os.getenv("SHOTDIR"); local log=io.open(dir.."/st.log","w")
local function shot(nm) local w,h=scr.width,scr.height; local px=scr:pixels(); local o=io.open(dir.."/"..nm..".ppm","wb")
  o:write(string.format("P6\n%d %d\n255\n",w,h)); local t={}
  for i=0,w*h-1 do local v=string.unpack("<I4",px,i*4+1); t[#t+1]=string.char((v>>16)&255,(v>>8)&255,v&255) end
  o:write(table.concat(t)); o:close()
  local q=io.open(dir.."/"..nm..".pal","wb"); q:write(sp:read_range(0x80000,0x80fff,8)); q:close() end
SBT=emu.add_machine_frame_notifier(function() f=f+1
  local s=sp:read_u8(0x40029)
  if s~=last then log:write(string.format("%d st=%d stage=%d prog=%04x\n",f,s,sp:read_u8(0x101051),sp:read_u16(0x101052))); log:flush(); last=s; ent=f; if s==2 then n2=n2+1 end end
  if (s==2 or s==5) and REL[f-ent] then shot(string.format("s%d_%d_%03d",n2,s,f-ent)) end
end)
dofile(os.getenv("G3RUN"))
