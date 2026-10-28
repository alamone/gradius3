"""メインCPU側の改造コードを、小さな空きの集まりに詰めて置く（#34）

- 置き場所（REGIONS）は ROM の空き（C・マスクの読まれない隙間）と、共有RAMの空き（起動時にサブが書き込む）。
- コードは「かたまり」（chunk = 1つ以上の処理。中の分岐はかたまりの中だけ）に分けて書く。かたまりの間は jsr/jmp/lea の .l で呼ぶ。
- 1回目：仮の番地で組み立てて大きさを測る → 大きい順に、入るなかで一番小さい空きへ（ROM 優先）→ 2回目：本当の番地で組み立て。
"""
import re, asm68

def labels_in(src):
    return re.findall(r'^\s*([A-Za-z_][\w]*)\s*:', src, re.M)

def layout(chunks, regions, head='', ext=None):
    """chunks: [(名前, ソース, 'rom'|'any')]  regions: [(名前, 始め, 終わり(含まない), 'rom'|'ram')]
    戻り: (置き場所 {chunk名: (region名, org)}, 組み立てた [(region名, org, bytes)], ラベル)"""
    ext = dict(ext or {})
    allnames = set()
    for n, s, p in chunks: allnames.update(labels_in(s))
    dummy = {k: 0x12340 for k in allnames}
    dummy.update(ext)
    size = {}
    for n, s, p in chunks:
        b, _ = asm68.assemble(head + s, 0, dict(dummy))
        size[n] = len(b) + (len(b) & 1)
    free = {r[0]: [r[1], r[2], r[3]] for r in regions}   # 名前 → [次の空き, 終わり, 種類]
    order = {r[0]: i for i, r in enumerate(regions)}
    place = {}
    for n, s, p in sorted(chunks, key=lambda c: (c[2] != 'rom', -size[c[0]])):
        best = None
        for rn, (lo, hi, kind) in free.items():
            if p == 'rom' and kind != 'rom': continue
            if hi - lo < size[n]: continue
            key = (kind != 'rom', hi - lo, order[rn])    # ROM を先に、残りが一番少なくなる所
            if best is None or key < best[0]: best = (key, rn)
        if best is None:
            left = sorted(((hi - lo), rn) for rn, (lo, hi, k) in free.items())
            raise AssertionError('入らない: %s (%dB)。空き: %s' % (n, size[n], ', '.join('%s %d' % (r, v) for v, r in left if v)))
        rn = best[1]; place[n] = (rn, free[rn][0]); free[rn][0] += size[n]
    lab = dict(ext)
    # 2回目の前に、全部のかたまりのラベルの本当の番地を集める（大きさは変わらない）
    for n, s, p in chunks:
        _, l = asm68.assemble(head + s, place[n][1], dict(dummy))
        for k in labels_in(s): lab[k] = l[k]
    out = []
    for n, s, p in chunks:
        b, l = asm68.assemble(head + s, place[n][1], dict(lab))
        assert len(b) + (len(b) & 1) == size[n], (n, len(b), size[n])
        out.append((place[n][0], place[n][1], b + (b'\0' if len(b) & 1 else b'')))
    left = {rn: v[1] - v[0] for rn, v in free.items()}
    return place, out, lab, size, left
