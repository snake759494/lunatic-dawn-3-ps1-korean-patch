import sys,os,random;sys.path.insert(0,os.path.dirname(__file__))
from emu import Emu
from PIL import Image
e=Emu()
def icon():
    e.shot('shots/w.png'); im=Image.open('shots/w.png').convert('RGB'); px=im.load()
    pts=[(x,y) for x in range(240,315) for y in range(160,200) if sum(px[x,y])>720]
    red=[(x,y) for x in range(240,315) for y in range(160,200) if px[x,y][0]>180 and px[x,y][1]<90 and px[x,y][2]<90]
    if not pts or not red: return None
    c=lambda P:(sum(p[0] for p in P)/len(P), sum(p[1] for p in P)/len(P))
    a=c(pts); b=c(red); return (a[0]-b[0],a[1]-b[1])
# goal: maximize score = dx*gx+dy*gy
gx,gy=float(sys.argv[1]),float(sys.argv[2]); steps=int(sys.argv[3])
dirs=['up','down','left','right']
p=icon(); print('start',p)
for s in range(steps):
    best=None
    for d in random.sample(dirs,4):
        e(cmd='save',path=os.path.abspath('saves/_w.state'))
        e(cmd='buttons',hold=[d]); e.run(200); e(cmd='buttons',hold=[])
        q=icon()
        D=lambda r:((r[0]-gx)**2+(r[1]-gy)**2)**.5
        sc=-1e9 if (q is None or p is None) else D(p)-D(q)
        if best is None or sc>best[0]: best=(sc,d,q)
        e(cmd='load',path=os.path.abspath('saves/_w.state'))
    sc,d,q=best
    if sc<=0.1:
        d=random.choice(dirs)
    e(cmd='buttons',hold=[d]); e.run(200); e(cmd='buttons',hold=[]); p=icon()
    print(s,d,round(sc,2),p)
