import sys,os,struct,heapq,json;sys.path.insert(0,os.path.dirname(__file__))
from emu import Emu
e=Emu()
def pos(): return struct.unpack('<hh',e.read(0x8007ccac,4))
def area(): return e.read(0x800ee190,2)
start=sys.argv[1]; budget=int(sys.argv[2]); G=int(sys.argv[3]) if len(sys.argv)>3 else 30
e(cmd='load',path=os.path.abspath(start)); e.run(2)
p0=pos(); a0=area(); print('start',p0,a0.hex())
seen={}; k=0
def key(p): return (p[0]//G,p[1]//G)
AX=int(os.environ.get('AX','0')); SG=int(os.environ.get('SG','1'))
pq=[(-SG*p0[AX],0,start,p0)]; seen[key(p0)]=1; best=p0
while pq and k<budget:
    _,_,st,p=heapq.heappop(pq)
    for d in ['right','up','down','left']:
        e(cmd='load',path=os.path.abspath(st)); e.run(1)
        e(cmd='buttons',hold=[d]); e.run(90); e(cmd='buttons',hold=[]); e.run(2)
        q=pos(); a=area()
        if a!=a0 or abs(q[0]-p[0])>2000 or abs(q[1]-p[1])>2000:
            nm='saves/bfs/exit%d.state'%k; e(cmd='save',path=os.path.abspath(nm)); e.shot('shots/exit%d.png'%k)
            print('AREA CHANGE',p,q,a.hex(),nm); sys.stdout.flush(); continue
        if key(q) in seen: continue
        seen[key(q)]=1; k+=1
        nm='saves/bfs/n%d.state'%k; e(cmd='save',path=os.path.abspath(nm))
        heapq.heappush(pq,(-SG*q[AX],k,nm,q))
        if SG*q[AX]>SG*best[AX]: best=q; print(k,'best',q); sys.stdout.flush()
e.shot('shots/bfs_end.png'); print('done',k,best)
