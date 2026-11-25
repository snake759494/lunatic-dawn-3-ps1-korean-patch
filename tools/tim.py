import struct,sys
from PIL import Image
def parse(d,o=0):
    magic,flag=struct.unpack_from('<II',d,o)
    assert magic==0x10, hex(magic)
    bpp=flag&3; p=o+8; clut=None
    if flag&8:
        ln,cx,cy,cw,ch=struct.unpack_from('<IHHHH',d,p); clut=(cx,cy,cw,ch,d[p+12:p+ln]); p+=ln
    ln,ix,iy,iw,ih=struct.unpack_from('<IHHHH',d,p)
    return dict(bpp=bpp,clut=clut,x=ix,y=iy,w=iw,h=ih,pix=d[p+12:p+ln],end=p+ln,pixoff=p+12)
def c15(v): return ((v&31)<<3,((v>>5)&31)<<3,((v>>10)&31)<<3,0 if v==0 else 255)
def toimg(t,palno=0):
    w=t['w']*{0:4,1:2,2:1}[t['bpp']]; h=t['h']; im=Image.new('RGBA',(w,h)); px=im.load()
    pal=None
    if t['clut']:
        cx,cy,cw,ch,cd=t['clut']; n=cw
        pal=[c15(x) for x in struct.unpack_from('<%dH'%n,cd,palno*n*2)]
    for y in range(h):
        for x in range(w):
            if t['bpp']==0: v=(t['pix'][y*t['w']*2+x//2]>>(4*(x&1)))&15; px[x,y]=pal[v]
            elif t['bpp']==1: px[x,y]=pal[t['pix'][y*t['w']*2+x]]
            else: px[x,y]=c15(struct.unpack_from('<H',t['pix'],(y*w+x)*2)[0])
    return im
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read(); t=parse(d); print({k:v for k,v in t.items() if k not in('pix','clut')}, t['clut'][:4] if t['clut'] else None)
    toimg(t).save(sys.argv[2])
