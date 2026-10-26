local mainsp = manager.machine.devices[":maincpu"].spaces["program"]
local f = 0
local code = tonumber(os.getenv("BGM") or "a0", 16)
local START = tonumber(os.getenv("BSTART") or "1000")
local END = START + tonumber(os.getenv("BLEN") or "1800")
emu.register_frame_done(function()
  f = f + 1
  if f == START then mainsp:write_u16(0xe8000, code * 257); mainsp:write_u16(0xf0000, 0) end
  if f >= END then manager.machine:exit() end
end)
