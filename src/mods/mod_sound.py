"""サウンドCPU(Z80, 945_r05.d9)へのパッチ
未使用曲 A1（メニューで鳴らす）だけ音量を本来の半分にする。
- FM: 0x0992 の ld a,(ix+$43)（フェード用の減衰量）を call に置き換え、曲が A1 のときは減衰を +8（0.75dB×8 = 6dB = 振幅半分）
- PCM(007232): 0x0B3B の and $78 / ld c,a を call に置き換え、曲が A1 のときは音量(4bit)を半分に
  (ix+$01) は曲の開始時にその曲番号が入る（0x0129）
空き: 0xec91〜0xfc26（0xff）
"""
SONG = 0xa1
FM_ATT = 0xeca0
PCM_ATT = 0xecb0

def apply(rom):
    fm = bytes([0xdd, 0x7e, 0x01, 0xfe, SONG, 0xdd, 0x7e, 0x43, 0xc0,   # ld a,(ix+1) / cp A1 / ld a,(ix+$43) / ret nz
                0xfe, 0x78, 0xd0, 0xc6, 0x08, 0xc9])                    # cp $78 / ret nc / add a,8 / ret
    pcm = bytes([0xe6, 0x78, 0x4f, 0xdd, 0x7e, 0x01, 0xfe, SONG, 0x79, 0xc0,  # and $78 / ld c,a / ld a,(ix+1) / cp A1 / ld a,c / ret nz
                 0xcb, 0x3f, 0xe6, 0x78, 0x4f, 0xc9])                         # srl a / and $78 / ld c,a / ret
    rom.put('snd', FM_ATT, fm, 'snd-fm-att')
    rom.put('snd', PCM_ATT, pcm, 'snd-pcm-att')
    rom.put('snd', 0x0992, bytes([0xcd, FM_ATT & 0xff, FM_ATT >> 8]), 'snd-fm-hook', expect=bytes.fromhex('dd7e43'))
    rom.put('snd', 0x0b3b, bytes([0xcd, PCM_ATT & 0xff, PCM_ATT >> 8]), 'snd-pcm-hook', expect=bytes.fromhex('e6784f'))

def fix_sum(rom):
    """起動時のROMチェック: 0x0000〜0xefff のバイト合計(16bit)が 0x73b5。改造で変わった分を 0xef00〜 の空き(0xff)を減らして戻す"""
    s = rom.snd; want = sum(rom.snd0[:0xf000]) & 0xffff
    assert want == 0x73b5
    d = (sum(s[:0xf000]) - want) & 0xffff
    buf = bytearray(b'\xff' * 0x100)
    i = 0
    while d:
        k = min(0xff, d); buf[i] -= k; d -= k; i += 1
    rom.put('snd', 0xef00, bytes(buf[:max(i, 1)]), 'snd-sum')
    assert sum(s[:0xf000]) & 0xffff == want
