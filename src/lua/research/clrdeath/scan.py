import sys
exec(open('terr.py').read().split('xs = range')[0].replace("D = sys.argv[1]","D = None"))
xs = range(0x1000, 0x11001, 0x400); ys = range(0x2000, 0xe001, 0x200)
def run(d, tc):
    global D; D = d
    prev = None
    for f in range(tc-3, tc+41):
        try: h, scr = hits(f, xs, ys)
        except FileNotFoundError: continue
        S = set((p[0], p[1]) for p in h)
        if prev is not None and S != prev:
            new = S - prev
            X = sorted(set(p[0] for p in new)); Y = sorted(set(p[1] for p in new))
            print(' ', f, 't=%+d' % (f - tc), 'hits', len(S), 'new', len(new), ('x %x-%x y %x-%x' % (X[0], X[-1], Y[0], Y[-1])) if new else '', 'gone', len(prev - S))
        prev = S
for d, tc in [(a.split(':')[0], int(a.split(':')[1])) for a in sys.argv[1:]]:
    print(d, tc); run(d, tc)
