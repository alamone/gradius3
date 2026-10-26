local snd = manager.machine.devices[":audiocpu"].spaces["program"]
local f = 0; local addr = 0
local out = io.open(os.getenv("OUT"), "w")
local tap = snd:install_write_tap(0xf030, 0xf031, "ym", function(off, data, mask)
  if off == 0xf030 then addr = data else
    if (addr >= 0x20 and addr <= 0x27) or addr == 0x08 then out:write(string.format("%d %02x %02x\n", f, addr, data)) end
  end
end)
local tap2 = snd:install_write_tap(0xf020, 0xf02d, "kk", function(off, data, mask) end)
local END = tonumber(os.getenv("END") or "6000")
local seq = {}
for fr, k in (os.getenv("SEQ") or ""):gmatch("(%d+):(%w+)") do seq[tonumber(fr)] = k end
local P = manager.machine.ioport.ports
emu.register_frame_done(function()
  f = f + 1
  if f >= END then out:close(); manager.machine:exit() end
end)
