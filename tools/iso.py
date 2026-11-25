"""MODE2/2352 BIN ISO9660 reader."""
import struct, sys
SEC=2352
class Disc:
    def __init__(s,path,mode='rb'):
        s.f=open(path,mode)
    def read(s,lba,n=1):
        out=bytearray()
        for i in range(n):
            s.f.seek((lba+i)*SEC+24); out+=s.f.read(2048)
        return bytes(out)
    def readfile(s,lba,size):
        return s.read(lba,(size+2047)//2048)[:size]
    def walk(s):
        pvd=s.read(16)
        rlba,rsz=struct.unpack_from('<I',pvd,156+2)[0],struct.unpack_from('<I',pvd,156+10)[0]
        res=[]
        def rec(lba,size,path):
            data=s.read(lba,(size+2047)//2048); p=0
            while p<len(data):
                l=data[p]
                if l==0: p=(p//2048+1)*2048; continue
                elba=struct.unpack_from('<I',data,p+2)[0]; esz=struct.unpack_from('<I',data,p+10)[0]
                fl=data[p+25]; nl=data[p+32]; name=data[p+33:p+33+nl]
                if name not in (b'\0',b'\1'):
                    nm=name.decode('ascii','replace').split(';')[0]
                    if fl&2: rec(elba,esz,path+nm+'/')
                    else: res.append((path+nm,elba,esz,lba,p))
                p+=l
        rec(rlba,rsz,'/')
        return res
if __name__=='__main__':
    d=Disc(sys.argv[1])
    for n,l,sz,dl,dp in d.walk(): print(f'{l:7d} {sz:10d} {n}')
