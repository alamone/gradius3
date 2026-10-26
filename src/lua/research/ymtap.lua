local m = manager.machine
local a = m.devices[":audiocpu"].spaces["program"]
local out = io.open(os.getenv("YMOUT") or "runs/ym.txt", "w")
local reg = 0
local f = 0
local pan = {}
G3YT = a:install_write_tap(0xf030, 0xf031, "ym", function(offset, data, mask)
  if offset == 0xf030 then reg = data
  elseif reg >= 0x20 and reg <= 0x27 then
    local k = reg .. ":" .. (data >> 6)
    if not pan[k] then pan[k] = true; out:write(string.format("%d ch%d RL=%d (val %02x)\n", f, reg - 0x20, data >> 6, data)); out:flush() end
  end
  return data
end)
G3YN = emu.add_machine_frame_notifier(function() f = f + 1 end)
