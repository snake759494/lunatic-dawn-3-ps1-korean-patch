import sys,os
sys.path.insert(0,os.path.dirname(__file__))
from iso import Disc
d=Disc(r'../Lunatic Dawn III (Japan) (Track 1).bin')
for n,l,sz,_,_ in d.walk():
    if n.startswith('/MOVIE/') or n=='/DUMMY.DA' or l==0: continue
    p='ext'+n; os.makedirs(os.path.dirname(p),exist_ok=True)
    open(p,'wb').write(d.readfile(l,sz))
