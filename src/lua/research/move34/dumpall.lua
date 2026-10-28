local m=manager.machine; local sp=m.devices[":maincpu"].spaces["program"]; local ss=m.devices[":sub"].spaces["program"]; local f=0
local A,B=tonumber(os.getenv("DA")),tonumber(os.getenv("DB"))
DD=emu.add_machine_frame_notifier(function() f=f+1; if f>=A and f<=B and (f-A)%(tonumber(os.getenv("DS") or "1"))==0 then local o=io.open(os.getenv("DO").."/f"..f..".bin","wb"); o:write(sp:read_range(0x40000,0x43fff,8)); o:write(sp:read_range(0x100000,0x103fff,8)); o:write(ss:read_range(0x100000,0x103fff,8)); o:write(sp:read_range(0x80000,0x80fff,8)); if os.getenv("CHR") then o:write(sp:read_range(0x180000,0x19ffff,8)) end; o:close() end end)
dofile(os.getenv("G3RUN"))
