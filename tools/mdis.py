import capstone,struct
md=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32+capstone.CS_MODE_LITTLE_ENDIAN)
FILES=[('SLPS_017.49',0x80010000,0x800),('GAME.BIN',0x80170a38,0),('MODULE1.BIN',0x801f19a0,0),('MODULE2.BIN',0x801f19a0,0),('DATMODL.BIN',0x801f19a0,0),('ADVMSG.BIN',0x801f19a0,0)]
def dis(d,base):
    out=[]
    for o in range(0,len(d)-3,4):
        r=list(md.disasm(d[o:o+4],base+o))
        out.append((base+o,r[0].mnemonic,r[0].op_str) if r else (base+o,'.word',hex(struct.unpack_from('<I',d,o)[0])))
    return out
def load(fn,base,off,src='ext/'):
    return dis(open(src+fn,'rb').read()[off:],base)
