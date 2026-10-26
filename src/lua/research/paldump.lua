dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local f=0
G3PD = emu.add_machine_frame_notifier(function()
  f=f+1
  if f == 3300 then
    local t={} for a=0x800c0,0x800de,2 do t[#t+1]=string.format("%04x", main:read_u16(a)) end
    local u={} for a=0x103dec,0x103dfe,2 do u[#u+1]=string.format("%04x", main:read_u16(a)) end
    local o=io.open(os.getenv("CTOUT"),"w"); o:write("pal6 "..table.concat(t," ").."\nbuf "..table.concat(u," ").."\n"); o:close()
  end
end)
