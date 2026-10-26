dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local f=0
G3CH = emu.add_machine_frame_notifier(function()
  f=f+1
  for fr in (os.getenv("CHAT") or ""):gmatch("%d+") do
    if f == tonumber(fr) then local o=io.open(os.getenv("CTOUT").."_"..fr..".bin","wb"); o:write(main:read_range(0x180000,0x19ffff,8)); o:write(main:read_range(0x100000,0x103fff,8)); o:close() end
  end
end)
