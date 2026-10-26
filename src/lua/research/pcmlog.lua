dofile("/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/lua/bgm.lua")
local snd = manager.machine.devices[":audiocpu"].spaces["program"]
local f = 0; local reg = {}; local bank = 0
local out = io.open(os.getenv("PCMOUT"), "w")
_G.pt = snd:install_write_tap(0xf000, 0xf02d, "pcm", function(off, data, mask)
  if off == 0xf000 then bank = data return end
  if off < 0xf020 then return end
  local r = off - 0xf020; reg[r] = data
end)
_G.pr = snd:install_read_tap(0xf025, 0xf02b, "pcmr", function(off, data, mask)
  local r = off - 0xf020
  if r == 5 or r == 11 then  -- 読むと発音(ch0 / ch1)
    local b = (r == 5) and 0 or 6
    local st = (reg[b+2] or 0) | ((reg[b+3] or 0) << 8) | (((reg[b+4] or 0) & 1) << 16)
    out:write(string.format("%d ch%d start %05x bank %02x\n", f, r == 5 and 0 or 1, st, bank)); out:flush()
  end
end)
emu.register_frame_done(function() f = f + 1 end)
