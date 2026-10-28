local m=manager.machine; local sp=m.devices[":maincpu"].spaces["program"]; local f=0
SN=sp:install_write_tap(0x40380,0x403bf,"sn",function(off,d,mk) local v=(mk==0xff00) and (d>>8) or (d&0xff); print("SND",f,string.format("%02x x=%04x",v, sp:read_u32(0x1038de)>>16)) end)
SF=emu.add_machine_frame_notifier(function() f=f+1 end)
dofile(os.getenv("G3RUN2"))
