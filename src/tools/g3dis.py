import sys,os
S='/tmp/claude-0/-home-claude/57f28419-36f2-5d63-9dbe-6a3976a5a75b/scratchpad'
sys.path.insert(0,S+'/build/cs/bindings/python'); os.environ['LIBCAPSTONE_PATH']=S+'/build/cs/b'
import capstone
md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_M68K_000)
def load(d=S+'/out_t62'):
    f=open(d+'/945_313.f15','rb').read(); e=open(d+'/945_312.e15','rb').read()
    return bytes(x for p in zip(f,e) for x in p)
def dis(m,a,n):
    end=a+n
    while a<end:
        i=next(md.disasm(m[a:a+12],a,1),None)
        if not i: print(hex(a),'dc.w',m[a:a+2].hex()); a+=2; continue
        print('%6x  %-8s %s'%(i.address,i.mnemonic,i.op_str)); a+=i.size
if __name__=='__main__':
    m=load(); 
    for x in sys.argv[1:]:
        a,n=x.split(':'); print('---'); dis(m,int(a,16),int(n,16))
