"""Find absolute references (data words and lui/addiu pairs) into a range."""
import struct
def word_refs(d,lo,hi,align=4):
    out={}
    for j in range(0,len(d)-3,align):
        w=struct.unpack_from('<I',d,j)[0]
        if lo<=w<hi: out.setdefault(w,[]).append(('w',j))
    return out
def code_refs(d,lo,hi,start=0,end=None):
    """lui r,hi ; then addiu/ori/lw/lb.. r2,r,lo within 24 instrs (r not overwritten)"""
    end=end or len(d); out={}
    n=(end-start)//4
    W=struct.unpack_from('<%dI'%n,d,start)
    for i,w in enumerate(W):
        if (w>>26)==0xf:
            rt=(w>>16)&31; himm=w&0xffff
            for k in range(i+1,min(n,i+24)):
                x=W[k]; op=x>>26; rs=(x>>21)&31; rt2=(x>>16)&31
                if op in (9,0xd,0x20,0x21,0x23,0x24,0x25,0x28,0x29,0x2b) and rs==rt:
                    imm=x&0xffff
                    a=((himm<<16)+(imm if op==0xd else (imm-0x10000 if imm&0x8000 else imm)))&0xffffffff
                    if lo<=a<hi: out.setdefault(a,[]).append(('c',start+i*4,start+k*4))
                # stop if rt overwritten
                if op==0xf and rt2==rt: break
                if op in (9,0xd,0x23,0x21,0x25,0x20,0x24,0x0c,0x0a,0x0b,0x0e) and rt2==rt and not(rs==rt and op in(9,0xd)): break
                if op==0 and ((x>>11)&31)==rt: break
    return out
