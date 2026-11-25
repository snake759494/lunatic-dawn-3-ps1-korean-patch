import sys,os,struct,collections;sys.path.insert(0,os.path.dirname(__file__))
from emu import Emu
from PIL import Image
e=Emu()
def pos(): return struct.unpack('<hh',e.read(0x8007ccac,4))
start=sys.argv[1]; budget=int(sys.argv[2]); G=40
e(cmd='load',path=os.path.abspath(start)); e.run(2)
q=collections.deque([(start,pos())]); seen={(pos()[0]//G,pos()[1]//G)}; k=0
def texty(p):
    im=Image.open(p).convert('RGB'); px=im.load(); w,h=im.size
    return sum(1 for x in range(0,w,2) for y in range(30,h-50,2) if sum(px[x,y])>700)
HP0=None
while q and k<budget:
    st,p=q.popleft()
    for d in ['up','down','left','right']:
        e(cmd='load',path=os.path.abspath(st)); e.run(1)
        e(cmd='buttons',hold=[d]); e.run(150); e(cmd='buttons',hold=[]); e.run(2)
        r=pos(); k+=1
        sp='shots/ex/%d.png'%k; e.shot(sp); t=texty(sp)
        im=Image.open(sp).convert('RGB');px=im.load();hp=sum(1 for x in range(30,120) if px[x,202][1]>120 and px[x,202][0]<120)
        HP0=hp if HP0 is None else HP0
        if hp<HP0-4: print('HP',k,hp,r); sys.stdout.flush(); e(cmd='save',path=os.path.abspath('saves/hit%d.state'%k)); continue
        if t>40: print('TEXT',k,t,r); sys.stdout.flush()
        elif k%8: os.remove(sp)
        kk=(r[0]//G,r[1]//G)
        if kk in seen: continue
        seen.add(kk); nm='saves/bfs/x%d.state'%k; e(cmd='save',path=os.path.abspath(nm)); q.append((nm,r))
print('done',k,len(seen))
