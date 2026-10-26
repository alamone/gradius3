local m = manager.machine
local main = m.devices[":maincpu"].spaces["program"]
local sysf = m.ioport.ports[":SYSTEM"].fields
local coin = sysf["Coin 1"]
local svc = m.ioport.ports[":DSW3"].fields["Service Mode"]
local SVCF = tonumber(os.getenv("SVC") or "0")
local FR = tonumber(os.getenv("FR") or "1450")
local OUT = os.getenv("TOUT") or "tile.txt"
local f = 0
G3N = emu.add_machine_frame_notifier(function()
  f = f + 1; if f%200==0 then local g=io.open("runs/tile_prog.txt","a"); g:write(f,"\n"); g:close() end
  if SVCF>0 and f == SVCF then svc:set_value(1) end
  if SVCF==0 and f == 1300 then coin:set_value(1) end
  if f == 1310 then coin:set_value(0) end
  if f == FR then
    if os.getenv("SNAPIT") then m.video:snapshot() end
    local o = io.open(OUT, "w")
    local D = main:read_range(0x14c000, 0x153fff, 8)
    for li, base in ipairs({0, 0x1000, 0x2000}) do
      for row = 0, 31 do
        local line = {}
        for col = 0, 63 do
          local a = base + (row*64+col)*2
          line[#line+1] = string.format("%02x/%02x", D:byte(a+2), D:byte(a+0x4002))
        end
        o:write(string.format("L%d r%02d %s\n", li, row, table.concat(line, " ")))
      end
    end
    local P = main:read_range(0x80000, 0x80000+511, 8)
    local p = {}
    for i = 0, 255 do p[#p+1] = string.format("%02x%02x", P:byte(i*2+1), P:byte(i*2+2)) end
    o:write("PAL " .. table.concat(p, " ") .. "\n")
    o:close()
    m:exit()
  end
end)
