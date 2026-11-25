import json,glob,re,sys
from collections import Counter
TOK=re.compile(r'\{[A-Z]\d\}|<[PW]>|<[A-Za-z]\d>|\{[0-9a-f]{2}\}|\[a-z0-9]|%-?\d*[ds]')
def w(line):
    line=TOK.sub('',line)
    return sum(1 if (ord(c)>=0x80 or c==' ') else 0.5 for c in line)
L=float(sys.argv[1]) if len(sys.argv)>1 else 16
cj=Counter();ck=Counter();ex=[]
for p in sorted(glob.glob('tr/*_in.json')):
    if 'rare' in p: continue
    a=json.load(open(p,encoding='utf-8')); b=json.load(open(p.replace('_in','_ko'),encoding='utf-8'))
    for x in a:
        k=x['id']; 
        if k not in b: continue
        pre=k.split('/')[0]
        mj=max(w(l) for l in re.split(r'\n|<P>',x['jp'])); mk=max(w(l) for l in re.split(r'\n|<P>',b[k]))
        if mj>L: cj[pre]+=1
        if mk>L: ck[pre]+=1; ex.append((k,mj,mk,b[k]))
print('jp over',dict(cj)); print('ko over',dict(ck))
for e in ex[:40]: print(e)
