import sys,glob
M=sys.argv[1]; fs=sys.argv[2:]
cov=bytearray(0x20000)
for f in fs:
    d=open(f,'rb').read()
    for i,b in enumerate(d):
        if b: cov[i]=1
m=open(M,'rb').read()
print('touched',sum(cov)*2)
gaps=[];i=0
while i<0x20000:
    if not cov[i]:
        j=i
        while j<0x20000 and not cov[j]: j+=1
        gaps.append((i*2,(j-i)*2)); i=j
    else: i+=1
gaps.sort(key=lambda g:-g[1])
tot=sum(g[1] for g in gaps if g[1]>=256)
print('gaps>=256 total',tot)
for a,n in gaps[:60]: print('%06x-%06x %6d  %s'%(a,a+n,n,m[a:a+16].hex()))
