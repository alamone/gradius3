-- Issue #20 の調査（alamone さん）: START 表示から400フレームの間、パレットRAMへの書き込みを PC ごとに数える。詳しくは dev/research/start-palette.md
-- palcount.lua
-- mame gradius3j -autoboot_script palcount.lua -autoboot_delay 1 \
--   -video none -sound none -nothrottle -seconds_to_run 900
local frame, armed, mark, total = 0, false, 0, 0
local by_pc, mem, cpu = {}, nil, nil
local function tick()
  frame = frame + 1
  if frame == 240 then
    cpu = manager.machine.devices[":maincpu"]
    mem = cpu.spaces["program"]
    -- 書き込みタップは終わりの番地を奇数にすること
    G3_TAP = mem:install_write_tap(0x80000, 0x80FFF, "pal", function()
      if not armed then return end
      total = total + 1
      local pc = cpu.state["PC"].value
      by_pc[pc] = (by_pc[pc] or 0) + 1
    end)
  end
  if not mem then return end
  -- $40029 == 02 は START 表示。そこから 400 フレーム数える
  if not armed and mem:read_u8(0x40029) == 0x02 then
    armed, mark = true, frame + 400
  end
  if armed and frame >= mark then
    local rows = {}
    for pc, n in pairs(by_pc) do rows[#rows + 1] = { pc, n } end
    table.sort(rows, function(a, b) return a[2] > b[2] end)
    print(string.format("palette writes %d  (PC %d種)", total, #rows))
    for i = 1, math.min(#rows, 8) do
      print(string.format("   PC $%06X  x%d", rows[i][1], rows[i][2]))
    end
    manager.machine:exit()
  end
end
G3_SUB = emu.add_machine_frame_notifier(tick)
