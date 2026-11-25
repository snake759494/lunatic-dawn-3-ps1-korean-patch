"""client for host.py"""
import socket,json,sys,os
class Emu:
    def __init__(s,port=46677):
        s.s=socket.create_connection(('127.0.0.1',port)); s.f=s.s.makefile('rwb')
    def __call__(s,**kw):
        s.f.write((json.dumps(kw)+'\n').encode()); s.f.flush()
        r=json.loads(s.f.readline())
        if not r.get('ok'): raise RuntimeError(r)
        return r
    def run(s,n): return s(cmd='run',frames=n)
    def tap(s,b,f=4,run=20): return s(cmd='tap',btn=b,frames=f,run=run)
    def shot(s,p): return s(cmd='shot',path=os.path.abspath(p))
    def read(s,a,n): return bytes.fromhex(s(cmd='read',addr='%x'%a,len=n)['hex'])
    def ev(s,code): return s(cmd='eval',code=code)['result']
if __name__=='__main__':
    e=Emu(); print(e(**json.loads(sys.argv[1])))
