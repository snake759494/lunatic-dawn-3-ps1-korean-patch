"""after loading a state: write bytes that the new Korean build changed vs JP original into RAM (exe + GAME.BIN)"""
import sys,os;sys.path.insert(0,os.path.dirname(__file__))
from emu import Emu
from iso import Disc
B=Disc('../Lunatic Dawn III (Korean) (Track 1).bin'); fb={n:(l,sz) for n,l,sz,_,_ in B.walk()}
e=Emu()
for fn,base,off in [('/SLPS_017.49',0x80010000,0x800),('/GAME.BIN',0x80170a38,0)]:
    new=B.readfile(*fb[fn])[off:]; jp=open('ext'+fn,'rb').read()[off:]
    ram=b''.join(e.read(base+i,min(0x8000,len(new)-i)) for i in range(0,len(new),0x8000))
    n=0;i=0
    while i<len(new):
        if new[i]!=jp[i] and ram[i]!=new[i]:
            j=i
            while j<len(new) and (new[j]!=ram[j]) and j-i<256: j+=1
            e(cmd='write',addr='%x'%(base+i),hex=new[i:j].hex()); n+=j-i; i=j
        else: i+=1
    print(fn,'patched',n)
