"""Check every lui->lo address formation in GAME.BIN (following fall-through AND branches)
against the relocation map: original string address must map to the new one."""
import sys,os,struct,json
sys.path.insert(0,os.path.dirname(__file__))
from iso import Disc
from extract_text import GAME as O, GBASE, game_targets
B=Disc('../Lunatic Dawn III (Korean) (Track 1).bin')
fb={n:(l,sz) for n,l,sz,_,_ in B.walk()}
K=B.readfile(*fb['/GAME.BIN'])
mp={int(k,16):v for k,v in json.load(open('gamemap.json')).items()}
n=len(O)//4
WO=struct.unpack_from('<%dI'%n,O); WK=struct.unpack_from('<%dI'%n,K)
LO=(9,0xd,0x20,0x21,0x23,0x24,0x25,0x28,0x29,0x2b)
def wr(x):
    op=x>>26
    if op==0:
        f=x&63
        if f in(8,0x18,0x19,0x1a,0x1b,0x11,0x13): return None
        return (x>>11)&31
    if op in(8,9,0xa,0xb,0xc,0xd,0xe,0xf,0x20,0x21,0x22,0x23,0x24,0x25,0x26): return (x>>16)&31
    if op==3: return 31
def target(i,x):
    op=x>>26
    if op in(4,5,6,7) or op==1:
        off=x&0xffff; off=off-0x10000 if off&0x8000 else off; return i+1+off
    if op==2: return (x&0x3ffffff)-((GBASE&0x0fffffff)>>2)
    return None
def addr(hw,lw):
    imm=lw&0xffff
    return ((hw&0xffff)<<16)+(imm if lw>>26==0xd else (imm-0x10000 if imm&0x8000 else imm))&0xffffffff
bad=0;checked=0
def walk(hi_i,r,start,depth,seen):
    global bad,checked
    k=start
    while k<n and k<start+40:
        if (k,depth) in seen: return
        seen.add((k,depth))
        y=WO[k]
        if (y>>26) in LO and ((y>>21)&31)==r:
            a0=addr(WO[hi_i],y); p=a0-GBASE
            if p in mp:
                checked+=1
                a1=addr(WK[hi_i],WK[k])
                if a1!=GBASE+mp[p]:
                    bad+=1; print('BAD hi@%x lo@%x orig->%x new->%x want %x'%(GBASE+hi_i*4,GBASE+k*4,a0,a1,GBASE+mp[p]))
            if (y>>26) in(0x28,0x29,0x2b): pass
        t=target(k,y)
        if t is not None and depth<2 and 0<=t<n:
            # delay slot executes first
            ds=WO[k+1]
            if wr(ds)!=r: walk(hi_i,r,t,depth+1,seen)
            if (y>>26)==2: return  # unconditional j
        if (y>>26)==0 and (y&63)==8: return  # jr
        if wr(y)==r and k!=hi_i: return
        k+=1
for i,x in enumerate(WO):
    if x>>26==0xf and (x&0xffff) in (0x8017,0x8018,0x8019):
        walk(i,(x>>16)&31,i+1,0,set())
print('checked',checked,'bad',bad)
