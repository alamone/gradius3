local m = manager.machine
local scr
for k,v in pairs(m.screens) do scr = v; break end
local FR = tonumber(os.getenv("FR") or "600")
local sysf = m.ioport.ports[":SYSTEM"].fields
local f = 0
G3N = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f == FR then
    local w, h = scr.width, scr.height
    local px = scr:pixels()
    local o = io.open(os.getenv("PIXOUT") or "runs/pix.ppm", "wb")
    o:write(string.format("P6\n%d %d\n255\n", w, h))
    local t = {}
    for i = 0, w*h-1 do
      local v = string.unpack("<I4", px, i*4+1)
      t[#t+1] = string.char((v>>16)&255, (v>>8)&255, v&255)
    end
    o:write(table.concat(t)); o:close()
    local l = io.open("runs/pix.log","w"); l:write(w," ",h," ",#px,"\n"); l:close()
    m:exit()
  end
end)
