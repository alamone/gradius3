dofile(os.getenv("G3LUA"))
local main = manager.machine.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("CTOUT"), "w")
local f = 0
G3PL = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f >= 2200 and f % 10 == 0 then
    out:write(string.format("%d st=%02x top=%02x de=%08x 52=%04x 50=%02x cubes=%04x 101a=%04x 1069=%02x\n", f, main:read_u8(0x101051), main:read_u8(0x40005), main:read_u32(0x1038de), main:read_u16(0x101052), main:read_u8(0x101050), main:read_u16(0x103e36), main:read_u16(0x10101a), main:read_u8(0x101069))); out:flush()
  end
end)
