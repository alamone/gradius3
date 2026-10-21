"""サブCPU側: 隠しメニュー（描画・操作）— テーブル駆動
値は共有RAMメールボックス設定領域 MB+8〜 に保持（メインが開始時に参照）。
前回値は サブ私有RAM(V_LASTBUF)に保存。
※ タイル座標/属性は MAME実測後に TILE_* / ATTR_* を調整する。
"""
import struct

# (ラベル, 種別, 最小, 最大, MBオフセット, 値文字列 or None, 既定値)   種別 0=数値 1=列挙 2=アクション
# 種別 3 = 面/エリアの表の1行（最小値=面番号 1..12、最大値=その面のエリア数）
AREAS = [4, 5, 9, 1, 5, 4, 3, 4, 3, 10, 2, 0, 5]   # 選べるエリア数。1面V・7面IV・8面V はボス戦中の復活地点で、そこから開始すると即面クリアになるため除外
STAGE_LABELS = ['STAGE 1', 'STAGE 2', 'STAGE 3', 'STAGE 4', 'STAGE 5', 'STAGE 6', 'STAGE 7', 'STAGE 8', 'STAGE 9', 'STAGE 10', 'EX STAGE', '', 'BOSS RUSH']
# 行の並び: 面1〜10, BOSS RUSH(内部の面番号13), EX STAGE(11。A=グラディウス B=サラマンダ → 開始時に 11/12)
ROW_ORDER = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 10]
ITEMS = [
    ('MODE',      1, 0, 2, 0x0b, ['NORMAL', 'CUBE RUSH', 'BOSS RUSH'], 0),
] + [(STAGE_LABELS[i], 3, i + 1, AREAS[i], 0x08, None, 0) for i in ROW_ORDER] + [
    ('LOOP',      0, 1, 99, 0x09, None, 1),
    ('LIVES',     0, 1, 99, 0x0d, None, 3),
    ('SHD COLOR', 1, 1, 10, 0x16, ['?', 'BLUE', 'RED', 'GREEN', 'GOLD', 'PURPLE', 'CYAN', 'ORANGE', 'PINK', 'SILVER', 'BLACK'], 1),
    ('CUBE PATTERN', 0, 0, 99, 0x1d, None, 0),
    ('HUNTER NEXT', 1, 0, 3, 0x1b, ['DEFAULT', 'TYPE 1', 'TYPE 2', 'TYPE 3'], 0),
    ('HUNTER TIME', 0, 0, 99, 0x1c, None, 0),
    ('RANK DISP', 1, 0, 1, 0x0e, ['OFF', 'ON'], 0),
    ('INVINCIBLE', 1, 0, 1, 0x20, ['OFF', 'ON'], 0),   # 一時的な項目（無敵）
    ('START',     2, 0, 0, 0, None, 0),
    ('BACK TO DEMO', 2, 0, 0, 0, None, 0),
]
ROMAN = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']   # エリア名(英字)
GRID_COL = 26
ROMAN_OFS = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
ATTR_SELGRID = 0x80      # 選択中のマスの色（パレット4: アトラクト後はオレンジ）
ATTR_DIS = 0xa0          # MODE で使われないマスの色（パレット5: 暗い青紫）
NITEM = len(ITEMS)
# 可視領域は タイル列12〜51 / 行2〜29 (320x224)。それに合わせて配置
ROW0, COL_LABEL, COL_VAL, COL_CUR = 4, 14, 29, 12
TILE_A = 0x24c000
ATTR_TXT = 0x00          # 属性（パレット番号<<5）。実測で調整
ATTR_SEL = 0x20          # 選択行

def build_data(base):
    """文字列・項目表を base から並べて (bytes, labels) を返す"""
    blob = bytearray(); lab = {}
    def al():
        if len(blob) % 2: blob.append(0)
    def put(name, data):
        al(); lab[name] = base + len(blob); blob.extend(data)
    # 文字列
    for i, it in enumerate(ITEMS):
        put(f'L{i}', it[0].encode() + b'\0')
    for i, it in enumerate(ITEMS):
        if it[5]:
            ptrs = []
            for j, s in enumerate(it[5]):
                put(f'V{i}_{j}', s.encode() + b'\0'); ptrs.append(lab[f'V{i}_{j}'])
            al(); lab[f'VT{i}'] = base + len(blob)
            for p in ptrs: blob.extend(struct.pack('>I', p))
    put('TITLE', b'GRADIUS III  SPECIAL MENU\0')
    put('HELP1', b'UP DOWN SELECT  LEFT RIGHT CHANGE\0')
    put('HELP2', b'START GO   SHOT2 BACK TO DEMO\0')
    put('PS_T', b'PAUSE\0')
    put('RK_T', b'RANK\0')
    put('PS_C0', b'>CONTINUE\0')
    put('PS_C1', b' CONTINUE\0')
    put('PS_G0', b'>GAME OVER\0')
    put('PS_G1', b' GAME OVER\0')
    put('PS_I0', b'>INVINCIBLE\0')
    put('PS_I1', b' INVINCIBLE\0')
    put('PS_ON', b'ON \0')
    put('PS_OFF', b'OFF\0')
    # 項目記述子 12B: labelptr.l type.b min.b max.b mboff.b pad.b strtab.l
    al(); lab['ITM'] = base + len(blob)
    for i, it in enumerate(ITEMS):
        blob.extend(struct.pack('>IBBBBI', lab[f'L{i}'], it[1], it[2], it[3], it[4], lab.get(f'VT{i}', 0)))
    # 既定値表（MB+8からの順序に依存せず、(mboff,既定値)ペア）
    al(); lab['DEF'] = base + len(blob)
    for it in ITEMS:
        if it[1] not in (2, 3): blob.extend(bytes([it[4], it[6]]))
    blob.extend(bytes([0x08, 1, 0x0a, 1]))     # 面1・エリアI
    blob.extend(b'\xff\xff')
    # ローマ数字(エリア)
    for i, r in enumerate(ROMAN): put(f'RM{i}', r.encode() + b'\0')
    al(); lab['ROMAN'] = base + len(blob)
    for i in range(len(ROMAN)): blob.extend(struct.pack('>I', lab[f'RM{i}']))
    lab['ROMOFS'] = base + len(blob); blob.extend(bytes(ROMAN_OFS))
    return bytes(blob), lab

ENGINE = """
SV2     = $100f00
V_CUR   = $100f10
V_DIRTY = $100f11
V_INIT  = $100f12
V_REPC  = $100f13
V_PIN   = $100f14
V_SIN   = $100f15
V_HAVE  = $100f16
V_LBUF  = $100f20          ; 前回値 0x30バイト(MB+8..MB+0x37 の写し) → 0x100f20-0x100f4f
NITEM   = %(nitem)d
TILEA   = $24c000

; ---- PutStr: a0=文字列, d0.w=x, d1.w=y, d2.b=属性 ----
PutStr:
        move.w  d1,d3
        lsl.w   #6,d3
        add.w   d0,d3
        add.w   d3,d3
        lea     TILEA.l,a1
        adda.w  d3,a1
ps_lp:  move.b  (a0)+,d4
        beq.s   ps_end
        cmpi.b  #$20,d4
        bne.s   ps_ok
        move.b  #$40,d4
ps_ok:  subi.b  #$30,d4
        move.b  d4,$4001(a1)
        move.b  d2,1(a1)
        addq.w  #2,a1
        bra.s   ps_lp
ps_end: rts

; ---- PutDec: d5.b=0..99, d0=x,d1=y,d2=属性 ----
PutDec:
        moveq   #0,d6
        move.b  d5,d6
        divu    #10,d6
        move.w  d1,d3
        lsl.w   #6,d3
        add.w   d0,d3
        add.w   d3,d3
        lea     TILEA.l,a1
        adda.w  d3,a1
        move.b  d6,d4
        bne.s   pd_w1
        move.b  #$10,d4
pd_w1:  move.b  d4,$4001(a1)
        move.b  d2,1(a1)
        addq.w  #2,a1
        swap    d6
        move.b  d6,$4001(a1)
        move.b  d2,1(a1)
        rts

; ---- ClearField: x=d0,y=d1,len=d7 (スペース) ----
ClrFld:
        move.w  d1,d3
        lsl.w   #6,d3
        add.w   d0,d3
        add.w   d3,d3
        lea     TILEA.l,a1
        adda.w  d3,a1
cf_lp:  move.b  #$10,$4001(a1)
        move.b  #0,1(a1)
        addq.w  #2,a1
        dbf     d7,cf_lp
        rts

; ---- ClearAll: 3レイヤーのタイルを空に ----
ClrAll:
        lea     $24c000.l,a1
        move.w  #$17ff,d7
ca_lp:  move.b  #$10,$4001(a1)   ; 空白タイル=0x10(ゲーム本体の画面クリアと同じ)
        move.b  #0,1(a1)
        addq.w  #2,a1
        dbf     d7,ca_lp
        rts
"""

ENGINE2 = """
V_I     = $100f17
V_Y     = $100f18
V_TMP   = $100f1a
V_SINP  = $100f1c

; ---- 現在行の記述子 a5 を求める ----
CurDesc:
        moveq   #0,d7
        move.b  V_CUR.l,d7
        move.w  d7,d3
        mulu    #12,d3
        lea     ITM.l,a5
        adda.l  d3,a5
        rts

; ---- 全行描画 ----
DrawAll:
        clr.b   V_I.l
da_row:
        moveq   #0,d7
        move.b  V_I.l,d7
        move.w  d7,d3
        mulu    #12,d3
        lea     ITM.l,a5
        adda.l  d3,a5
        move.w  d7,d1
        addi.w  #%(row0)d,d1
        move.w  d1,V_Y.l
        lea     V_TMP.l,a0
        move.b  #$20,(a0)
        clr.b   1(a0)
        cmp.b   V_CUR.l,d7
        bne.s   da_nc
        move.b  #$3e,(a0)
da_nc:  move.w  #%(colcur)d,d0
        move.b  #%(attr)d,d2
        jsr     PutStr.l
        movea.l (a5),a0
        move.w  #%(collab)d,d0
        move.w  V_Y.l,d1
        move.b  #%(attr)d,d2
        jsr     PutStr.l
        cmpi.b  #2,4(a5)
        beq.s   da_next
        cmpi.b  #3,4(a5)
        bne.s   da_val
        jsr     DrawGrid.l
        bra.s   da_next
da_val: move.w  #%(colval)d,d0
        move.w  V_Y.l,d1
        moveq   #11,d7
        jsr     ClrFld.l
        moveq   #0,d0
        move.b  7(a5),d0
        lea     $203f00.l,a0
        move.b  0(a0,d0.w),d5
        cmpi.b  #1,4(a5)
        beq.s   da_str
        move.w  #%(colval)d,d0
        move.w  V_Y.l,d1
        move.b  #%(attr)d,d2
        jsr     PutDec.l
        bra.s   da_next
da_str: moveq   #0,d0
        move.b  d5,d0
        lsl.w   #2,d0
        movea.l 8(a5),a2
        movea.l 0(a2,d0.w),a0
        move.w  #%(colval)d,d0
        move.w  V_Y.l,d1
        move.b  #%(attr)d,d2
        jsr     PutStr.l
da_next:
        addq.b  #1,V_I.l
        cmpi.b  #NITEM,V_I.l
        bcs.w   da_row
        rts

; ---- 値変更 d6=+1/-1 ----
ChangeVal:
        jsr     CurDesc.l
        cmpi.b  #2,4(a5)
        beq.s   cv_ret
        cmpi.b  #3,4(a5)
        beq.w   cv_grid
        moveq   #0,d0
        move.b  7(a5),d0
        lea     $203f00.l,a0
        move.b  0(a0,d0.w),d1
        add.b   d6,d1
        cmp.b   5(a5),d1
        bge.s   cv_hi
        move.b  6(a5),d1
        bra.s   cv_st
cv_hi:  cmp.b   6(a5),d1
        ble.s   cv_st
        move.b  5(a5),d1
cv_st:  move.b  d1,0(a0,d0.w)
cv_ret: rts
; 面/エリアの表: 別の面の行で左右 → その面のエリアIを選ぶ。同じ面なら左右でエリアを移動(端で一周)
cv_grid:
        move.b  5(a5),d0
        cmp.b   $203f08.l,d0
        beq.s   cg_same
        move.b  d0,$203f08.l
        move.b  #1,$203f0a.l
        rts
cg_same:
        move.b  $203f0a.l,d1
        add.b   d6,d1
        bne.s   cg_1
        move.b  6(a5),d1
cg_1:   cmp.b   6(a5),d1
        bls.s   cg_2
        moveq   #1,d1
cg_2:   move.b  d1,$203f0a.l
        rts

; ---- 面/エリアの表の1行を描く (a5=記述子, V_Y=行) ----
DrawGrid:
        move.w  #GRIDCOL,d0
        move.w  V_Y.l,d1
        moveq   #22,d7
        jsr     ClrFld.l
        moveq   #1,d6
dg_lp:  cmp.b   6(a5),d6
        bhi.w   dg_r
; MODE によって使われないマスは暗い色(ATTRDIS):
;   CUBE RUSH = 全部 / BOSS RUSH = EX STAGE の行全部と、面1〜10の行の B 以降(BOSS RUSH の行はそのまま)
        move.b  5(a5),d0        ; この行の面番号(1〜10, 11=EX, 13=BOSS RUSH)
        move.b  $203f0a.l,d4    ; 選択中のエリア
        move.b  $203f0b.l,d5    ; MODE
        cmpi.b  #1,d5
        beq.s   dg_dis
        cmpi.b  #2,d5
        bne.s   dg_en
        cmpi.b  #11,d0
        beq.s   dg_dis
        cmpi.b  #10,d0
        bhi.s   dg_en
        moveq   #1,d4           ; ボスラッシュでは面1〜10の開始は常に A
        cmpi.b  #1,d6
        bne.s   dg_dis
dg_en:  moveq   #%(attr)d,d2
        cmp.b   $203f08.l,d0
        bne.s   dg_n
        cmp.b   d4,d6
        bne.s   dg_n
        move.b  #ATTRSELGRID,d2
        bra.s   dg_n
dg_dis: move.b  #ATTRDIS,d2
dg_n:   moveq   #0,d3
        move.b  d6,d3
        subq.w  #1,d3
        lea     ROMOFS.l,a0
        moveq   #0,d0
        move.b  0(a0,d3.w),d0
        addi.w  #GRIDCOL,d0
        lsl.w   #2,d3
        lea     ROMAN.l,a0
        movea.l 0(a0,d3.w),a0
        move.w  V_Y.l,d1
        movem.l d6/a5,-(a7)
        jsr     PutStr.l
        movem.l (a7)+,d6/a5
        addq.b  #1,d6
        bra.w   dg_lp
dg_r:   rts

; ---- メニュー初期化 ----
MenuInit:
        cmpi.b  #2,MBS_REQ.l
        bne.s   mi_def
        tst.b   V_HAVE.l
        beq.s   mi_def
        lea     V_LBUF.l,a0
        lea     $203f08.l,a1
        moveq   #$2f,d7
mi_cp:  move.b  (a0)+,(a1)+
        dbf     d7,mi_cp
        bra.s   mi_scr
mi_def: lea     DEF.l,a0
        lea     $203f00.l,a1
mi_dl:  moveq   #0,d0
        move.b  (a0)+,d0
        cmpi.b  #$ff,d0
        beq.s   mi_scr
        move.b  (a0)+,0(a1,d0.w)
        bra.s   mi_dl
mi_scr: jsr     ClrAll.l
        lea     TITLE.l,a0
        move.w  #14,d0
        move.w  #2,d1
        move.b  #%(attr)d,d2
        jsr     PutStr.l
        lea     HELP1.l,a0
        move.w  #13,d0
        move.w  #27,d1
        move.b  #%(attr)d,d2
        jsr     PutStr.l
        lea     HELP2.l,a0
        move.w  #13,d0
        move.w  #28,d1
        move.b  #%(attr)d,d2
        jsr     PutStr.l
        clr.b   V_CUR.l
        move.b  MBS_P1.l,V_PIN.l
        move.b  MBS_SYS.l,V_SIN.l
        move.b  #1,V_DIRTY.l
        clr.b   V_REPC.l
        rts

; ---- メニュー 1フレーム ----
MenuFrame:
        tst.b   V_INIT.l
        bne.w   mf_run
        jsr     MenuInit.l
        move.b  #1,V_INIT.l
mf_run:
        move.b  MBS_P1.l,d0
        move.b  V_PIN.l,d1
        move.b  d0,V_PIN.l
        move.b  d1,d2
        not.b   d2
        and.b   d0,d2             ; 新規押下
        ; 押しっぱなしの連射（方向キー）
        move.b  d0,d3
        andi.b  #$0f,d3
        beq.w   mf_norep
        cmp.b   d1,d0
        bne.w   mf_norep
        addq.b  #1,V_REPC.l
        cmpi.b  #18,V_REPC.l
        bcs.w   mf_dorep
        move.b  #14,V_REPC.l
        or.b    d3,d2
        bra.w   mf_dorep
mf_norep:
        tst.b   d3
        bne.w   mf_dorep
        clr.b   V_REPC.l
mf_dorep:
        move.b  MBS_SYS.l,d4
        move.b  V_SIN.l,d5
        move.b  d4,V_SIN.l
        not.b   d5
        and.b   d4,d5             ; SYSTEM新規押下
        btst    #2,d2
        beq.w   mf_nu
        move.b  V_CUR.l,d7
        bne.w   mf_u1
        move.b  #NITEM,d7
mf_u1:  subq.b  #1,d7
        move.b  d7,V_CUR.l
        move.b  #1,V_DIRTY.l
mf_nu:  btst    #3,d2
        beq.w   mf_nd
        move.b  V_CUR.l,d7
        addq.b  #1,d7
        cmpi.b  #NITEM,d7
        bcs.w   mf_d1
        moveq   #0,d7
mf_d1:  move.b  d7,V_CUR.l
        move.b  #1,V_DIRTY.l
mf_nd:  btst    #0,d2
        beq.w   mf_nl
        movem.l d2/d4-d5,-(a7)
        moveq   #-1,d6
        jsr     ChangeVal.l
        movem.l (a7)+,d2/d4-d5
        move.b  #1,V_DIRTY.l
mf_nl:  btst    #1,d2
        beq.w   mf_nr
        movem.l d2/d4-d5,-(a7)
        moveq   #1,d6
        jsr     ChangeVal.l
        movem.l (a7)+,d2/d4-d5
        move.b  #1,V_DIRTY.l
mf_nr:  ; 決定: SYSTEMスタート or (B1 かつ START行)
        move.b  d5,d3
        andi.b  #$18,d3
        bne.w   mf_go
        btst    #4,d2
        beq.w   mf_nb1
        jsr     CurDesc.l
        cmpi.b  #2,4(a5)
        bne.w   mf_nb1
        cmpi.b  #NITEM-1,V_CUR.l
        beq.w   mf_cancel
        bra.w   mf_go
mf_nb1: btst    #5,d2
        bne.w   mf_cancel
        tst.b   V_DIRTY.l
        beq.w   mf_ret
        clr.b   V_DIRTY.l
        jsr     DrawAll.l
mf_ret: rts
mf_go:  cmpi.b  #2,$203f0b.l     ; ボスラッシュ: 面1〜10は常にエリアA、EX STAGE は使えないので面1
        bne.s   mf_gb
        cmpi.b  #11,$203f08.l
        bne.s   mf_gb1
        move.b  #1,$203f08.l
mf_gb1: cmpi.b  #10,$203f08.l
        bhi.s   mf_gb
        move.b  #1,$203f0a.l
mf_gb:  cmpi.b  #1,$203f0b.l     ; キューブラッシュ = 9面 エリア2(独自開始点)
        bne.w   mf_g1
        move.b  #9,$203f08.l
        move.b  #2,$203f0a.l
mf_g1:  move.w  #$2001,$203f1e.l    ; 隠し面(STAGE 11/12): 戻り先 = 10面のラスボス手前(X=0x200000)
        cmpi.b  #13,$203f08.l       ; 10面ボスラッシュの行(13)も表から
        beq.s   mf_g0
        cmpi.b  #10,$203f08.l
        bhi.w   mf_g2
mf_g0:
        moveq   #0,d0               ; 開始進行度 = PROGTBL[(面-1)*8 + (エリア-1)] → MB+$1e
        move.b  $203f08.l,d0
        subq.w  #1,d0
        mulu    #10,d0
        moveq   #0,d1
        move.b  $203f0a.l,d1
        subq.w  #1,d1
        add.w   d1,d0
        add.w   d0,d0
        lea     PROGTBL.l,a0
        move.w  0(a0,d0.w),$203f1e.l
mf_g2:  lea     $203f08.l,a0
        lea     V_LBUF.l,a1
        moveq   #$2f,d7
mf_sv:  move.b  (a0)+,(a1)+
        dbf     d7,mf_sv
        cmpi.b  #13,$203f08.l       ; 保存後に 10面ボスラッシュ(13) → 面10 として渡す
        bne.s   mf_g3
        move.b  #10,$203f08.l
mf_g3:  cmpi.b  #11,$203f08.l       ; EX STAGE の B → サラマンダ隠し面(12)
        bne.s   mf_g4
        cmpi.b  #2,$203f0a.l
        bne.s   mf_g4
        move.b  #12,$203f08.l
mf_g4:  move.b  #1,V_HAVE.l
        move.b  #1,MBS_DONE.l
        rts
mf_cancel:
        move.b  #2,MBS_DONE.l
        rts
"""

PAUSE = """
; ---- 装備コマンドの回数計算 (改造プレイ中、毎フレーム) ----
; 目標: START=スピード2・ミサイル・レーザー・オプション4・バリア / SHOT+START=レーザーの代わりにダブル
;       MISSILE+START=スピード2・ミサイル・オプション2
; 結果: MB+$24(1P) / +$2c(2P) に [SPEED,MISSILE,DOUBLE,LASER,OPTION,SHIELD の使用回数, スピードを下げる印]
CmdCalc:
        lea     $201000.l,a0
        lea     $203f24.l,a1
        bsr.s   cc_one
        lea     $201080.l,a0
        lea     $203f2c.l,a1
cc_one: move.b  MBS_P1.l,d2
        move.b  $69(a0),d0
        andi.b  #$1f,d0
        moveq   #2,d1
        sub.b   d0,d1
        bpl.s   cc1
        moveq   #0,d1
cc1:    move.b  d1,(a1)
        cmpi.b  #2,d0
        shi     6(a1)
        moveq   #0,d1
        tst.b   $6d(a0)
        bne.s   cc2
        moveq   #1,d1
cc2:    move.b  d1,1(a1)
        clr.b   2(a1)
        clr.b   3(a1)
        clr.b   5(a1)
        moveq   #2,d3
        btst    #5,d2
        bne.s   cc_op
        moveq   #4,d3
        btst    #4,d2
        beq.s   cc_l
        move.b  #1,2(a1)
        bra.s   cc_sh
cc_l:   move.b  #1,3(a1)
cc_sh:  tst.b   $2b(a0)
        bne.s   cc_op
        move.b  #1,5(a1)
cc_op:  move.b  $68(a0),d0
        andi.b  #7,d0
        sub.b   d0,d3
        bpl.s   cc3
        moveq   #0,d3
cc3:    move.b  d3,4(a1)
        rts

; ---- ランク表示 (改造プレイ中・RANK DISP=ON): 画面右上 行3 に "RANK nn" ----
RankDisp:
        lea     RK_T.l,a0
        move.w  #43,d0
        move.w  #3,d1
        moveq   #0,d2
        jsr     PutStr.l
        move.b  $2039c1.l,d5
        move.w  #48,d0
        move.w  #3,d1
        moveq   #0,d2
        jmp     PutDec.l

V_PST   = $100f50
V_PSEL  = $100f51
V_PPIN  = $100f52
V_PSIN  = $100f53
V_PSAV  = $101100          ; 4行x16桁x2バイト = 128（0x101100〜: 元のサブのプログラムが使っていない範囲）
MBS_INV = $203f20          ; 無敵（メインの MB+$20）
V_LINV  = $100f38          ; スタートメニューの前回値の写し（MB+$20 に対応）
PX      = 26
PY      = 14
PW      = 16
; ---- ポーズ窓: 保存/復元 (layer A, 行PY..PY+3, 桁PX..PX+PW-1) ----
PSave:  lea     V_PSAV.l,a0
        moveq   #0,d0
        bra.s   ps_go
PRest:  lea     V_PSAV.l,a0
        moveq   #1,d0
ps_go:  moveq   #3,d6
        move.w  #PY,d1
pr_row: move.w  d1,d3
        lsl.w   #6,d3
        addi.w  #PX,d3
        add.w   d3,d3
        lea     TILEA.l,a1
        adda.w  d3,a1
        moveq   #PW-1,d7
pr_col: tst.b   d0
        bne.s   pr_r
        move.b  1(a1),(a0)+
        move.b  $4001(a1),(a0)+
        bra.s   pr_n
pr_r:   move.b  (a0)+,1(a1)
        move.b  (a0)+,$4001(a1)
pr_n:   addq.w  #2,a1
        dbf     d7,pr_col
        addq.w  #1,d1
        dbf     d6,pr_row
        rts

; 1行描く: a0=文字列(選択中なら '>' 付き), d4=行番号(0..2) → PY+1+d4
PLine:  move.w  #PX+1,d0
        move.w  d4,d1
        addi.w  #PY+1,d1
        moveq   #0,d2
        jmp     PutStr.l

PDraw:  moveq   #3,d6
        move.w  #PY,d1
pd_cl:  move.w  #PX,d0
        moveq   #PW-1,d7
        movem.l d1/d6,-(a7)
        jsr     ClrFld.l
        movem.l (a7)+,d1/d6
        addq.w  #1,d1
        dbf     d6,pd_cl
        lea     PS_T.l,a0
        move.w  #PX+5,d0
        move.w  #PY,d1
        moveq   #0,d2
        jsr     PutStr.l
        moveq   #0,d4
        lea     PS_C1.l,a0
        tst.b   V_PSEL.l
        bne.s   pd_1
        lea     PS_C0.l,a0
pd_1:   bsr.w   PLine
        moveq   #1,d4
        lea     PS_G1.l,a0
        cmpi.b  #1,V_PSEL.l
        bne.s   pd_2
        lea     PS_G0.l,a0
pd_2:   bsr.w   PLine
        moveq   #2,d4
        lea     PS_I1.l,a0
        cmpi.b  #2,V_PSEL.l
        bne.s   pd_3
        lea     PS_I0.l,a0
pd_3:   bsr.w   PLine
        lea     PS_OFF.l,a0
        tst.b   MBS_INV.l
        beq.s   pd_4
        lea     PS_ON.l,a0
pd_4:   move.w  #PX+13,d0
        move.w  #PY+3,d1
        moveq   #0,d2
        jmp     PutStr.l

; ---- ポーズ 1フレーム (MBS_PAUS==1 の間) ----
; 上下: CONTINUE / GAME OVER / INVINCIBLE。INVINCIBLE の行では 左右・ショットで ON/OFF。START か ショットで決定
PauseFrame:
        tst.b   V_PST.l
        bne.s   pf_run
        move.b  #1,V_PST.l
        clr.b   V_PSEL.l
        move.b  MBS_P1.l,V_PPIN.l
        move.b  MBS_SYS.l,V_PSIN.l
        jsr     PSave.l
        jmp     PDraw.l
pf_run: move.b  MBS_P1.l,d0
        move.b  V_PPIN.l,d1
        move.b  d0,V_PPIN.l
        not.b   d1
        and.b   d0,d1
        move.b  MBS_SYS.l,d4
        move.b  V_PSIN.l,d5
        move.b  d4,V_PSIN.l
        not.b   d5
        and.b   d4,d5
        btst    #2,d1           ; 上
        beq.s   pf_dn
        subq.b  #1,V_PSEL.l
        bpl.s   pf_rd
        move.b  #2,V_PSEL.l
        bra.s   pf_rd
pf_dn:  btst    #3,d1           ; 下
        beq.s   pf_lr
        addq.b  #1,V_PSEL.l
        cmpi.b  #3,V_PSEL.l
        bcs.s   pf_rd
        clr.b   V_PSEL.l
        bra.s   pf_rd
pf_lr:  cmpi.b  #2,V_PSEL.l
        bne.s   pf_nm
        move.b  d1,d2
        andi.b  #$13,d2         ; 左右・ショット
        beq.s   pf_nm
        eori.b  #1,MBS_INV.l
        move.b  MBS_INV.l,V_LINV.l
pf_rd:  movem.l d1/d5,-(a7)
        jsr     PDraw.l
        movem.l (a7)+,d1/d5
        rts
pf_nm:  andi.b  #$18,d5
        bne.s   pf_ok
        btst    #4,d1
        beq.s   pf_ret
pf_ok:  jsr     PRest.l
        clr.b   V_PST.l
        moveq   #2,d0           ; CONTINUE / INVINCIBLE の行 → 再開
        cmpi.b  #1,V_PSEL.l
        bne.s   pf_go
        moveq   #3,d0           ; GAME OVER
pf_go:  move.b  d0,MBS_PAUS.l
pf_ret: rts
"""

def source(lab):
    return ('GRIDCOL = %d\nATTRSELGRID = %d\nATTRDIS = %d\n' % (GRID_COL, ATTR_SELGRID, ATTR_DIS)) + (ENGINE + ENGINE2 + PAUSE.replace('%', '%%')) % {'nitem': NITEM, 'row0': ROW0, 'colcur': COL_CUR, 'collab': COL_LABEL, 'colval': COL_VAL, 'attr': ATTR_TXT, 'attrsel': ATTR_SEL}
