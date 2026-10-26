"""メニューの背景: 3面ボス(ビッグコアMkIII)が反射レーザーを撃っている瞬間（奥の岩の背景はなし・暗く）
ボス・反射レーザー・自機はすべてスプライト(57個)。スプライト表 1KB と色 0.5KB だけを持つ。
MAME で記録したその瞬間の A面(ボス)・スプライト(レーザー・自機)・色から、メニュー表示用のデータを作る。
"""
import os, struct
D = os.path.join(os.path.dirname(__file__), 'menubg')
F = 7440
DIM = 0.40
COLSHIFT = 10
SHD_X, SHD_Y = int(os.environ.get('SHDX', '293')), int(os.environ.get('SHDY', '185'))
SHIP, SHIP_OX, SHIP_OY = 71, int(os.environ.get('SHIPX', '184')), int(os.environ.get('SHIPY', '148'))   # 自機のスプライト番号と位置（スプライト座標）          # 記録時の A面スクロール(0x160) → メニュー中(0x1b0) の差 = 80ドット = 10タイル

def _load():
    """pal・spr はリポジトリにある（メニュー背景に使うのはこの2つだけ）。
    vram・chr（A面の岩の背景）は今は使っていないので、無ければ読まない（ROM 由来なのでリポジトリには入れない）"""
    def opt(name):
        f = os.path.join(D, '%s_%d.bin' % (name, F))
        return open(f, 'rb').read() if os.path.exists(f) else None
    v = opt('vram'); K = bytes(v[2*i+1] for i in range(0x4000)) if v else None
    chr_ = opt('chr')
    pal = open(os.path.join(D, 'pal_%d.bin' % F), 'rb').read()
    s = open(os.path.join(D, 'spr_%d.bin' % F), 'rb').read(); spr = bytes(s[i] for i in range(1, len(s), 2))
    return K, chr_, pal, spr

def blobs():
    K, chr_, pal, spr = _load()
    blank = 16
    cells = []; codes = set()
    for r in (range(32) if K is not None and chr_ is not None else ()):
        for c in range(64):
            i = r * 64 + c
            a = K[0x800 + i]; lo = K[0x2800 + i]
            code = lo | ((a & 1) << 8) | ((a & 0x1c) << 7)
            if code == blank: continue
            codes.add(code)
            cells.append((r * 64 + (c + COLSHIFT) % 64, a, lo))
    tiles = b''.join(struct.pack('>H', c) + chr_[c*32:c*32+32] for c in sorted(codes))
    cellb = b''.join(struct.pack('>HBB', i, a, lo) for i, a, lo in cells)
    p = bytearray()
    for o in range(0x200, 0x400, 2):          # スプライトの色（パレット16〜31）
        w = struct.unpack('>H', pal[o:o+2])[0]
        r, g, b = (w >> 10) & 31, (w >> 5) & 31, w & 31
        r, g, b = int(r * DIM + .5), int(g * DIM + .5), int(b * DIM + .5)
        p += struct.pack('>H', (w & 0x8000) | (r << 10) | (g << 5) | b)
    sp = bytearray(1024)
    for i in range(0, 1024, 8):
        if spr[i] & 0x80: sp[i:i+8] = spr[i:i+8]
    # 自機（表の71番）を移す: CUBE HEIGHT の上の空き行、先端が EX STAGE の行の A のあたり
    o = SHIP * 8
    sp[o+4] = (sp[o+4] & 0xfe) | (((256 - SHIP_OY) & 0x1ff) >> 8); sp[o+5] = (256 - SHIP_OY) & 0xff
    sp[o+6] = (sp[o+6] & 0xfe) | ((SHIP_OX & 0x1ff) >> 8); sp[o+7] = SHIP_OX & 0xff
    # シールド色の見本: フリーシールド（丸い玉1つ・16x16・コード 0x3a・色3。ゲーム中に記録）を SHD COLOR の右に置く。色はメニューで選んだ色を暗くせずに入れる
    x, y = SHD_X, SHD_Y
    sp[0:8] = bytes([0x80 | 0x39, 0x00, 0x3a, 0x06, ((256 - y) & 0x1ff) >> 8, (256 - y) & 0xff, (x & 0x1ff) >> 8, x & 0xff])
    return {'MBGPAL': (0, bytes(p)), 'MBGSPR': (0, bytes(sp))}   # ボス本体・レーザー・自機はすべてスプライト（A面は奥の岩なので使わない）

if __name__ == '__main__':
    b = blobs()
    for k, (n, d) in b.items(): print(k, n, len(d))
    print('total', sum(len(d) for n, d in b.values()))
