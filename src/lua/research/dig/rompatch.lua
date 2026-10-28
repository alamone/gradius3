-- 地形を掘る跡（#6）の調査用。起動時のROMチェックが済んだあと（12秒）に ROM を書き換えてから g3run.lua を動かす
-- env SUBPATCH="addr:hexbytes,..."（サブ） MAINPATCH=同（メイン）  G3RUN=g3run.lua のパス
local m = manager.machine
local function apply(tag, spec)
  local rg = m.memory.regions[tag]
  for a, hx in (spec or ""):gmatch("(%x+):(%x+)") do
    a = tonumber(a, 16)
    for i = 0, #hx // 4 - 1 do rg:write_u16(a + i*2, tonumber(hx:sub(i*4+1, i*4+4), 16)) end
    print(tag, string.format("%x", a), hx)
  end
end
local done = false
SUBFIX_N = emu.add_machine_frame_notifier(function()
  if not done and m.time.seconds > 12 then
    done = true; apply(":sub", os.getenv("SUBPATCH")); apply(":maincpu", os.getenv("MAINPATCH"))
  end
end)
dofile(os.getenv("G3RUN"))
