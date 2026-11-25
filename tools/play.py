import sys,os,json; sys.path.insert(0,os.path.dirname(__file__))
from emu import Emu
e=Emu(int(os.environ.get('PORT','46677')))
# usage: play.py "a,a,start,down*3,shot:x" ; each step: btn[*n] or wait:N or shot:name or save:name or load:name
for step in sys.argv[1].split(','):
    step=step.strip()
    if step.startswith('wait:'): e.run(int(step[5:]))
    elif step.startswith('shot:'): e.shot('shots/%s.png'%step[5:])
    elif step.startswith('hold:'):
        _,b,n=step.split(':'); e(cmd='buttons',hold=b.split('+')); e.run(int(n)); e(cmd='buttons',hold=[])
    elif step.startswith('save:'): e(cmd='save',path=os.path.abspath('saves/%s.state'%step[5:]))
    elif step.startswith('load:'): e(cmd='load',path=os.path.abspath('saves/%s.state'%step[5:]))
    else:
        n=1
        if '*' in step: step,n=step.split('*'); n=int(n)
        for i in range(n): e.tap(step,4,16)
