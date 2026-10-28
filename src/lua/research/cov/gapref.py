import struct,sys
m=open(sys.argv[1] if len(sys.argv)>1 else 'main313.bin','rb').read()
c=open(sys.argv[2],'rb').read()
# refs: abs long/word + pc-rel branches/lea/pea
refs={}
def add(t,src,k): refs.setdefault(t,[]).append((src,k))
for a in range(0,len(m)-3,2):
    v=struct.unpack('>I',m[a:a+4])[0]
    if 0x400<=v<0x40000: add(v,a,'L')
    w=struct.unpack('>H',m[a:a+2])[0]
    if (w&0xf000)==0x6000:
        d=w&0xff
        if d==0: d=struct.unpack('>h',m[a+2:a+4])[0]
        elif d==0xff: d=None
        else: d=d-256 if d&0x80 else d
        if d is not None: add(a+2+d,a,'B')
    if (w&0xf0f8)==0x50c8: add(a+2+struct.unpack('>h',m[a+2:a+4])[0],a,'D')
    if (w&0xf1ff)==0x41fa or w==0x487a or w in (0x4efa,0x4eba): add(a+2+struct.unpack('>h',m[a+2:a+4])[0],a,'P')
    if (w&0xf1ff)==0x41f8 or w in (0x4eb8,0x4ef8,0x4878):
        t=struct.unpack('>H',m[a+2:a+4])[0]; add(t,a,'W')
gaps=[];i=0
while i<0x20000:
    if not c[i]:
        j=i
        while j<0x20000 and not c[j]: j+=1
        gaps.append((i*2,j*2)); i=j
    else: i+=1
MIN=int(sys.argv[3]) if len(sys.argv)>3 else 200
for s,e in sorted(gaps,key=lambda g:g[0]-g[1]):
    if e-s<MIN: continue
    inc=[(t,src,k) for t in range(s,e) for (src,k) in refs.get(t,[]) if not (s<=src<e)]
    inc_cov=[x for x in inc if c[x[1]//2]]
    print('%06x-%06x %5d  in=%d (from covered=%d) prev=%s'%(s,e,e-s,len(inc),len(inc_cov),m[s-2:s].hex()))
    for t,src,k in inc[:6]: print('     -> %06x from %06x %s %s'%(t,src,k,'COV' if c[src//2] else ''))
