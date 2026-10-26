dofile(os.getenv("G3LUA"))
local sub = manager.machine.devices[":sub"].spaces["program"]
local f = 0
local out = io.open(os.getenv("CTOUT"), "w")
local A = {}
for a = 0x100000, 0x103ff0, 0x10 do A[#A+1] = a end
G3SP = emu.add_machine_frame_notifier(function()
  f = f + 1
  if f == 1000 then for _, a in ipairs(A) do if sub:read_u8(a+15) == 0 then sub:write_u8(a+15, 0xa5) end end end
  if f == 4790 then for _, a in ipairs(A) do out:write(string.format("%x %02x\n", a+15, sub:read_u8(a+15))) end out:close() end
end)
