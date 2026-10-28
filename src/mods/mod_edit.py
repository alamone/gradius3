"""エディット画面の拡張（改造プレイ時のみ）
エディットでも、タイプA〜D専用の武器を選べるようにする:
  MISSILE: NORMAL / CONTROL / UPPER / S.SPREAD + PHOTON TORPEDO / SPREAD BOMB / 2WAY MISSILE
  DOUBLE : VERTICAL / SPREAD GUN / TAIL GUN / FREE WAY + DOUBLE
  LASER  : TWIN / RIPPLE / E.LASER / C.LASER + NORMAL LASER

仕組み
  メイン: エディット画面が使う3つの表（各列の選択肢の数 0x73b6・武器コード 0x7450・選択枠の位置 0x7566）を
          共有RAM $103b40〜 の表を見るように書き換える（命令の追加なし。表の間隔 4→8 のみ変更）。
          共有RAMの表はサブCPUが毎フレーム書く: 通常プレイ=純正と同じ内容、改造プレイ=拡張した内容。
  サブ  : 拡張分（5番目以降の選択肢）を選んでいる列は、その列の4マスの絵を消して名前の文字を出す（2ページ目）。
          ページの判定は選択枠の位置(X座標の端数)に印を付けて行う（見た目には影響しない）。
"""
import struct

EB = 0x103b40            # 共有RAM(メイン空間)  サブからは +0x100000
O_MAX, O_VAL, O_PTR, O_BOX = 0, 8, 56, 80
SIZE = O_BOX + 3 * 8 * 12  # 368

GEN_VAL = [[0x02, 0x16, 0x1c, 0x1d], [0x07, 0x17, 0x06, 0x13], [0x0b, 0x0c, 0x18, 0x0a],
           [0x0d, 0x0e, 0x0d, 0x0d], [0x12, 0x10, 0x11, 0x1a], [0x1b, 0x19, 0x1e, 0x1a]]
EXT_ADD = [[0x03, 0x04, 0x05], [0x08], [0x09]]           # PHOTON/SPREAD/2WAY, DOUBLE, NORMAL LASER
GEN_MAX = [3, 3, 3, 1, 3, 2]
BOXPTR = [0x757e, 0x75ae, 0x75de, 0x760e, 0x763e, 0x766e]
PAGE_MARK = 0x10         # 選択枠X座標の最下位バイト = 0x10+番号(4〜6) → 2ページ目
LABELS = [[], [], []]     # 2ページ目は絵（名前入り）なので文字は書かない
# 2ページ目の絵: タイプ選択画面の武器の絵(4x4タイル, 名前の行を含む) [列][マス]
#   edit_icons.bin = PHOTON(タイプD) SPREAD BOMB(B) 2WAY(C) DOUBLE(A) NORMAL LASER(A) の順
ICON_POS = [[0, 1, 2], [3], [4]]

def tables(main, ext):
    """共有RAM EB に置く表 (bytes, SIZE)"""
    b = bytearray(SIZE)
    mx = list(GEN_MAX)
    if ext:
        for k in range(3): mx[k] = 3 + len(EXT_ADD[k])
    b[O_MAX:O_MAX + 6] = bytes(mx)
    for k in range(6):
        v = GEN_VAL[k] + (EXT_ADD[k] if ext and k < 3 else [])
        b[O_VAL + 8 * k:O_VAL + 8 * k + len(v)] = bytes(v)
    ptr = list(BOXPTR)
    if ext:
        for k in range(3): ptr[k] = EB + O_BOX + 96 * k
    b[O_PTR:O_PTR + 24] = b''.join(struct.pack('>I', p) for p in ptr)
    for k in range(3):
        ent = [main[BOXPTR[k] + 12 * i:BOXPTR[k] + 12 * i + 12] for i in range(4)]
        assert struct.unpack('>I', ent[0][4:8])[0] & 0xff == 0
        for i in range(8):
            e = bytearray(ent[i % 4])
            if i >= 4: e[7] = PAGE_MARK + i
            o = O_BOX + 96 * k + 12 * i
            b[o:o + 12] = e
    return bytes(b)

def apply_main(rom, main):
    """メインROM: 表の参照先を共有RAMへ（命令は増やさない）"""
    rom.put('main', 0x72cc, bytes.fromhex('49f9') + struct.pack('>I', EB + O_MAX), 'ed_max', expect=bytes.fromhex('49f9000073b6'))
    rom.put('main', 0x7402, bytes.fromhex('4df9') + struct.pack('>I', EB + O_VAL), 'ed_val', expect=bytes.fromhex('4df900007450'))
    for a in (0x7416, 0x7420, 0x742a, 0x7432, 0x743c):          # addq.w #4,a6 → addq.w #8,a6 (表の間隔)
        rom.put('main', a, bytes.fromhex('504e'), 'ed_stride', expect=bytes.fromhex('584e'))
    rom.put('main', 0x74e2, bytes.fromhex('43f9') + struct.pack('>I', EB + O_PTR), 'ed_box', expect=bytes.fromhex('43f900007566'))

# ---- サブ: 2ページ目の表示 ----
# エディット画面のマスは レイヤー(K052109 の $2000 面): 列 3+6k の4タイル幅, 行 9〜27 (5行ごとに1マス)
# 文字は FIX レイヤー(メニューと同じ面)。FIX の列 = レイヤーの列 + 12
LAYER_ATTR = 0x24e001    # サブ空間: 面$2000 の属性(+1)。コードは +0x4000
SIG = (3, 11, 6)         # 画面判定: 行3 列11〜16 のタイルコード（"EDIT MODE" の文字）

def sub_data(gfxdump):
    """ビルド時に、純正のエディット画面のタイル(ダンプ)から 元の絵(3列分)と判定用の印を取り出す"""
    def code(r, c): return gfxdump[0x4000 + 0x2000 + r * 0x80 + c * 2 + 1]
    def attr(r, c): return gfxdump[0x2000 + r * 0x80 + c * 2 + 1]
    sig = bytes(code(SIG[0], SIG[1] + i) for i in range(SIG[2]))
    orig = bytearray()
    for k in range(3):
        c0 = 3 + 6 * k
        for r in range(9, 28):
            for t in range(4): orig += bytes([attr(r, c0 + t), code(r, c0 + t)])
    blank = bytes([attr(19, 21), code(19, 21)])
    return sig, bytes(orig), blank

SRC = """
LAYER_ATTR = $24e001
V_EDON  = $1034c0
V_EDTX  = $1034c1
V_PG    = $1034c4           ; 3列分のページ(0/1)

; ---- 改造プレイ中、毎フレーム: エディット画面なら拡張分の表示 ----
EditOv:
        lea     $252000+%(sigofs)d.l,a0
        lea     EDSIG.l,a1
        moveq   #%(siglen)d-1,d7
eo_sg:  move.b  (a0),d0
        cmp.b   (a1)+,d0
        bne.w   eo_off
        addq.w  #2,a0
        dbf     d7,eo_sg
        tst.b   V_EDON.l
        bne.s   eo_1
        move.b  #1,V_EDON.l
        clr.l   V_PG.l
eo_1:   moveq   #0,d6
eo_col: move.w  d6,d0
        mulu    #$50,d0
        lea     $20237b.l,a0        ; 選択枠(物体 $102370+$50*列)の X 座標の最下位バイト
        move.b  0(a0,d0.w),d1
        moveq   #0,d2
        cmpi.b  #$14,d1
        bcs.s   eo_p
        cmpi.b  #$18,d1
        bcc.s   eo_p
        moveq   #1,d2
eo_p:   lea     V_PG.l,a0
        cmp.b   0(a0,d6.w),d2
        beq.s   eo_nx
        move.b  d2,0(a0,d6.w)
        move.w  d6,-(a7)
        jsr     EdDraw.l
        move.w  (a7)+,d6
eo_nx:  addq.w  #1,d6
        cmpi.w  #3,d6
        bcs.s   eo_col
        rts
eo_off: tst.b   V_EDON.l
        beq.s   eo_r
        clr.b   V_EDON.l
        tst.b   V_EDTX.l
        beq.s   eo_r
        clr.b   V_EDTX.l
        moveq   #9,d5
eo_cl:  move.w  #13,d0
        move.w  d5,d1
        moveq   #19,d7
        jsr     ClrFld.l           ; 3列分(FIX 列14〜33)
        addq.w  #1,d5
        cmpi.w  #28,d5
        bcs.s   eo_cl
eo_r:   rts

; d6 = 列(0〜2), d2 = ページ(0=元の絵 1=名前)
EdDraw:
        move.w  d6,d0
        mulu    #12,d0              ; レイヤー列 (3+6k)*2 バイト
        addi.w  #6,d0
        lea     LAYER_ATTR.l,a2
        adda.w  d0,a2
        lea     $480(a2),a2         ; 行9
        move.w  d6,d0
        mulu    #152,d0
        lea     EDORIG.l,a1         ; 1ページ目 = 元の絵 / 2ページ目 = タイプ選択画面の武器の絵を並べたもの
        tst.b   d2
        beq.s   ed_p1
        lea     EDPAGE2.l,a1
ed_p1:  adda.w  d0,a1
        moveq   #18,d5              ; 19行
ed_r:   moveq   #3,d4
        movea.l a2,a3
ed_t:   move.b  (a1)+,(a3)
        move.b  (a1)+,$4000(a3)
        addq.w  #2,a3
        dbf     d4,ed_t
        lea     $80(a2),a2
        dbf     d5,ed_r
        ; FIX レイヤーの文字: いったん消してから(2ページ目なら)名前を書く
        move.w  d6,d0               ; 文字の左端: MISSILE列はマスの1つ左から7文字分、他の列はマスの左端から6文字分
        mulu    #6,d0
        addi.w  #3+12,d0
        moveq   #5,d4
        tst.w   d6
        bne.s   ed_c0
        subq.w  #1,d0
        moveq   #6,d4
ed_c0:  move.w  d0,d3
        moveq   #9,d5
ed_c:   move.w  d3,d0
        move.w  d5,d1
        move.w  d4,d7
        movem.l d2-d6,-(a7)
        jsr     ClrFld.l
        movem.l (a7)+,d2-d6
        addq.w  #1,d5
        cmpi.w  #28,d5
        bcs.s   ed_c
        tst.b   d2
        beq.s   ed_x
        move.b  #1,V_EDTX.l
        move.w  d6,d0
        lsl.w   #2,d0
        lea     EDLBL.l,a4
        movea.l 0(a4,d0.w),a4       ; この列の名前: [行, 文字列...0] の並び, 行=0 で終わり
ed_l:   moveq   #0,d1
        move.b  (a4)+,d1
        beq.s   ed_x
        movea.l a4,a0
ed_z:   tst.b   (a4)+
        bne.s   ed_z
        move.w  d3,d0
        moveq   #0,d2
        movem.l d3/a4,-(a7)
        jsr     PutStr.l
        movem.l (a7)+,d3/a4
        bra.s   ed_l
ed_x:   rts
"""

def sub_blob(base, sig, orig, blank, gen, ext):
    """サブROMのデータ: 表(純正/拡張)・判定用の印・元の絵・空白タイル・名前"""
    b = bytearray(); lab = {}
    def put(n, x):
        if len(b) & 1: b.append(0)
        lab[n] = base + len(b); b.extend(x)
    put('EDGEN', gen); put('EDEXT', ext); put('EDSIG', sig); put('EDORIG', orig); put('EDBLANK', blank)
    import os
    icons = open(os.path.join(os.path.dirname(__file__), 'edit_icons.bin'), 'rb').read()
    p2 = bytearray()
    for k in range(3):
        for r in range(19):
            j, rr = divmod(r, 5)
            for t in range(4):
                if rr < 4 and j < len(ICON_POS[k]):
                    o = ICON_POS[k][j] * 32 + rr * 8 + t * 2
                    p2 += icons[o:o + 2]
                else:
                    p2 += blank
    put('EDPAGE2', bytes(p2))
    lp = []
    for k in range(3):
        s = bytearray()
        for j, (l1, l2) in enumerate(LABELS[k]):
            r = 9 + 5 * j + 1
            s += bytes([r]) + l1.encode() + b'\0'
            if l2: s += bytes([r + 1]) + l2.encode() + b'\0'
        s += b'\0'
        put('EDL%d' % k, bytes(s)); lp.append(lab['EDL%d' % k])
    put('EDLBL', b''.join(struct.pack('>I', p) for p in lp))
    return bytes(b), lab

def src():
    return SRC % {'sigofs': SIG[0] * 0x80 + SIG[1] * 2 + 1 - 0x2000 + 0x2000, 'siglen': SIG[2]}

# ---- メイン: 左右で2ページ目 ----
# 0x7288 の「move.b d6,d7 / andi.b #$c,d7」(新しく押したレバーの上下) を jsr EdLR に置き換え、直後の bne.s $72aa はそのまま使う。
# 左右を押したとき、その列に2ページ目があれば(表の選択肢の数>=5: 改造プレイ時のみ) 1ページ目⇔2ページ目の先頭へ移動。
EDLR_ADDR = 0xd660        # （使っていない。#34 から EdLR は mod_main の「かたまり」として置く。apply_lr も使っていない）
SRC_LR = """
        org $%x
EdLR:   move.b  d6,d7
        andi.b  #$03,d7         ; 左右を新しく押した?
        beq.s   el_ud
        moveq   #0,d1
        move.b  9(a0),d1        ; 今の列
        lea     $%x.l,a4        ; 列ごとの選択肢の数-1 (共有RAMの表)
        cmpi.b  #4,0(a4,d1.w)
        bcs.s   el_ud           ; 2ページ目なし(通常プレイは常にここ)
        lea     $a(a0,d1.w),a3
        moveq   #4,d0
        cmp.b   (a3),d0
        bhi.s   el_s            ; 1ページ目 → 2ページ目の先頭
        moveq   #0,d0           ; 2ページ目 → 1ページ目の先頭
el_s:   move.b  d0,(a3)
        jsr     $2c86.l         ; カーソル移動の音(上下と同じ)
el_ud:  move.b  d6,d7           ; 元の処理: 上下を新しく押した? (Z フラグを返す)
        andi.b  #$0c,d7
        rts
"""

def apply_lr(rom):
    import asm68
    b, lab = asm68.assemble(SRC_LR % (EDLR_ADDR, EB + O_MAX), EDLR_ADDR)
    rom.put('main', EDLR_ADDR, b, 'ed_lr', free_ok=True, expect=None) if False else None
    rom.img('main')[EDLR_ADDR:EDLR_ADDR + len(b)] = b
    rom.used.append(('main', EDLR_ADDR, EDLR_ADDR + len(b), 'ed_lr'))
    rom.put('main', 0x7288, bytes.fromhex('4eb9') + EDLR_ADDR.to_bytes(4, 'big'), 'ed_lrhook', expect=bytes.fromhex('1e060207000c'))
    return len(b)
