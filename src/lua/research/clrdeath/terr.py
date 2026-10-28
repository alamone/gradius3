# 純正の地形の当たり判定（メイン $83b0）をダンプから再現して、画面のどこが「当たる」かをフレームごとに数える
import sys, struct
D = sys.argv[1]
def load(k, f): return open(f'{D}/{k}_{f}.bin', 'rb').read()
def hits(f, xs, ys):
    vram, chr_, shr = load('vram', f), load('chr', f), load('shr', f)
    L = lambda a: struct.unpack('>I', shr[a-0x100000:a-0x100000+4])[0]
    B = lambda a: shr[a-0x100000]
    scr, f4, mp = L(0x1038de), L(0x1038f4), B(0x1039c0); scy = L(0x1038e2)
    out = set()
    for oy in ys:
        for ox in xs:
            x = (scr + ox) & 0xffffffff; y = (scy + oy) & 0xffffffff
            d5 = (y - f4) & 0xffffffff
            d7 = (y >> 4) & 0xffff
            d5w = (0xff0 - d7) & 0xffff
            d7w = d5w & 0xf80
            d6 = (x >> 8) & 0x1fe; d4 = d6
            idx = (((d6 & 0x1f8) >> 2) + d7w) & 0xffff
            if d5 & 0x10000:
                attr = B(0x100000 + idx); code = B(0x100000 + idx + 1)
            else:
                attr = vram[0x2001 + idx]; code = vram[0x6001 + idx]
            t = attr & 0xe0
            if t == 0x80: continue
            if t == 0xa0: out.add((ox, oy, 'A')); continue
            tile = (code | ((attr & 1) << 8) | (((attr >> 2) & 7) << 9)) & 0xfff
            off = ((d5w & 0x70) >> 2) + ((d4 & 4) >> 1)
            a = tile * 32 + off
            if mp == 0x0d: continue
            w = (chr_[a] << 8) | chr_[a+1]
            ok = True
            for k in range(4):
                n = (w >> (4*k)) & 0xf
                if n == 0 or n >= 0xe: ok = False; break
            if ok and (w & 0xff) < 0xee: out.add((ox, oy, 'P'))
    return out, scr
xs = range(0x1000, 0x11001, 0x200); ys = range(0x2000, 0xe001, 0x100)
f0, f1 = int(sys.argv[2]), int(sys.argv[3])
prev = None
for f in range(f0, f1 + 1):
    h, scr = hits(f, xs, ys)
    new = h - prev if prev is not None else set()
    print(f, 'scr=%x' % scr, 'hits', len(h), 'new', len(new), sorted(new)[:6])
    prev = h
