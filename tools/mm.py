import sys,os,subprocess
from PIL import Image
# run steps then save full shot + zoomed minimap side by side to shots/mm.png
subprocess.check_call([sys.executable,os.path.join(os.path.dirname(__file__),'play.py'),sys.argv[1]+',shot:mm0'])
im=Image.open('shots/mm0.png').convert('RGB'); w,h=im.size
m=im.crop((240,160,315,200)).resize((350,187),Image.NEAREST)
o=Image.new('RGB',(w+350,max(h,187))); o.paste(im,(0,0)); o.paste(m,(w,0)); o.save('shots/mm.png')
