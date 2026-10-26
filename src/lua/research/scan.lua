local mainsp = manager.machine.devices[":maincpu"].spaces["program"]
local f = 0
local START, STEP = 1000, 600
local LAST = tonumber(os.getenv("LASTCODE") or "255")
local function send(c) mainsp:write_u16(0xe8000, c * 257); mainsp:write_u16(0xf0000, 0) end
emu.register_frame_done(function()
  f = f + 1
  if f >= START then
    local k = (f - START) // STEP
    local r = (f - START) % STEP
    if k > LAST then manager.machine:exit() return end
    if r == 0 then send(k) end
    if r == STEP - 30 then send(0) end
  end
end)
