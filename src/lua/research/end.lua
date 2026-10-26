local f=0
G3N = emu.add_machine_frame_notifier(function() f=f+1
  if f==300 then manager.machine.ioport.ports[":SYSTEM"].fields["Coin 1"]:set_value(1) end
  if f==310 then manager.machine.ioport.ports[":SYSTEM"].fields["Coin 1"]:clear_value() end
  if f==400 then manager.machine.ioport.ports[":SYSTEM"].fields["1 Player Start"]:set_value(1) end
  if f==410 then manager.machine.ioport.ports[":SYSTEM"].fields["1 Player Start"]:clear_value() end
  if f>=3600 then manager.machine:exit() end end)
