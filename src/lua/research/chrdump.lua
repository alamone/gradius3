dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local f=0
G3CD = emu.add_machine_frame_notifier(function()
  f=f+1
  if f == tonumber(os.getenv("AT")) then local o=io.open(os.getenv("CTOUT"),"wb"); o:write(main:read_range(0x180000,0x181fff,8)); o:close() end
end)
