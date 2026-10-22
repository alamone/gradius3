"""メインCPU側スタブ（純正313へのパッチ）
空き領域: A=0xd4aa(425B) B=0xd8f6(532B) C=0x3fd9a(〜0x3feff, 358B)  ※0x3ff00-0x3fff0 は ROM合計の微調整用に確保
"""
MB = 0x103f00           # メールボックス（共有RAM。サブ側は 0x203f00）。要MAME確認: 未使用であること
# オフセット
O_P1, O_SYS, O_UNLOCK, O_REQ, O_DONE, O_KIND, O_PAUSE, O_MODRUN = 0, 1, 2, 3, 4, 5, 6, 7
O_STAGE, O_LOOP, O_AREA, O_MODE, O_BEGIN = 8, 9, 10, 11, 12

CONSTS = f"""
MB      = ${MB:x}
MB_P1   = ${MB+O_P1:x}
MB_SYS  = ${MB+O_SYS:x}
MB_UNLK = ${MB+O_UNLOCK:x}
MB_REQ  = ${MB+O_REQ:x}
MB_DONE = ${MB+O_DONE:x}
MB_KIND = ${MB+O_KIND:x}
MB_PAUS = ${MB+O_PAUSE:x}
MB_RUN  = ${MB+O_MODRUN:x}
MB_STG  = ${MB+O_STAGE:x}
MB_LOOP = ${MB+O_LOOP:x}
MB_AREA = ${MB+O_AREA:x}
MB_MODE = ${MB+O_MODE:x}
MB_BEG  = ${MB+O_BEGIN:x}
ApplyStart = $d8f6
"""

# --- エリアA: 入力ミラー / スタート判定フック / メニュー状態 ---
SRC_A = CONSTS + """
MB_EMIS  = $103f11
MB_EDBL  = $103f12
MB_ELSR  = $103f13
        org $d4aa
; ---- キューブラッシュのパターン固定 (0x26238 の move.b $40032.l,d5 を置換) ----
; キューブの出現の高さは「その瞬間の $40032 xor $40033」で16通りから決まる。
; 改造プレイ中で CUBE HEIGHT/SHIFT/TYPE のどれかが R 以外のとき、1個目が出る瞬間だけ
; フレームカウンタを「その並びになる値」(サブが毎フレーム $103e30 に用意)にする。2個目以降は純正どおり
CubeSeed:
        jmp     CUBESEED2.l      ; 本体は 0xd653〜 の空き領域（CubeSeed2）
        even
StubIn:
        jsr     $33b8.l
        move.b  $c8003.l,d0
        not.b   d0
        move.b  d0,MB_P1.l
        LOCKCALL
        move.b  $c8001.l,d0
        not.b   d0
        move.b  d0,MB_SYS.l
        cmpi.b  #1,MB_PAUS.l    ; ポーズ中はフレームカウンタを進めない（キューブの並びがポーズでずれないように）
        bne.s   si_np
        subq.w  #1,$40032.l
si_np:  tst.b   $103ed0.l       ; サブからスコアの描き直しの依頼（CUBE INFO を OFF にした／キューブがくっついて点が入った）
        beq.s   ms_nr
        clr.b   $103ed0.l
        movem.l d0-d7/a0-a6,-(a7)
        jsr     SCOREHK.l
        movem.l (a7)+,d0-d7/a0-a6
ms_nr:  jsr     HUDPAL.l
        rts

HookStart:
        clr.b   MB_RUN.l        ; アトラクト中は改造プレイ中フラグを落とす
        tst.b   MB_UNLK.l
        beq.s   hs_norm
        move.w  $40042.l,d0
        not.w   d0
        and.w   $40040.l,d0
        andi.w  #$18,d0
        beq.s   hs_norm
        tst.b   $4004a.l
        bne.s   hs_cred
        move.b  $40034.l,d1
        beq.s   hs_norm
hs_cred:
        moveq   #1,d2
        btst    #3,d0
        bne.s   hs_k
        moveq   #2,d2
        tst.b   $4004a.l
        bne.s   hs_k
        cmpi.b  #2,$40034.l
        bcs.s   hs_norm
hs_k:
        move.b  $c8003.l,d1
        moveq   #1,d3
        btst    #2,d1
        beq.s   hs_go
        moveq   #2,d3
        btst    #3,d1
        bne.s   hs_norm
hs_go:
        move.b  d3,MB_REQ.l
        move.b  d2,MB_KIND.l
        clr.b   MB_DONE.l
        move.b  #3,$40005.l
        ori     #1,ccr
        rts
hs_norm:
        jmp     $2968.l

; 新トップ状態3: メニュー実行中（サブCPUが描画・操作）。確定/キャンセルを待つ
ModState:
        jsr     PALCOPY.l       ; メニューの背景の色（サブが用意したら写す）
        move.l  #$6000,$1038e8.l ; スクロール位置 0 に固定（レジスタ値 = 変数-0x6000 を毎フレーム反映する処理がある）
        move.l  #$6000,$1038f0.l
        clr.l   $1038ec.l
        clr.l   $1038f4.l
        clr.w   $10393c.l
        clr.w   $10393e.l
        move.b  MB_DONE.l,d0
        beq.s   ms_rts
        cmpi.b  #2,d0
        beq.s   ms_cancel
        move.b  $40034.l,d1
        cmpi.b  #2,MB_KIND.l
        beq.s   ms_p2
        moveq   #1,d7
        jsr     $2a76.l
        clr.b   $40080.l
        bra.s   ms_begin
ms_p2:  moveq   #2,d7
        jsr     $2a76.l
        move.b  #1,$40080.l
ms_begin:
        jsr     $29c0.l
        jsr     ApplyStart.l
        clr.b   MB_REQ.l
        clr.b   MB_DONE.l
ms_rts: rts
ms_cancel:
        clr.b   $40005.l
        clr.b   MB_REQ.l
        clr.b   MB_DONE.l
        rts

; 新状態表（0x1e58の代わり）
StateTbl:
        dc.l    $1e6c, $1e64, $28ce, ModState
"""

# --- エリアB: 開始設定の反映 ---
SRC_B = CONSTS + """
MB_LIVES = $103f0d
SetEdit  = $d4aa
MB_PEND  = $103f1a
MB_EMIS  = $103f11
MB_EDBL  = $103f12
MB_ELSR  = $103f13
MB_TYPE  = $103f0f
MB_SHD   = $103f15
        org $d8f6
; メニュー確定後（0x29c0 で通常のゲーム開始処理を済ませた直後）に呼ばれる
ApplyStart:                     ; メニュー確定直後: 改造プレイ開始の印だけ付ける（面・周回は ApplyStage で後から）
        move.b  #1,MB_RUN.l
        move.b  #7,MB_PEND.l
        move.w  #$ff00,$103f38.l
        clr.b   $103f21.l       ; START 押下時間
        move.b  #1,$103f22.l    ; 装備コマンドの残り回数: 通常1回 / キューブ・ボスラッシュは無制限($ff)
        tst.b   MB_MODE.l
        beq.s   as_1
        st      $103f22.l
as_1:
        lea     $101000.l,a0
        bsr.w   sk_set
        lea     $101080.l,a0
        bsr.s   sk_set
        rts

; 面・周回・エリアの反映。装備選択画面が終わり、面の準備(状態2)に入る瞬間に1回だけ呼ばれる
; （先に書くと、周回≠0 のときゲームが選択画面を飛ばしてしまうため）
ApplyStage:
        move.b  MB_STG.l,d0
        subq.b  #1,d0           ; 面1..10 → 内部 0..9 (11,12=隠し面 → 戻り先は10面)
        cmpi.b  #9,d0
        bls.s   as_nb
        moveq   #9,d0
as_nb:  move.b  d0,$101051.l
        move.b  d0,$1010d1.l
        move.b  MB_LOOP.l,d0
        subq.b  #1,d0
        add.b   d0,d0
        move.b  d0,$101063.l
        move.b  d0,$1010e3.l
; エリア(復活地点)指定: 0x4ce8 は「$101063 bit0≠0 のとき $101052(進行度)以下で最後のエリア開始点」を使う
SetArea:                        ; 進行度はサブCPUがビルド時の表から計算して MB+$1e に置く
        ori.b   #1,$101063.l    ; 「再開」扱い: 1周目の新規開始で面が1面に戻される処理(0x37c6)を避ける
        ori.b   #1,$1010e3.l
        move.w  $103f1e.l,d6
        beq.s   sa_ret
        move.w  d6,$101052.l
        move.w  d6,$1010d2.l
sa_ret: rts

; （タイプ選択画面の差し替え SkipType は、改造プレイでも純正どおり表示するようになったので外した）
sk_set: cmpi.b  #1,MB_MODE.l    ; 残機はディップスイッチどおり。キューブラッシュはそれに +4（遊んでいない側＝残機0 には足さない）
        bne.s   sk_sr
        tst.b   $50(a0)
        beq.s   sk_sr
        move.b  $50(a0),d0      ; 残機は BCD
        moveq   #4,d1
        dc.w    $44fc,$0000     ; move #0,ccr
        dc.w    $c101           ; abcd d1,d0
        move.b  d0,$50(a0)
sk_sr:  rts

; ---- 改造モードのポーズ(プレイ中 START)。戻り d0≠0 ならこのフレームのゲーム処理を止める ----
; MB_PAUS: 0=通常 1=ポーズ中(サブがメニュー表示) 2=再開 3=ゲームオーバー
PauseChk:                       ; 戻り d0: 0=通常 1=止める 2=装備コマンド実行
        move.b  MB_PAUS.l,d0
        beq.s   pc_chk
        cmpi.b  #2,d0
        bcs.s   pc_frz
        beq.s   pc_res
        clr.b   MB_PAUS.l
        clr.b   $101050.l
        clr.b   $1010d0.l
        move.b  #8,$40029.l
        clr.b   $4002b.l
        moveq   #1,d0
        rts
pc_res: clr.b   MB_PAUS.l
        moveq   #0,d0
        rts
pc_chk: lea     $103f21.l,a0    ; 1P START: 短く押す=装備コマンド / 約1秒押し続ける=ポーズ
        btst    #3,MB_SYS.l
        beq.s   pc_up
        addq.b  #1,(a0)
        cmpi.b  #60,(a0)
        bne.s   pc_no
        move.b  #1,MB_PAUS.l
pc_frz: moveq   #1,d0
        rts
pc_up:  move.b  (a0),d1
        clr.b   (a0)
        tst.b   d1
        beq.s   pc_no
        cmpi.b  #60,d1
        bcc.s   pc_no
        moveq   #2,d0
        rts
pc_no:  moveq   #0,d0
        rts


        even

; ---- 隠しメニューの解除/ロック (毎フレーム, d0=P1 正論理) ----
; 解除: 上+A → 全部離す → 下+A   ロック: 下+A → 離す → 上+A   (各3秒以内, プレイ中以外)。放置300秒で自動ロック
; MB+$3a 段階 / +$3b 種類(1=解除,0=ロック) / +$3c 残り時間 / +$3e 最後の操作時刻
Lock:   lea     $103f3a.l,a0
        cmpi.b  #2,$40005.l
        bcc.w   lk_act
; 解除/ロックのコマンド (各段階3秒以内):
;   段階0: レバー上(下)＋A がそろう → 1: 全部離す → 2: レバー下(上)＋A がそろう → 3: 全部離す → 成立
;   レバーとボタンを押す順番・同時押しは問わない。上から始めると解除、下から始めるとロック
        andi.b  #$1f,d0
        move.b  (a0),d1
        beq.s   lk_0
        subq.b  #1,2(a0)
        beq.s   lk_clr
        btst    #0,d1           ; 段階1・3 = 離すのを待つ
        beq.s   lk_2
        tst.b   d0
        bne.s   lk_idle
        cmpi.b  #3,d1
        bne.s   lk_nx
        move.b  1(a0),MB_UNLK.l
        clr.w   4(a0)           ; 放置カウンタ
        bra.s   lk_clr
lk_2:   moveq   #$18,d3         ; 段階2: 最初と逆の方向＋A
        tst.b   1(a0)
        bne.s   lk_t
        moveq   #$14,d3
lk_t:   cmp.b   d3,d0
        bne.s   lk_idle
lk_nx:  addq.b  #1,(a0)
        move.b  #180,2(a0)
        bra.s   lk_idle
lk_0:   moveq   #1,d2
        cmpi.b  #$14,d0
        beq.s   lk_s
        moveq   #0,d2
        cmpi.b  #$18,d0
        bne.s   lk_idle
lk_s:   move.b  d2,1(a0)
        bra.s   lk_nx
lk_clr: clr.b   (a0)
lk_idle:                        ; 300秒自動ロック(遊んでいない間)
        tst.b   MB_UNLK.l
        beq.s   lk_r
        addq.w  #1,4(a0)        ; 放置フレーム数(ゲームのフレームカウンタはアトラクト一巡で0に戻るため自前で数える)
        cmpi.w  #18000,4(a0)    ; 300秒
        bcs.s   lk_r
        clr.b   MB_UNLK.l
lk_r:   rts
lk_act: clr.b   (a0)
        clr.w   4(a0)
        rts


; ---- 開始時のハンターの設定（PlayHook から） ----
PendB:  move.b  $103f1b.l,d0    ; HUNTER NEXT (0=そのまま, 1..3 → $42e73=0..2)
        beq.s   pb_h1
        subq.b  #1,d0
        move.b  d0,$42e73.l
pb_h1:  moveq   #0,d0           ; HUNTER TIME (0=そのまま, n → $42e70=n*60: オプション1個で n 秒)
        move.b  $103f1c.l,d0
        beq.s   pb_r
        mulu    #60,d0
        move.w  d0,$42e70.l
pb_r:   rts

; ---- キューブラッシュ（改造プレイ）の点数はハイスコア・ランキングに入れない ----
CkCR:   tst.b   MB_RUN.l        ; 戻り: eq = キューブラッシュの改造プレイ
        beq.s   ck_n
        cmpi.b  #1,MB_MODE.l
        rts
ck_n:   cmpi.b  #1,MB_RUN.l
        rts
; 0x197e の cmp.l $40058.l,d7 の置き換え（点数加算後のハイスコア更新）: キューブラッシュなら更新しない（C=1）
HiHk:   bsr.s   CkCR
        bne.s   hh_n
        ori     #1,ccr
        rts
hh_n:   cmp.l   $40058.l,d7
        rts
; 0x226c4 の move.l $101054.l,d0 の置き換え（ゲームオーバー後のランキング判定）: キューブラッシュなら 0点として扱う
RankHk: move.l  $101054.l,d0
        bsr.s   CkCR
        bne.s   rh_r
        moveq   #0,d0
rh_r:   rts
; 見出しの暗めの色（F面パレット6・ゲームでは未使用）: 改造プレイ中は毎フレーム入れる
HudPal: tst.b   MB_RUN.l
        beq.s   hp_r
        move.w  #$5252,$800de.l
        move.w  #$10a9,$800d2.l
        tst.b   $103ed4.l       ; CUBE COLOR 有効: 飛んでくるキューブの色（サブが共有RAMに置いた5色分のパレット）を写す
        beq.s   hp_r
        lea     $103cb0.l,a0    ; 共有RAMの未使用域（0x103cb0〜0x103df3: パレット9つ分）
        moveq   #8,d2
hp_p:   movea.l (a0)+,a1
        moveq   #15,d1
hp_w:   move.w  (a0)+,(a1)+
        dbf     d1,hp_w
        dbf     d2,hp_p
hp_r:   rts

; ---- 敵出現表ポインタ ($42e00) の補正 (0x154aa の move.l a6,$42e00 を置換) ----
; 改造プレイ・10面(マップ13)・X<0x780(ボスラッシュ区間) のときだけ「X 以上の最初のイベント」から始める
; (ゲーム本来の X/0x300 刻みの索引だと、ボス直前から始めたときにボスの出現イベントを取りこぼす/前のボスが出る)
EvPtr:  tst.b   MB_RUN.l
        beq.s   ev_st
        cmpi.b  #13,$1039c0.l
        bne.s   ev_st
        move.l  $1038de.l,d0
        lsr.l   #8,d0
        cmpi.w  #$780,d0
        bcc.s   ev_st
        movea.l #$252d4,a6
ev_lp:  cmp.w   (a6),d0
        bls.s   ev_st
        lea     10(a6),a6
        bra.s   ev_lp
ev_st:  move.l  a6,$42e00.l
        rts

"""

# --- エリアC: エディット装備 / プレイ開始時のパワーアップ適用 ---
SRC_C = CONSTS + """
MB_SPD   = $103f10
MB_EMIS  = $103f11
MB_EDBL  = $103f12
MB_ELSR  = $103f13
MB_OPT   = $103f14
MB_PMIS  = $103f17
MB_PSHOT = $103f18
MB_PSHON = $103f19
MB_PEND  = $103f1a
MB_MODE  = $103f0b
PauseChk = $%x
ApplyStage = $%x
        org $3fd9a

; ゲーム状態5(プレイ中)の代わり: シールド色・ポーズ/装備コマンド・開始時のハンター設定
PlayHook:
        tst.b   MB_RUN.l
        beq.w   ph_go
        cmpi.b  #1,$103f16.l    ; SHD COLOR (1=純正の青)
        beq.s   ph_nc
        lea     $103e00.l,a0    ; サブが用意した7色 → シールドのパレット(0x131-0x136,0x13e)
        lea     $80262.l,a1
        moveq   #5,d7
ph_cl:  move.w  (a0)+,(a1)+
        dbf     d7,ph_cl
        move.w  (a0),$8027c.l
ph_nc:  jsr     PauseChk.l
        subq.b  #1,d0
        beq.s   ph_rts          ; 1: ポーズ中
        bcs.s   ph_np
        bsr.s   Command         ; 2: 装備コマンド
ph_np:
        tst.b   MB_PEND.l
        beq.s   ph_go
        movem.l d0-d7/a0-a6,-(a7)
        lea     $101000.l,a2
        moveq   #0,d0           ; bit0=1P 未適用 / bit1=2P 未適用
        tst.b   $4007f.l
        beq.s   ph_p
        lea     $101080.l,a2
        moveq   #1,d0
ph_p:   bclr    d0,MB_PEND.l
        beq.s   ph_x
        jsr     PENDB.l         ; ハンターの設定（本体は B 領域）
        move.b  $103f0d.l,d4    ; SPEED (0〜5): スピードアップを n 回使う
        beq.s   ph_g
        moveq   #1,d3
        bsr.w   Use
ph_g:   move.b  $103f23.l,d0    ; CAPSULE (0=そのまま, 1〜7 = SPEEDUP〜!): カプセルゲージの位置
        beq.s   ph_h2
        move.b  d0,$6a(a2)
ph_h2:
ph_x:   movem.l (a7)+,d0-d7/a0-a6
ph_go:  jmp     $3a24.l
ph_rts: rts

; ---- 装備コマンド: サブCPUが「目標の装備にそろえるのに各枠を何回使うか」を計算済み(MB+$24〜 / 2P は +$2c〜) ----
; 枠 1=SPEED 2=MISSILE 3=DOUBLE 4=LASER 5=OPTION 6=SHIELD、+6 = スピードを2段階へ下げる印
Command:
        jsr     CMDCNT.l        ; d1 = 残り回数 ($ff=無制限。無敵中も無制限)
        beq.s   cm_r
        addq.b  #1,d1
        beq.s   cm_go
        subq.b  #1,$103f22.l
cm_go:  movem.l d0-d7/a0-a6,-(a7)
        lea     $101000.l,a2
        lea     $103f24.l,a4
        tst.b   $4007f.l
        beq.s   cm_p
        lea     $101080.l,a2
        lea     $103f2c.l,a4
cm_p:   lea     $101f60.l,a3    ; 取得処理(0x8b0e)と同じ: シールド等のオブジェクト枠
        tst.b   6(a4)
        beq.s   cm_s
        move.w  #$280,$2c(a2)   ; スピード2段階 = 0x100+0xc0*2
        move.w  #$8102,$1e(a2)
        andi.b  #$e0,$69(a2)
        ori.b   #2,$69(a2)
cm_s:   moveq   #1,d3
cm_lp:  move.b  -1(a4,d3.w),d4
        bsr.s   Use
        addq.w  #1,d3
        cmpi.w  #7,d3
        bne.s   cm_lp
        move.b  #1,$6a(a2)      ; カプセルゲージの選択位置を SPEED UP に
        movem.l (a7)+,d0-d7/a0-a6
cm_r:   rts
; d3=枠番号 d4=回数
Use:    andi.w  #$ff,d4
        subq.w  #1,d4
        bmi.s   us_r
us_lp:  movem.l d3-d4/a2-a4,-(a7)
        lea     $70(a2),a1
        add.w   d3,d3
        adda.w  d3,a1
        moveq   #0,d7
        move.b  1(a1),d7
        lsl.w   #2,d7
        lea     $8ce6.l,a6
        movea.l 0(a6,d7.w),a6
        jsr     (a6)
        movem.l (a7)+,d3-d4/a2-a4
        dbf     d4,us_lp
us_r:   rts

; ---- ゲーム状態2(面の準備)の入口フック: モード別の面設定 ----
; MODE: 0=通常 1=キューブラッシュ 2=ボスラッシュ
StageHook:
        tst.b   MB_RUN.l
        beq.w   sh_go
        tst.b   $4002b.l
        bne.w   sh_go
        moveq   #0,d0           ; キューブの数列を初期化(開始・再開のたび同じ並びにする)
        move.b  $103f1d.l,d0
        mulu    #40503,d0
        move.w  d0,$103e30.l
        bclr    #2,MB_PEND.l    ; 開始時1回だけ: 面・周回・エリアを反映
        beq.s   sh_m
        jsr     ApplyStage.l
        move.b  $103f08.l,d0    ; STAGE 11=グラディウス隠し面 12=サラマンダ隠し面
        subi.b  #10,d0
        bls.s   sh_m
        ; 隠し面: 0x3bba と同じ手順（戻り先 = 10面のラスボス手前の復活地点）
        move.b  d0,$103957.l
        move.w  #$ffff,$103cc0.l
        move.w  $101052.l,$103cc2.l
        move.b  $101051.l,$103cc4.l
        addi.b  #10,d0
        move.b  d0,$101051.l
        move.w  #$310,$101052.l
        ori.b   #1,$101063.l
        bra.s   sh_go
sh_m:   cmpi.b  #2,MB_MODE.l
        bne.s   sh_go
sh_boss:                        ; ボスラッシュ (開始位置はサブが用意するボスラッシュ用エリア表で決まる)
        moveq   #0,d0
        move.b  $101051.l,d0
        andi.b  #$0f,d0
        cmpi.b  #3,d0           ; 4面(高速面・ボスなし)は飛ばす
        bne.s   sh_b1
        addq.b  #1,$101051.l
        addq.b  #1,d0
sh_b1:  cmp.b   $103f38.l,d0    ; 面が変わった回数を数え、一巡したらゲームオーバー
        beq.s   sh_go
        jsr     BOSSSET.l       ; = move.b d0,$103f38.l ＋ 次の面もボス手前から始める
        addq.b  #1,$103f39.l
        cmpi.b  #10,$103f39.l   ; 開始面 + 8面 → 開始面に戻った(10回目)
        bcs.s   sh_go
        move.b  #3,$103f06.l    ; 一巡した → ポーズの「GAME OVER」と同じ処理をプレイ開始時に行わせる
sh_go:  jmp     $3790.l

; ---- エリア開始表の差し替え (0x4cfc の lea $54fe,a6 を置換) : 改造プレイ時のみ独自表 ----
AreaTbl:
        lea     $54fe.l,a6
        tst.b   MB_RUN.l
        beq.s   at_r
        lea     $103f40.l,a6    ; サブCPUが共有RAMに置く独自エリア表(ポインタ16個+表)
at_r:   rts

"""

import os
CUBEX = int(os.environ.get('CUBEX', '54000'), 16); CUBEY = int(os.environ.get('CUBEY', '0'), 16)
# 10面(マップ13)の独自エリア表。
# ボスラッシュの各ボス = 敵出現表(0x252d4)のボス出現イベントの約0xc4手前。ボス1 = 0x11c00、
#   ボス2〜6 = 0x21c02/0x35bdd/0x49c21/0x5dc03/0x71bde（端数を不規則に数単位ずらす）
# ボスラッシュ後 = EvPtr の補正区間(X<0x780)を抜けた直後の 0x7a000 / ラスボス手前 = 0x25c000
ST10 = [(0, 0x20000), (0x11c00, 0x20000), (0x21c02, 0x20000), (0x35bdd, 0x20000), (0x49c21, 0x20000),
        (0x5dc03, 0x20000), (0x71bde, 0x20000), (0x7a000, 0x20000), (0xc0000, 0), (0xf0000, 0), (0x120000, 0),
        (0x148000, 0), (0x180000, 0), (0x1b0000, 0), (0x200000, 0), (0x25c000, 0)]
# メニューの構成:
#   STAGE 10 = 開始 / ボスラッシュ直後 / 本来の復活地点7つ / 最終地点   BOSS RUSH = ボス2〜6の手前
for _kv in os.environ.get('ST10X', '').split(','):      # テスト用: ST10X="2=24000,3=38000"
    if _kv: _i, _v = _kv.split('='); ST10[int(_i)] = (int(_v, 16), ST10[int(_i)][1])
ST10_ROW = [0, 7, 8, 9, 10, 11, 12, 13, 14, 15]
BR_ROW = [2, 3, 4, 5, 6]
# 9面 = 開始 / 0x58000(キューブ地帯の手前。キューブラッシュもここから) / 0x5c000(ボス手前)
ST9 = [(0, 0), (0x58000, 0), (0x5c000, 0)]
if os.environ.get('ST9X'): ST9 = [(0, 0)] + [(int(v, 16), 0) for v in os.environ['ST9X'].split(',')]
# 3面 = 本来の8地点 + ビッグコアMkIII手前 0x1ca000 (Y は8番目と同じ)
MK3 = (int(os.environ.get("MK3X", "1ca000"), 16), 0x30000)
EXT10 = 0x103e40                                  # 10面の表を置く共有RAM (0x103e40〜0x103ec7, 起動後は未使用)
PTCOLS = 10                                       # PROGTBL の1行の語数

def _prog(x):
    return ((x >> 8) + 1) if x else 0

def progress_tables():
    """(PROGTBL: 行1..13 x エリア1..10 の開始進行度, 面idx0..15 のボス接近進行度) をメインROMから算出
    行11/12(隠し面)は未使用、行13 = 10面ボスラッシュ"""
    import struct
    d = open('/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/work/main313.bin', 'rb').read()
    L = lambda a: struct.unpack('>I', d[a:a+4])[0]
    smap = d[0x69ce:0x69de]
    custom = {1: ST9, 5: None}
    def areas(m):
        if custom.get(m): return custom[m]
        a = L(0x54fe + 4*m); r = []
        while L(a) != 0x0fffffff and len(r) < 16: r.append((L(a), L(a+4))); a += 8
        if m == 5: r.append(MK3)
        return r
    def row(xs):
        xs = list(xs) + [xs[-1]] * (PTCOLS - len(xs))
        return [_prog(x) for x in xs[:PTCOLS]]
    pt = []
    for st in range(9):
        ar = []
        for x, y in areas(smap[st]):            # 同じ位置の重複エントリは1つにまとめる(メニューの表と一致)
            if x not in ar: ar.append(x)
        pt += row(ar)
    pt += row([ST10[i][0] for i in ST10_ROW])
    pt += [0] * (2 * PTCOLS)
    pt += row([ST10[i][0] for i in BR_ROW])
    bt = []
    for st in range(16):
        m = smap[st]; v = 0
        if m != 0xff:
            a = L(0x4f06 + 4*m)
            while L(a) != 0xffffffff:
                if d[a+5] & 0x80: v = L(a) >> 8; break
                a += 6
        bt.append(v)
    return pt, bt

def ext10_blob(boss=False):
    """共有RAM EXT10 に置く10面の表 (ボスラッシュ時はボス1直前から)"""
    import struct
    t = ST10[1:] if boss else ST10
    b = b''.join(struct.pack('>II', x, y) for x, y in t + [(0x0fffffff, 0)])
    assert len(b) <= 0x88
    return b + bytes(0x88 - len(b))

def area_table_blob(base=0x103f40):
    """共有RAM base に置く独自エリア表 (メインCPU空間のアドレスで構成)"""
    import struct
    d = open('/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/work/main313.bin', 'rb').read()
    L = lambda a: struct.unpack('>I', d[a:a+4])[0]
    a = 0x560a; m5 = []
    while L(a) != 0x0fffffff: m5.append((L(a), L(a+4))); a += 8
    m1 = ST9 + [(0x0fffffff, 0)]
    m5 = m5 + [MK3, (0x0fffffff, 0)]
    p1 = base + 64; p5 = p1 + 8 * len(m1)
    ptr = [0x553a, p1, 0x557a, 0x55aa, 0x55da, p5, 0x5652, 0x5682, 0x56b2, 0x56e2, 0x5712, 0x573a, 0x576a, EXT10, 0x57ea, 0]
    assert L(0x54fe + 4*5) == 0x560a
    b = b''.join(struct.pack('>I', x) for x in ptr)
    b += b''.join(struct.pack('>II', x, y) for x, y in m1 + m5)
    assert len(b) <= 0xc0
    return b + bytes(0xc0 - len(b))

BRDELTA = int(os.environ.get('BRDELTA', '14000'), 16)   # ボスラッシュ: ボス接近位置のこれだけ手前から（全面で検証済み。0x10000 だと着いた瞬間に面クリアになる面がある）

def boss_area_blob(base=0x103f40):
    """ボスラッシュ用エリア表: 各面(4面・10面を除く)の表を「ボス接近位置-BRDELTA」の1件だけにする。
    死んだときも必ずボス直前から再開する。"""
    import struct
    d = open('/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/work/main313.bin', 'rb').read()
    L = lambda a: struct.unpack('>I', d[a:a+4])[0]
    smap = d[0x69ce:0x69de]
    pt, bt = progress_tables()
    ptr = [L(0x54fe + 4*m) for m in range(16)]
    ptr[13] = EXT10
    body = b''
    for st in (0, 1, 2, 4, 5, 6, 7, 8):
        m = smap[st]; bx = (bt[st] << 8) - BRDELTA
        a = ptr[m]; y = 0
        while L(a) != 0x0fffffff and L(a) <= bx: y = L(a+4); a += 8
        ptr[m] = base + 64 + len(body)
        body += struct.pack('>IIII', bx, y, 0x0fffffff, 0)
    b = b''.join(struct.pack('>I', x) for x in ptr) + body
    assert len(b) <= 0xc0, len(b)
    return b + bytes(0xc0 - len(b))

LOCK_SUSPEND = True        # 解除・ロックのコマンドを一時停止（True の間は常に解除状態）。戻すときは False
INV_ADDR = 0xd6a0          # 0xd653〜0xd8f5 の未使用データ領域（エディット左右切り替えの後ろ）
SRC_INV = CONSTS + """
MB_INV  = $103f20
; Z=0 なら無敵（改造プレイ中かつ INVINCIBLE=ON）
InvChk: tst.b   MB_RUN.l
        beq.s   ic_r
        tst.b   MB_INV.l
ic_r:   rts
; 0x7bc4 / 0xae22 の move.b #1,$400a2.l を置き換え（ここから先が死亡処理）
DieA:   bsr.s   InvChk
        bne.s   da_inv
        move.b  #1,$400a2.l
        rts
da_inv: addq.l  #4,sp
        clr.w   $1a(a0)
        jmp     $7bf4.l
DieB:   bsr.s   InvChk
        bne.s   db_inv
        move.b  #1,$400a2.l
        rts
db_inv: addq.l  #4,sp
        clr.w   $1a(a0)
        jmp     $ae52.l

; ---- テクニカル/ビギナー選択（改造プレイ）: ビギナーは選べない・灰色 ----
; 0x6b16 の andi.b #2,d6 / beq.s を置き換え（右でビギナーへ移る処理）
TypeBeg: tst.b  MB_RUN.l
        bne.s   tb_no
        andi.b  #2,d6
        beq.s   tb_no
        rts
tb_no:  addq.l  #4,sp
        rts
; 0x6a90 の jsr $e824（ビギナーの枠 = パレット $80600 を「選ばれていない色」にする）を置き換え
TypeGrey: tst.b MB_RUN.l
        beq.s   tg_n
        lea     GREYPAL.l,a0
        lea     $80600.l,a1
        moveq   #15,d1
tg_lp:  move.w  (a0)+,(a1)+
        dbf     d1,tg_lp
        rts
tg_n:   jmp     $e824.l
GREYPAL: GREYDATA
; ボスラッシュ: 面が変わるたび、その面のボス手前を「再開位置」にする（d0 = 面 0..9）
BossSet: move.b d0,$103f38.l
        move.l  a0,-(sp)
        move.w  d0,-(sp)
        add.w   d0,d0
        lea     BOSSPROG.l,a0
        move.w  0(a0,d0.w),d0
        beq.s   bs_x
        move.w  d0,$101052.l
        move.w  d0,$1010d2.l
        ori.b   #1,$101063.l
        ori.b   #1,$1010e3.l
bs_x:   move.w  (sp)+,d0
        move.l  (sp)+,a0
        rts
BOSSPROG: BOSSDATA
; ---- キューブの出現の瞬間（0x26238 の move.b $40032.l,d5 の置き換え。CubeSeed から来る）----
CubeSeed2:
        tst.b   $103f07.l
        beq.s   cs_x
        cmpi.w  #1,$48(a3)
        bne.s   cs_rec
        move.b  $103f35.l,d5
        or.b    $103f36.l,d5
        or.b    $103f37.l,d5
        beq.s   cs_r
CUBESEEDBODY
cs_r:   move.w  $40032.l,$103e3a.l   ; 1個目の瞬間のカウンタ（サブが H/S/T を割り出してプレイ中に表示）
cs_rec: move.w  $48(a3),$103e36.l    ; 何個目か と その瞬間のカウンタ（サブが予想と比べて処理落ちのずれを見る）
        move.w  $40032.l,$103e38.l
cs_x:   move.b  $40032.l,d5
        rts
; メニューの背景: サブが共有RAM $102000 に置いたスプライトの色(256語)をパレット $80200〜 へ（$103e34 が合図）
PalCopy: tst.b  $103e34.l
        beq.s   pc_r
        clr.b   $103e34.l
        lea     $102000.l,a0
        lea     $80200.l,a1
        move.w  #255,d0
pc_l:   move.w  (a0)+,(a1)+
        dbf     d0,pc_l
pc_r:   rts
; 0x1d24 の jsr $326e（CREDIT の表示）を置き換え: 隠しメニュー表示中（トップ状態3）は出さない
; スコア表示(0x180a: 2P→HI→1P の順に3つ描く)の入口: キューブラッシュで CUBE INFO を ON にしている間は 1P だけ描く（HI・2P の場所にキューブの情報）
ScoreHk: tst.b  $103ed1.l       ; サブが「CUBE INFO 表示中」としたとき
        bne.s   sk_1p
        jmp     $180a.l
sk_1p:  moveq   #0,d0
        jmp     $180e.l
CredHook: cmpi.b #3,$40005.l
        beq.s   ch_r
        jmp     $326e.l
ch_r:   rts
; 面クリア → 次の面（状態7 の 0x3c7a: clr.w $101052 を置き換え）。ボスラッシュなら次の面もボス手前から
NextStg: tst.b  MB_RUN.l
        beq.s   ns_n
        cmpi.b  #2,MB_MODE.l
        bne.s   ns_n
        movem.l d0/a0,-(sp)
        moveq   #0,d0
        move.b  $101051.l,d0
        andi.b  #$0f,d0
        addq.b  #1,d0
        cmpi.b  #10,d0
        bcs.s   ns1
        moveq   #0,d0
ns1:    cmpi.b  #3,d0           ; 4面(ボスなし)は飛ばす: ここで1つ進めておくと 0x68d4 で5面になる
        bne.s   ns2
        addq.b  #1,$101051.l
        moveq   #4,d0
ns2:    move.b  d0,$103f38.l
        addq.b  #1,$103f39.l    ; 一巡したらゲームオーバー（StageHook と同じ数え方）
        cmpi.b  #10,$103f39.l
        bcs.s   ns3
        move.b  #3,$103f06.l
ns3:    add.w   d0,d0
        lea     BOSSPROG.l,a0
        move.w  0(a0,d0.w),d0
        move.w  d0,$101052.l
        move.w  d0,$1010d2.l
        ori.b   #1,$101063.l
        ori.b   #1,$1010e3.l
        movem.l (sp)+,d0/a0
        rts
ns_n:   clr.w   $101052.l
        rts
; 0x68d4（次の面へ）の中の jsr $695c（位置を0に戻す）を置き換え: ボスラッシュなら 0x4ce8 でボス手前の位置を入れ直す
NextPos: jsr    $695c.l
        tst.b   MB_RUN.l
        beq.s   np_r
        cmpi.b  #2,MB_MODE.l
        bne.s   np_r
        jmp     $4ce8.l
np_r:   rts
; 装備コマンドの残り回数（無敵中は無制限 $ff として返す）
CmdCnt: tst.b   MB_INV.l
        beq.s   cc_n
        moveq   #-1,d1
        rts
cc_n:   move.b  $103f22.l,d1
        rts
"""

def apply(rom):
    import asm68
    # 組み立て順: B → C(PauseChk を参照) → A(IdleLock を参照)
    src_b = SRC_B
    if LOCK_SUSPEND:                                      # 解除/ロックは一時停止中: 本体はROMに入れない（ソースは残す）
        a_, b_ = src_b.index('Lock:   lea'), src_b.index('lk_act: clr.b   (a0)')
        b_ = src_b.index('rts', b_) + 3
        src_b = src_b[:a_] + 'Lock:   rts' + src_b[b_:]
    b2, lab2 = asm68.assemble(src_b, 0xd8f6, labels=None)
    assert len(b2) <= 532, len(b2)
    rom.put('main', 0xd8f6, b2, 'stubsB')
    rom.put('main', 0x154aa, bytes.fromhex('4eb9') + lab2['EvPtr'].to_bytes(4, 'big'), 'evptr', expect=bytes.fromhex('23ce00042e00'))
    import struct
    d313 = open('/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/work/main313.bin', 'rb').read()
    gw = []
    for i in range(16):                                   # ビギナーの枠の色(0x328c0)を灰色・やや暗く
        v = struct.unpack('>H', d313[0x328c0 + 2*i:0x328c2 + 2*i])[0]
        r, g, b_ = (v >> 10) & 31, (v >> 5) & 31, v & 31
        y = int((r * 0.3 + g * 0.59 + b_ * 0.11) * 1.4 + 3.5)
        gw.append(((y << 10) | (y << 5) | y) if (v and 2 <= i <= 6) else v)   # 2〜6 = ビギナーの枠の線の色だけ（8〜10 などはテクニカルの文字と共用）
    pt_, bt_ = progress_tables()
    bp = []
    for st in range(10):                                  # ボスラッシュ用: 面ごとのボス手前の進行度（boss_area_blob と同じ位置）
        if st == 9: bp.append(_prog(ST10[1][0]))
        elif st == 3 or not bt_[st]: bp.append(0)
        else: bp.append(_prog((bt_[st] << 8) - BRDELTA))
    src_inv = SRC_INV.replace('GREYDATA', 'dc.w    ' + ','.join('$%x' % x for x in gw)).replace('BOSSDATA', 'dc.w    ' + ','.join('$%x' % x for x in bp))
    src_inv = src_inv.replace('CUBESEEDBODY', ('        move.w  #$%x,$40032.l' % ((int(os.environ['CUBESLOT']) << 2) << 8)) if os.environ.get('CUBESLOT') else '        move.w  $103e30.l,$40032.l')
    bi, li = asm68.assemble(src_inv, INV_ADDR)
    assert INV_ADDR + len(bi) <= 0xd8f5, hex(len(bi))
    rom.img('main')[INV_ADDR:INV_ADDR + len(bi)] = bi
    rom.used.append(('main', INV_ADDR, INV_ADDR + len(bi), 'invincible'))
    b3, lab3 = asm68.assemble(SRC_C.replace('PENDB', '$%x' % lab2['PendB']).replace('CMDCNT', '$%x' % li['CmdCnt']).replace('BOSSSET', '$%x' % li['BossSet']).replace('PauseChk = $%x', 'PauseChk = $%x' % lab2['PauseChk']).replace('ApplyStage = $%x', 'ApplyStage = $%x' % lab2['ApplyStage']), 0x3fd9a)
    assert 0x3fd9a + len(b3) <= 0x3ffc0, hex(len(b3))
    rom.put('main', 0x3fd9a, b3, 'stubsC')
    rom.put('main', 0x4cfc, bytes.fromhex('4eb9') + lab3['AreaTbl'].to_bytes(4, 'big'), 'areatbl', expect=bytes.fromhex('4df9000054fe'))
    rom.put('main', 0x28ec + 2*4, lab3['StageHook'].to_bytes(4, 'big'), 'stagehook', expect=bytes.fromhex('00003790'))
    rom.put('main', 0x28ec + 5*4, lab3['PlayHook'].to_bytes(4, 'big'), 'playhook', expect=bytes.fromhex('00003a24'))
    srca = SRC_A.replace('PALCOPY', '$%x' % li['PalCopy']).replace('SCOREHK', '$%x' % li['ScoreHk']).replace('HUDPAL', '$%x' % lab2['HudPal']).replace('CUBESEED2', '$%x' % li['CubeSeed2']).replace('CUBESEEDBODY_UNUSED', ('        move.w  #$%x,$40032.l' % ((int(os.environ['CUBESLOT']) << 2) << 8)) if os.environ.get('CUBESLOT') else '''        move.w  $103e30.l,$40032.l''').replace('LOCKCALL', 'move.b  #1,MB_UNLK.l     ; 解除/ロックのコマンドは一時停止中: 常に解除' if LOCK_SUSPEND else 'jsr     Lock.l')
    b, lab = asm68.assemble(('Lock = $%x\n' % lab2['Lock']) + srca, 0xd4aa)
    assert len(b) <= 425, len(b)
    rom.put('main', 0xd4aa, b, 'stubsA')
    rom.put('main', 0x1d1e, bytes.fromhex('4eb9') + lab['StubIn'].to_bytes(4, 'big'), 'hook-in', expect=bytes.fromhex('4eb9000033b8'))
    rom.put('main', 0x1e82, bytes.fromhex('4eb9') + lab['HookStart'].to_bytes(4, 'big'), 'hook-start', expect=bytes.fromhex('4eb900002968'))
    rom.put('main', 0x26238, bytes.fromhex('4eb9') + lab['CubeSeed'].to_bytes(4, 'big'), 'cubeseed', expect=bytes.fromhex('1a3900040032'))
    rom.put('main', 0x1e44, lab['StateTbl'].to_bytes(4, 'big'), 'state-table-ptr', expect=bytes.fromhex('00001e58'))
    import mod_edit
    mod_edit.apply_main(rom, open('/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad/work/main313.bin', 'rb').read())
    print('edit L/R stub bytes', mod_edit.apply_lr(rom))
    # 無敵（改造プレイのみ・メニューの INVINCIBLE）: 自機が死亡に入る2か所の直前で、無敵なら当たりを消して通常の続きへ
    rom.put('main', 0x7bc4, bytes.fromhex('4eb9') + li['DieA'].to_bytes(4, 'big') + bytes.fromhex('4e71'), 'inv-a', expect=bytes.fromhex('13fc0001000400a2'))
    rom.put('main', 0xae22, bytes.fromhex('4eb9') + li['DieB'].to_bytes(4, 'big') + bytes.fromhex('4e71'), 'inv-b', expect=bytes.fromhex('13fc0001000400a2'))
    rom.put('main', 0x6b16, bytes.fromhex('4eb9') + li['TypeBeg'].to_bytes(4, 'big'), 'type-beg', expect=bytes.fromhex('0206000267' + '1a'))
    rom.put('main', 0x6a90, bytes.fromhex('4eb9') + li['TypeGrey'].to_bytes(4, 'big'), 'type-grey', expect=bytes.fromhex('4eb90000e824'))
    rom.put('main', 0x197e, bytes.fromhex('4eb9') + lab2['HiHk'].to_bytes(4, 'big'), 'hi-cube', expect=bytes.fromhex('beb900040058'))
    rom.put('main', 0x226c4, bytes.fromhex('4eb9') + lab2['RankHk'].to_bytes(4, 'big'), 'rank-cube', expect=bytes.fromhex('203900101054'))
    rom.put('main', 0x15b6, li['ScoreHk'].to_bytes(4, 'big'), 'score-tbl', expect=bytes.fromhex('0000180a'))
    rom.put('main', 0x1932, li['ScoreHk'].to_bytes(4, 'big'), 'score-1p', expect=bytes.fromhex('0000180a'))
    rom.put('main', 0x1954, li['ScoreHk'].to_bytes(4, 'big'), 'score-2p', expect=bytes.fromhex('0000180a'))
    rom.put('main', 0x1d24, bytes.fromhex('4eb9') + li['CredHook'].to_bytes(4, 'big'), 'credit-hide', expect=bytes.fromhex('4eb90000326e'))
    rom.put('main', 0x692a, bytes.fromhex('4eb9') + li['NextPos'].to_bytes(4, 'big'), 'bossrush-pos', expect=bytes.fromhex('4eb90000695c'))
    rom.put('main', 0x3c7a, bytes.fromhex('4eb9') + li['NextStg'].to_bytes(4, 'big'), 'bossrush-next', expect=bytes.fromhex('427900101052'))
    print('invincible stub bytes', len(bi))
    rom.free_main = [(0xd4aa + len(b), 0xd4aa + 425), (0xd8f6 + len(b2), 0xd8f6 + 532)]
    print('main free: A %d  B %d  C %d' % (425 - len(b), 532 - len(b2), 0x3ffc0 - 0x3fd9a - len(b3)))
    return lab, lab2
