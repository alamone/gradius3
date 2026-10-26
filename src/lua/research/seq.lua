local mainsp = manager.machine.devices[":maincpu"].spaces["program"]
local f = 0
local codes = {}
for c in (os.getenv("CODES") or ""):gmatch("%x+") do codes[#codes + 1] = tonumber(c, 16) end
local START, LEN, GAP = 1000, 1920, 90
local function send(c) mainsp:write_u16(0xe8000, c * 257); mainsp:write_u16(0xf0000, 0) end
emu.register_frame_done(function()
  f = f + 1
  if f < START then return end
  local k = (f - START) // (LEN + GAP)
  local r = (f - START) % (LEN + GAP)
  if k >= #codes then manager.machine:exit() return end
  if r == 0 then send(codes[k + 1]) end
  if r == LEN then send(0xff) end
  if r == LEN + 20 then send(0x00) end
end)
