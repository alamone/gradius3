"""メインCPU側の改造コードを、小さな空きの集まりに詰めて置く（#34）

- 置き場所は「ひと続きの空き」（ROM の C・共有RAM・メインRAM）と「隙間の列」（マスクの読まれない14バイトの隙間。
  命令を詰めて、隙間の終わりで bra.s で次の隙間へつなぐ）。
- コードは「かたまり」（chunk）に分けて書く。かたまりの間は jsr/jmp/lea の .l で呼ぶ（ラベルはかたまり全体で重ならないこと）。
- 大きい順に、入るなかで一番小さい「ひと続きの空き」へ。どこにも入らないものは隙間の列へ（データのかたまりは分けられないので不可）。
- 隙間の列で短い分岐が届かなくなったら、その分岐だけ .w にしてやり直す。
"""
import re, asm68

TERMINAL = re.compile(r'^(rts|rte|rtr|jmp|bra(\.[sw])?)\b', re.I)

def labels_in(src):
    return re.findall(r'^\s*([A-Za-z_][\w]*)\s*:', src, re.M)

def _lines(src):
    """ソース → [(ラベルたち, 命令)]（コメント・空行を除く。ラベルだけの行は次の命令に付ける）"""
    out, pend = [], []
    for ln in src.splitlines():
        s = ln.split(';')[0].strip()
        if not s: continue
        m = re.match(r'^([A-Za-z_][\w]*)\s*:\s*(.*)$', s)
        if m:
            pend.append(m.group(1)); s = m.group(2).strip()
            if not s: continue
        out.append((pend, s)); pend = []
    if pend: out.append((pend, ''))
    return out

def _text(L): return '\n'.join(''.join('%s:\n' % x for x in lb) + ins for lb, ins in L)

def _isize(ins, head, dummy):
    mn = ins.split()[0].lower()
    if re.match(r'^b(ra|sr|[a-z]{2})\.s$', mn) and mn not in ('bclr.s', 'bset.s', 'btst.s', 'bchg.s'): return 2
    if re.match(r'^b(ra|sr|[a-z]{2})\.w$', mn) and mn not in ('bclr.w', 'bset.w', 'btst.w', 'bchg.w'): return 4
    if re.match(r'^db', mn): return 4
    b, _ = asm68.assemble(head + ins, 0, dict(dummy))
    return len(b)

def layout(chunks, regions, stream, head='', ext=None, data=()):
    """chunks: [(名前, ソース, 置ける所の種類の集合)]  regions: [(名前, 始め, 終わり(含まない), 種類)]
    stream: [(名前, 始め, 終わり)]（隙間の列。種類は 'rom'）  data: 分けられないかたまりの名前
    戻り: (置き場所 {chunk名: [region名...]}, 組み立てた [(region名, org, bytes)], ラベル, 大きさ, 残り)"""
    ext = dict(ext or {})
    allnames = []
    for n, s, p in chunks: allnames += labels_in(s)
    dup = {k for k in allnames if allnames.count(k) > 1}
    assert not dup, 'ラベルが重なっている: %s' % dup
    dummy = {k: 0x12340 for k in allnames}
    dummy.update(ext)
    widen = set()                                         # .s → .w にした (かたまり名, 行番号)
    for attempt in range(60):
        src = {}
        for n, s, p in chunks:
            L = _lines(s)
            L = [(lb, re.sub(r'^(b\w+)\.s\b', r'\1.w', ins) if (n, i) in widen else ins) for i, (lb, ins) in enumerate(L)]
            src[n] = L
        size = {}
        for n, s, p in chunks:
            b, _ = asm68.assemble(head + _text(src[n]), 0, dict(dummy))
            size[n] = len(b) + (len(b) & 1)
        place, pieces = {}, []
        # 1) 隙間の列へ: 'stream' を含むかたまり（めったに通らない処理）を元の順で。入りきらないものは 2) へ回す
        si, off, cur = 0, 0, []
        overflow = []; pre = {}
        for n, s, p in chunks:
            if 'stream' not in p or n in data: continue
            save = (si, off, list(cur), len(pieces))
            ok = True; pl = []; mypre = {}
            for lb, ins in src[n]:
                sz = _isize(ins, head, dummy) if ins else 0
                while True:
                    if si >= len(stream): ok = False; break
                    room = stream[si][2] - stream[si][1] - off
                    need = sz + (0 if TERMINAL.match(ins or 'x') else 2)
                    if need <= room: break
                    if cur:
                        if not TERMINAL.match(cur[-1][1]): cur.append(([], 'bra.s   _S%d' % (si + 1)))
                        pieces.append((stream[si][0], stream[si][1], '_s%d' % si, cur))
                    cur = []; si += 1; off = 0
                if not ok: break
                if not cur: lb = ['_S%d' % si] + lb
                for k in lb: mypre[k] = stream[si][1] + off
                cur.append((lb, ins)); off += sz
                if stream[si][0] not in pl: pl.append(stream[si][0])
            if not ok:
                si, off, cur = save[0], save[1], save[2]; del pieces[save[3]:]
                overflow.append(n); continue
            assert TERMINAL.match(cur[-1][1]), 'かたまりの最後が rts/jmp/bra でない: %s' % n
            place[n] = pl; pre.update(mypre)
        if cur:
            pieces.append((stream[si][0], stream[si][1], '_s%d' % si, cur)); si += 1
        # 2) ひと続きの空きへ: 残り全部を大きい順に（データ・'rom' を先に）
        free = {r[0]: [r[1], r[2], r[3]] for r in regions}
        order = {r[0]: i for i, r in enumerate(regions)}
        rest = [c for c in chunks if c[0] not in place]
        for n, s, p in sorted(rest, key=lambda c: (c[0] not in data, c[2] != {'rom'} and c[2] != {'rom', 'stream'}, -size[c[0]])):
            best = None
            for rn, (lo, hi, kind) in free.items():
                if kind not in p or hi - lo < size[n]: continue
                key = (kind != 'rom', hi - lo, order[rn])
                if best is None or key < best[0]: best = (key, rn)
            assert best, '入らない: %s (%dB)。空き: %s' % (n, size[n], ', '.join('%s %d' % (k, v[1] - v[0]) for k, v in free.items()))
            rn = best[1]; place[n] = [rn]; pieces.append((rn, free[rn][0], n, src[n])); free[rn][0] += size[n]
        streamleft = sum(e - b for _, b, e in stream[si:]) + (stream[si - 1][2] - stream[si - 1][1] - off if si else 0)
        # 組み立て（2回: ラベルを集める → 本当の番地で）
        lab = dict(ext)
        known = dict(dummy); known.update({'_S%d' % i: stream[i][1] for i in range(len(stream))}); known.update(pre)
        lab.update(pre)
        instream = {n for n, s, p in chunks if n in place and place[n] and place[n][0] in {x[0] for x in stream}}
        try:
            for rn, org, n, L in pieces:
                if n.startswith('_s'): continue
                _, l = asm68.assemble(head + _text(L), org, dict(known))
                for lb, ins in L:
                    for k in lb: lab[k] = l[k]
            known.update(lab)
            out = []
            for rn, org, n, L in pieces:
                b, l = asm68.assemble(head + _text(L), org, dict(known))
                for lb, ins in L:
                    for k in lb: assert l[k] == lab[k], ('ラベルの番地が合わない', k, hex(l[k]), hex(lab[k]))
                out.append((rn, org, b + (b'\0' if len(b) & 1 else b'')))
        except asm68.AsmError as e:
            m = re.search(r'bcc\.s range .* at ([0-9a-f]+): (.*)$', str(e))
            if not m: raise
            ins = m.group(2).strip()
            hit = False
            for n, s, p in chunks:
                for i, (lb, x) in enumerate(src[n]):
                    if x == ins and (n, i) not in widen and n in instream: widen.add((n, i)); hit = True
            assert hit, str(e)
            continue
        left = {rn: v[1] - v[0] for rn, v in free.items()}
        left['stream'] = streamleft
        return place, out, lab, size, left
    raise AssertionError('分岐の .w への置き換えが終わらない')
