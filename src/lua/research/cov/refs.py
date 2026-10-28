# メインROM内の「番地らしい値」(32bit の 0x400〜0x3ffff 偶数, jsr/jmp/lea .w) の一覧 → refs.txt
import struct,sys
m=open(sys.argv[1],'rb').read()
out=open(sys.argv[2],'w')
for a in range(0,len(m)-3,2):
    v=struct.unpack('>I',m[a:a+4])[0]
    if 0x400<=v<0x40000: out.write('%06x L %06x\n'%(a,v))
    w=struct.unpack('>H',m[a:a+2])[0]
    if w in (0x4eb8,0x4ef8) or (w&0xf1ff)==0x41f8:
        t=struct.unpack('>H',m[a+2:a+4])[0]
        if t<0x8000: out.write('%06x W %06x\n'%(a,t))
    if w in (0x6100,0x6000) or (w&0xff00) in (0x6100,0x6000) :
        pass
out.close()
