dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local sub = manager.machine.devices[":sub"].spaces["program"]
local f = 0
local acc = {}
local on = false
local function mark(base) return function(off, data, mask)
  if on then local a = off - base; acc[a] = true; acc[a+1] = true end
end end
G3T1 = main:install_read_tap(0x100000, 0x103fff, "mr", mark(0x100000))
G3T2 = main:install_write_tap(0x100000, 0x103fff, "mw", mark(0x100000))
G3T3 = sub:install_read_tap(0x200000, 0x203fff, "sr", mark(0x200000))
G3T4 = sub:install_write_tap(0x200000, 0x203fff, "sw", mark(0x200000))
G3AC = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f == tonumber(os.getenv("ACC0")) then on = true end
  if f == tonumber(os.getenv("ACC1")) then
    local o = io.open(os.getenv("CTOUT"), "w")
    for a = 0, 0x3fff do o:write(acc[a] and "1" or "0") end
    o:close()
  end
end)
