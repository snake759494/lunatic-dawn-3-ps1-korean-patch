"""Write files back into a MODE2/2352 BIN (Form1 sectors, EDC/ECC recomputed) and fix ISO dir sizes."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
from iso import Disc, SEC
from cdecc import fix_sector_mode2form1

class DiscW(Disc):
    def __init__(s, path):
        s.f = open(path, 'r+b')
        s.index = {n: (l, sz, dl, dp) for n, l, sz, dl, dp in s.walk()}

    def write_sector(s, lba, data2048, last=False):
        s.f.seek(lba * SEC); sec = bytearray(s.f.read(SEC))
        sec[24:24 + 2048] = data2048.ljust(2048, b'\0')
        # keep subheader; set EOR/EOF bits on last sector of file like original? keep as is
        fix_sector_mode2form1(sec)
        s.f.seek(lba * SEC); s.f.write(sec)

    def replace(s, name, data, alloc_sectors):
        lba, sz, dl, dp = s.index[name]
        n = (len(data) + 2047) // 2048
        assert n <= alloc_sectors, '%s: %d sectors > alloc %d' % (name, n, alloc_sectors)
        old = (sz + 2047) // 2048
        for i in range(max(n, old)):
            chunk = data[i * 2048:(i + 1) * 2048] if i < n else b''
            if i < n or i < old:
                s.write_sector(lba + i, chunk)
        if len(data) != sz:
            s.set_size(name, len(data))

    def set_size(s, name, size):
        lba, sz, dl, dp = s.index[name]
        # directory record at sector dl + dp//2048, offset dp%2048
        sl = dl + dp // 2048; off = dp % 2048
        d = bytearray(s.read(sl))
        struct.pack_into('<I', d, off + 10, size); struct.pack_into('>I', d, off + 14, size)
        s.write_sector(sl, bytes(d))
        s.index[name] = (lba, size, dl, dp)
