import sys,os,struct;sys.path.insert(0,os.path.dirname(__file__))
from emu import Emu
e=Emu()
# tp.py addr x y  : write two int16 at addr
a=int(sys.argv[1],16); x=int(sys.argv[2]); y=int(sys.argv[3])
e(cmd='write',addr='%x'%a,hex=struct.pack('<hh',x,y).hex())
