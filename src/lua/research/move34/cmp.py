import glob,os,sys
A,B=sys.argv[1],sys.argv[2]
ex=[(0x40500,0x405e0),(0x42e78,0x43000),(0x43f70,0x44000),(0x103812,0x1038d4),(0x103966,0x1039c0),(0x1039c6,0x103ac0),(0x40400,0x40500),(0x403c0,0x40400)]
def addr(i): return 0x40000+i if i<0x4000 else 0x100000+i-0x4000
tot=0
for f in sorted(glob.glob(A+'/*.bin')):
    n=os.path.basename(f); g=os.path.join(B,n)
    if not os.path.exists(g): print('missing',n); continue
    a=open(f,'rb').read(); b=open(g,'rb').read()
    if 'gfx' in n or 'pal' in n:
        d=sum(1 for x,y in zip(a,b) if x!=y); 
        if d: print(n,'diff bytes',d); tot+=1
        continue
    diffs=[addr(i) for i,(x,y) in enumerate(zip(a,b)) if x!=y and not any(lo<=addr(i)<hi for lo,hi in ex)]
    if diffs: print(n,len(diffs),' '.join('%x'%x for x in diffs[:12])); tot+=1
print('files with diffs',tot)
