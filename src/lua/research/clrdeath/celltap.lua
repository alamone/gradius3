local m = manager.machine
local main = m.devices[":maincpu"].spaces["program"]
local sub = m.devices[":sub"].spaces["program"]
local fr = 0
local F0, F1 = tonumber(os.getenv("CT0")), tonumber(os.getenv("CT1"))
local lf = io.open(os.getenv("TAPLOG"), "w")
CT_N = emu.add_machine_frame_notifier(function() fr = fr + 1; if fr >= F0 and fr <= F1 then lf:write(string.format("---- frame %d end t=%s\n", fr, tostring(m.time))) end end)
local function on() return fr + 1 >= F0 and fr + 1 <= F1 end
CT1 = main:install_write_tap(0x14e72a, 0x14e72b, "ma", function(o, d) if on() then lf:write(string.format("%d M attr %x=%x t=%s pc=%x\n", fr+1, o, d, tostring(m.time), m.devices[":maincpu"].state["PC"].value)) end end)
CT2 = main:install_write_tap(0x15272a, 0x15272b, "mc", function(o, d) if on() then lf:write(string.format("%d M code %x=%x t=%s pc=%x\n", fr+1, o, d, tostring(m.time), m.devices[":maincpu"].state["PC"].value)) end end)
CT3 = sub:install_write_tap(0x24c000, 0x253fff, "sv", function(o, d) if on() and ((o & 0x7ff) == 0x72a or (o & 0x7ff) == 0x72b) then lf:write(string.format("%d S vram %x=%x t=%s pc=%x\n", fr+1, o, d, tostring(m.time), m.devices[":sub"].state["PC"].value)) end end)
CT4 = main:install_write_tap(0x1039d0, 0x1039d1, "chk", function(o, d) if on() then lf:write(string.format("%d M check t=%s\n", fr+1, tostring(m.time))) end end)
dofile(os.getenv("G3RUN2"))
