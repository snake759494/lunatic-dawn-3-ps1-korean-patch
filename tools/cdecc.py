# -*- coding: utf-8 -*-
"""CD-ROM Mode 2 Form 1 EDC / ECC (P,Q) computation (ECM / cdrdao algorithm)."""
ECC_F = [0]*256
ECC_B = [0]*256
EDC_T = [0]*256
for _i in range(256):
    _j = ((_i << 1) ^ (0x11D if (_i & 0x80) else 0)) & 0xFF
    ECC_F[_i] = _j
    ECC_B[(_i ^ _j) & 0xFF] = _i
    _e = _i
    for _ in range(8):
        _e = (_e >> 1) ^ (0xD8018001 if (_e & 1) else 0)
    EDC_T[_i] = _e & 0xFFFFFFFF

def edc_compute(data, edc=0):
    t = EDC_T
    for b in data:
        edc = (edc >> 8) ^ t[(edc ^ b) & 0xFF]
    return edc & 0xFFFFFFFF

def _ecc_block(sec, src_off, major_count, minor_count, major_mult, minor_inc, dest_off):
    """Q parity reads past the 2064-byte payload into the P parity just written,
    so the source stays a view on the whole sector, never a truncated slice."""
    size = major_count * minor_count
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        ecc_a = 0
        ecc_b = 0
        for _ in range(minor_count):
            temp = sec[src_off + index]
            index += minor_inc
            if index >= size:
                index -= size
            ecc_a ^= temp
            ecc_b ^= temp
            ecc_a = ECC_F[ecc_a]
        ecc_a = ECC_B[(ECC_F[ecc_a] ^ ecc_b) & 0xFF]
        sec[dest_off + major] = ecc_a & 0xFF
        sec[dest_off + major + major_count] = (ecc_a ^ ecc_b) & 0xFF

def fix_sector_mode2form1(sec):
    """sec: bytearray(2352). Recompute EDC (0x818) and ECC P (0x81C) / Q (0x8C8)."""
    assert len(sec) == 2352
    edc = edc_compute(sec[16:2072])            # subheader + user data
    sec[2072] =  edc        & 0xFF
    sec[2073] = (edc >> 8)  & 0xFF
    sec[2074] = (edc >> 16) & 0xFF
    sec[2075] = (edc >> 24) & 0xFF
    hdr = bytes(sec[12:16])
    sec[12:16] = b'\x00\x00\x00\x00'           # header zeroed for Form 1 ECC
    _ecc_block(sec, 12, 86, 24,  2, 86, 0x81C)
    _ecc_block(sec, 12, 52, 43, 86, 88, 0x8C8)
    sec[12:16] = hdr
    return sec
