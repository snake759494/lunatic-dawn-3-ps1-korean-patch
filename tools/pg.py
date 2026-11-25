import sys,os,subprocess
from PIL import Image
# like play.py, but shots named automatically g0..; combined into shots/grid.png
steps=sys.argv[1].split(','); k=0; out=[]
for s in steps:
    if s.strip()=='S': out.append('shot:g%d'%k); k+=1
    else: out.append(s)
subprocess.check_call([sys.executable,os.path.join(os.path.dirname(__file__),'play.py'),','.join(out)])
ims=[Image.open('shots/g%d.png'%i) for i in range(k)]
w,h=ims[0].size; c=2 if k>1 else 1; r=(k+c-1)//c; o=Image.new('RGB',(w*c,h*r))
for i,im in enumerate(ims): o.paste(im,((i%c)*w,(i//c)*h))
o.save('shots/grid.png')
