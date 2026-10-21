"""サブCPU側: ロック/解除コンボ + 60秒自動ロック + メニュー起動
サブROM空き: 0x37d78〜0x3ffff（サブ連結イメージ上）。メールボックス: 共有RAM 0x103f00 → サブから 0x203f00
サブ専用変数: 0x100f00〜（サブ私有RAM。要MAME確認: 未使用であること）
"""
SUB_FREE = 0x37d78
MBS = 0x203f00

CONSTS = """
MBS_P1   = $203f00
MBS_SYS  = $203f01
MBS_UNLK = $203f02
MBS_REQ  = $203f03
MBS_DONE = $203f04
MBS_KIND = $203f05
MBS_PAUS = $203f06
MBS_RUN  = $203f07
TOPSTATE = $2037c5
SV       = $100f00
V_LAST   = $100f00
V_PUD    = $100f02
V_PDU    = $100f03
V_TUD    = $100f04
V_TDU    = $100f06
V_IDLE   = $100f08
FRAMECNT = $203950          ; メインのVBLANKが共有RAMへ写すフレームカウンタ(サブの$100022は途中で止まるため)
"""

SRC = CONSTS + """
        org $37d78
; サブ IRQ1(垂直同期, 毎フレーム) の前に割り込ませる。元のハンドラ 0x5c8 へ続ける
IrqHook:
        movem.l d0-d7/a0-a6,-(a7)
        lea     AREABLOB.l,a0           ; 独自エリア表を共有RAMへ (ボスラッシュ時は専用表)
        cmpi.b  #2,$203f0b.l
        bne.s   sb_a0
        lea     BOSSBLOB.l,a0
sb_a0:
        lea     $203f40.l,a1
        move.w  #AREACNT,d7
sb_cp:  move.l  (a0)+,(a1)+
        dbf     d7,sb_cp
        lea     EDGEN.l,a0              ; エディット画面の表 → $103b40 (改造プレイ時は拡張版)
        tst.b   MBS_RUN.l
        beq.s   sb_d0
        lea     EDEXT.l,a0
sb_d0:  move.b  (a0),d0                 ; 先頭(MISSILE列の数)が違うときだけ書き直す(毎フレームの負担を減らす)
        cmp.b   $203b40.l,d0
        beq.s   sb_d2
        lea     $203b40.l,a1
        moveq   #EDCNT,d7
sb_d1:  move.l  (a0)+,(a1)+
        dbf     d7,sb_d1
sb_d2:
        lea     EXTN.l,a0               ; 10面の独自エリア表 → $103e40 (ボスラッシュ時はボス1直前から)
        cmpi.b  #2,$203f0b.l
        bne.s   sb_e0
        lea     EXTB.l,a0
sb_e0:  lea     $203e40.l,a1
        moveq   #33,d7
sb_e1:  move.l  (a0)+,(a1)+
        dbf     d7,sb_e1
        moveq   #0,d0                   ; シールド色(選択中の7色)を共有RAM $103e00 へ
        move.b  $203f16.l,d0
        subq.b  #1,d0
        cmpi.b  #9,d0
        bls.s   sb_c1
        moveq   #0,d0
sb_c1:  mulu    #14,d0
        lea     SHCOL.l,a0
        adda.w  d0,a0
        lea     $203e00.l,a1
        moveq   #6,d7
sb_c2:  move.w  (a0)+,(a1)+
        dbf     d7,sb_c2
        lea     BOSSTBL.l,a0            ; ボスラッシュ用: 面ごとのボス接近位置 → $103e10
        lea     $203e10.l,a1
        moveq   #7,d7
sb_c3:  move.l  (a0)+,(a1)+
        dbf     d7,sb_c3
        jsr     Frame.l
        movem.l (a7)+,d0-d7/a0-a6
        jmp     $5c8.l          ; 元の処理へ

; ---- 毎フレーム ----  (解除/ロック/自動ロックはメインCPU側で処理)
Frame:
        move.w  $203e32.l,d0    ; キューブの RANDOM 用の乱数: 電源投入から毎フレーム進める（デモ・メニュー中も）
        mulu    #25173,d0
        addi.w  #13849,d0
        move.w  d0,$203e32.l
        moveq   #0,d1               ; CUBE INFO が有効か → $203ed1（メインはこれを見て HI・2P を描かない）
        cmpi.b  #2,TOPSTATE.l
        bne.s   fe_set
        tst.b   MBS_RUN.l
        beq.s   fe_set
        tst.l   $2038de.l
        beq.s   fe_set
        cmpi.b  #1,$203f0b.l
        bne.s   fe_set
        tst.b   $203f0c.l
        beq.s   fe_off
        moveq   #1,d1
        bra.s   fe_set
fe_off: tst.b   $203ed1.l           ; 表示中に OFF にされた → 最上段を消して、メインにスコアの描き直しを頼む
        beq.s   fe_set
        move.w  #26,d0
        move.w  #2,d1
        moveq   #24,d7
        jsr     ClrFld.l
        move.b  #1,$203ed0.l
        moveq   #0,d1
fe_set: move.b  d1,$203ed1.l
        tst.b   MBS_RUN.l           ; キューブラッシュでは残機が増えない（次に増える点数を 0 = もう増えない にしておく）
        beq.s   fe_x
        cmpi.b  #1,$203f0b.l
        bne.s   fe_x
        clr.l   $201058.l
fe_x:
        cmpi.b  #2,TOPSTATE.l
        beq.w   fr_ingame
        tst.b   MBS_REQ.l
        bne.w   fr_menu
        clr.b   V_INIT.l
fr_chk: rts
fr_menu:
        tst.b   MBS_DONE.l
        bne.w   fr_chk
        jmp     MenuFrame.l
fr_ingame:
        tst.b   MBS_RUN.l
        beq.w   fr_nr
        jsr     CmdCalc.l
        jsr     CubeCalc.l
        jsr     EditOv.l
        tst.l   $2038de.l       ; 面が始まってから（武器選択などの画面では出さない）
        beq.w   fr_nr
        jsr     CubeHud.l
        tst.b   $203f0e.l       ; RANK DISP（ポーズで切り替え。OFF にしたら消す）
        bne.s   fr_rk
        tst.b   V_RKL.l
        beq.w   fr_nr
        clr.b   V_RKL.l
        move.w  #43,d0
        move.w  #3,d1
        moveq   #7,d7
        jsr     ClrFld.l
        bra.w   fr_nr
fr_rk:  move.b  #1,V_RKL.l
        jsr     RankDisp.l
fr_nr:  cmpi.b  #1,MBS_PAUS.l
        bne.w   fr_np
        jmp     PauseFrame.l
fr_np:  clr.b   $100f50.l
        rts


; ---- キューブラッシュの並び: 毎フレーム、選ばれた H/S/T（R は毎フレーム乱数で選び直す）から
;      1個目が出る瞬間に入れるフレームカウンタの値を表から引いて $203e30 に置く（メインの CubeSeed が使う）
V_CRNG  = $203e32
CubeCalc:
        move.w  V_CRNG.l,d0
        moveq   #0,d1
        move.b  $203f35.l,d1    ; H: 0=R, 1..16
        bne.s   cu_h
        move.w  d0,d1
        lsr.w   #8,d1
        andi.w  #15,d1
        addq.w  #1,d1
cu_h:   subq.w  #1,d1
        lsl.w   #2,d1           ; (h*4 + s)
        moveq   #0,d2
        move.b  $203f36.l,d2    ; S: 0=R, 1..4
        bne.s   cu_s
        move.w  d0,d2
        lsr.w   #4,d2
        andi.w  #3,d2
        addq.w  #1,d2
cu_s:   subq.w  #1,d2
        add.w   d2,d1
        mulu    #45,d1
        moveq   #0,d2
        move.b  $203f37.l,d2    ; T: 0=R, 1..45
        bne.s   cu_t
        moveq   #0,d2
        move.w  d0,d2
        divu    #45,d2
        swap    d2
        andi.l  #$ffff,d2
        addq.w  #1,d2
cu_t:   subq.w  #1,d2
        add.w   d2,d1
        add.w   d1,d1
        lea     CUBETBL.l,a0
        move.w  0(a0,d1.w),$203e30.l
        rts
"""

DATA_BASE = 0x39000
WTYPE_BYTES = bytes([1,3,1, 3,1,4, 4,2,2, 2,4,3])   # TYPE A..D -> (missile, double, laser)

def apply(rom):
    import asm68, mod_menu, os
    import mod_main
    data, dl = mod_menu.build_data(DATA_BASE)
    ab = mod_main.area_table_blob()
    if len(data) & 1: data += b'\0'
    dl['AREABLOB'] = DATA_BASE + len(data); dl['AREACNT'] = len(ab) // 4 - 1
    data += ab
    bb = mod_main.boss_area_blob(); assert len(bb) == len(ab)
    dl['BOSSBLOB'] = DATA_BASE + len(data); data += bb
    import mod_edit
    main = open(os.path.join(os.path.dirname(__file__), '..', 'work', 'main313.bin'), 'rb').read()
    cells = open(os.path.join(os.path.dirname(__file__), 'edit_cells.bin'), 'rb').read()
    if len(data) & 1: data += b'\0'
    eb, el = mod_edit.sub_blob(DATA_BASE + len(data), cells[:6], cells[8:], cells[6:8], mod_edit.tables(main, False), mod_edit.tables(main, True))
    data += eb; dl.update(el); dl['EDCNT'] = mod_edit.SIZE // 4 - 1
    if len(data) & 1: data += b'\0'
    dl['EXTN'] = DATA_BASE + len(data); data += mod_main.ext10_blob(False)
    dl['EXTB'] = DATA_BASE + len(data); data += mod_main.ext10_blob(True)
    import struct
    pt, bt = mod_main.progress_tables()
    import mod_cube
    if len(data) & 1: data += b'\0'
    dl['CUBETBL'] = DATA_BASE + len(data); data += b''.join(struct.pack('>H', x) for x in mod_cube.table())
    dl['CUBEDLT'] = DATA_BASE + len(data); data += b''.join(struct.pack('>H', x) for x in mod_cube.DELTAS)
    import mod_menubg
    for k, (n, blob) in mod_menubg.blobs().items():
        if len(data) & 1: data += b'\0'
        dl[k] = DATA_BASE + len(data); data += blob
    dl['PROGTBL'] = DATA_BASE + len(data); data += b''.join(struct.pack('>H', x) for x in pt)
    dl['BOSSTBL'] = DATA_BASE + len(data); data += b''.join(struct.pack('>H', x) for x in bt)
    dl['SHCOL'] = DATA_BASE + len(data)
    data += open(os.path.join(os.path.dirname(__file__), 'shield_colors.bin'), 'rb').read()
    wt = DATA_BASE + len(data) + (len(data) & 1)
    data = data + (b'\0' if len(data) & 1 else b'') + WTYPE_BYTES
    consts = ''.join('%s = $%x\n' % (k, v) for k, v in dl.items()) + 'WTYPE = $%x\n' % wt
    src = CONSTS + consts + SRC.replace(CONSTS, '', 1) + mod_menu.source(dl) + mod_edit.src()
    src = src.replace('V_INIT', 'V_INIT') 
    b, lab = asm68.assemble('V_INIT = $100f12\n' + src if 'V_INIT   =' not in src else src, SUB_FREE)
    assert SUB_FREE + len(b) <= DATA_BASE, hex(SUB_FREE + len(b))
    rom.put('sub', SUB_FREE, b, 'subcore')
    rom.put('sub', 0xafc4, bytes.fromhex('4eb9') + lab['CubeStick'].to_bytes(4, 'big'), 'cube-stick', expect=bytes.fromhex('117c00010026'))
    rom.put('sub', 0x877c, bytes.fromhex('4eb9') + lab['SprHook'].to_bytes(4, 'big') + bytes.fromhex('4e714e714e71'), 'menubg-spr', expect=bytes.fromhex('610000d213fc000000203936'))
    rom.put('sub', DATA_BASE, data, 'menudata')
    # IRQ1 ハンドラ(0xc6e)内の jsr $5c8 (0xc88) → jsr IrqHook
    rom.put('sub', 0xc88, bytes.fromhex('4eb9') + lab['IrqHook'].to_bytes(4, 'big'), 'irq1hook', expect=bytes.fromhex('4eb9000005c8'))
    return lab, len(b)
