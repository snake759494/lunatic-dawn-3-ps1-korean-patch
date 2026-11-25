import sys,os,json,struct,re
sys.path.insert(0,os.path.dirname(__file__))
from iso import Disc
import build
from ld3 import encode
cm={k:int(v,16) for k,v in json.load(open('cmap.json',encoding='utf-8')).items()}
enc=build.Enc(cm)
ko=build.load_tr()
d=Disc(build.OUT_BIN); idx={n:(l,s) for n,l,s,_,_ in d.walk()}
F=lambda n: d.readfile(*idx[n])
game=F('/GAME.BIN'); msg=F('/MSG/MSG.DAT'); bad=0; n=0
def cs(b,o): return b[o:b.index(0,o)]
for k,hdr,offs,txt in build.msg_blocks():
    off,sz=struct.unpack_from('<2I',game,build.MSGTAB+8*k)
    blk=msg[off:off+sz]; tot,pb,tl=struct.unpack_from('<3I',blk,0)
    assert tot==sz and blk[:12+20]==blk[:12+20]
    ps=tot-tl-pb; no=struct.unpack_from('<%dH'%(pb//2),blk,ps); t=blk[ps+pb:]
    first={}
    for i,o in enumerate(offs): first.setdefault(o,i)
    for i,o in enumerate(offs):
        exp=enc(ko['msg/%d/%d'%(k,first[o])]); got=cs(t,no[i]); n+=1
        if exp!=got: bad+=1; print('MSG mismatch',k,i)
for name,pre,tab,cnt in [('/ADVMSG.BIN','adv',0x8024,743),('/DATMODL.BIN','names',0x420c,1318)]:
    nb=F(name); ob=open('ext'+name,'rb').read()
    for i in range(cnt):
        p=struct.unpack_from('<I',ob,tab+4*i)[0]-0x801f19a0
        if not(4<=p<tab): continue
        first=[j for j in range(cnt) if struct.unpack_from('<I',ob,tab+4*j)[0]-0x801f19a0==p][0]
        q=struct.unpack_from('<I',nb,tab+4*i)[0]-0x801f19a0
        exp=enc(ko['%s/%d'%(pre,first)]); got=cs(nb,q); n+=1
        if exp!=got: bad+=1; print('PTR mismatch',name,i)
from extract_text import game_targets
for p,(t,refs) in game_targets().items():
    exp=enc(ko['game/%x'%p])
    for r in refs:
        if r[0]=='w': a=struct.unpack_from('<I',game,r[1])[0]
        else:
            hi=struct.unpack_from('<I',game,r[1])[0]&0xffff; w=struct.unpack_from('<I',game,r[2])[0]; lo=w&0xffff
            a=(hi<<16)+(lo if (w>>26)==0xd else (lo-0x10000 if lo&0x8000 else lo))
        got=cs(game,a-build.GBASE); n+=1
        if got!=exp: bad+=1; print('GAME mismatch',hex(p),r)
print('checked',n,'mismatches',bad)
