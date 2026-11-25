import sys,struct
from PIL import Image
def vram(state):
    b=open(state,'rb').read(); i=b.find(b'GPURAM')
    # mednafen: name(32 bytes padded?) then u32 size
    j=i+len(b'GPURAM')
    # find size field: scan forward up to 40 bytes for 0x100000
    for k in range(j,j+64):
        if struct.unpack_from('<I',b,k)[0]==0x100000: return b[k+4:k+4+0x100000]
    raise Exception('no')
def vram15(v,path):
    im=Image.new('RGB',(1024,512)); px=im.load()
    for y in range(512):
        for x in range(1024):
            p=v[(y*1024+x)*2]|v[(y*1024+x)*2+1]<<8
            px[x,y]=((p&31)<<3,((p>>5)&31)<<3,((p>>10)&31)<<3)
    im.save(path)
def vram4(v,path):
    im=Image.new('L',(4096,512)); px=im.load()
    for y in range(512):
        for x in range(2048):
            c=v[y*2048+x]; px[2*x,y]=(c&15)*17; px[2*x+1,y]=(c>>4)*17
    im.save(path)
if __name__=='__main__':
    v=vram(sys.argv[1]); open(sys.argv[2]+'.raw','wb').write(v)
    vram15(v,sys.argv[2]+'_15.png'); vram4(v,sys.argv[2]+'_4.png')
