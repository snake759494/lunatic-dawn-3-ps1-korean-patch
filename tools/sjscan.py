import sys,os,re
def runs(b,minc=3):
    out=[];i=0;n=len(b)
    while i<n-1:
        j=i;c=0
        while j<n-1 and (0x81<=b[j]<=0x9f or 0xe0<=b[j]<=0xef) and (0x40<=b[j+1]<=0xfc and b[j+1]!=0x7f):
            j+=2;c+=1
        if c>=minc: out.append((i,b[i:j].decode('cp932','replace'))); i=j
        else: i+=1
    return out
for root,_,fs in os.walk('ext'):
    for f in fs:
        p=os.path.join(root,f); r=runs(open(p,'rb').read())
        if r: print(f'{p:30s} {len(r):6d} {sum(len(x[1]) for x in r):7d}  {r[0][1][:20]}')
