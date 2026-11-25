"""Find Japanese SJIS strings in original files that are byte-identical in the Korean disc."""
import sys,os,re
sys.path.insert(0,os.path.dirname(__file__))
from iso import Disc
from sjscan import runs
A=Disc(r'../Lunatic Dawn III (Japan) (Track 1).bin'); B=Disc(r'../Lunatic Dawn III (Korean) (Track 1).bin')
fb={n:(l,sz) for n,l,sz,_,_ in B.walk()}
KANA=re.compile('[ぁ-ヿ]')
for n,l,sz,_,_ in A.walk():
    if n.startswith('/MOVIE/') or n=='/DUMMY.DA' or l==0: continue
    a=A.readfile(l,sz); b=B.readfile(*fb[n])
    for o,s in runs(a,2):
        L=len(s)*2
        if a[o:o+L]==b[o:o+L] and (KANA.search(s) or len(s)>=2):
            print(n,hex(o),s)
