"""Lunatic Dawn III text helpers: tokenize SJIS game text <-> editable strings."""
import os, struct, re

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
EXT = os.path.join(WORK, 'ext')

def lead(c):
    return 0x81 <= c <= 0x9f or 0xe0 <= c <= 0xef

def decode(t):
    """bytes (no terminator) -> editable str. Raises ValueError if not text-like."""
    out = []; i = 0; n = len(t)
    while i < n:
        c = t[i]
        if lead(c):
            if i + 1 >= n: raise ValueError('cut')
            ch = t[i:i+2].decode('cp932')
            out.append(ch); i += 2
        elif c == 0x0a:
            out.append('\n'); i += 1
        elif c == 0x01 and i + 2 < n + 0 and i + 2 <= n - 1 and 0x41 <= t[i+1] <= 0x5a and 0x30 <= t[i+2] <= 0x39:
            out.append('{%c%c}' % (t[i+1], t[i+2])); i += 3
        elif c == 0x1b and i + 1 < n:
            L = t[i+1]
            if L in (0x50, 0x57):      # P, W
                out.append('<%c>' % L); i += 2
            elif i + 2 < n and 0x30 <= t[i+2] <= 0x39:
                out.append('<%c%c>' % (L, t[i+2])); i += 3
            else:
                out.append('{%02x}' % c); i += 1
        elif 0x20 <= c <= 0x7e and chr(c) not in '{}<>':
            out.append(chr(c)); i += 1
        else:
            out.append('{%02x}' % c); i += 1
    return ''.join(out)

TOK = re.compile(r'\{([A-Z])(\d)\}|<([PW])>|<([A-Za-z])(\d)>|\{([0-9a-f]{2})\}|(\n)|(%-?\d*[a-z]|\\[a-z0-9])|(.)', re.S)

def encode(s, cmap):
    """editable str -> bytes using cmap (char -> u16 code)."""
    out = bytearray()
    for m in TOK.finditer(s):
        if m.group(1):
            out += bytes([1, ord(m.group(1)), ord(m.group(2))])
        elif m.group(3):
            out += bytes([0x1b, ord(m.group(3))])
        elif m.group(4):
            out += bytes([0x1b, ord(m.group(4)), ord(m.group(5))])
        elif m.group(6):
            out.append(int(m.group(6), 16))
        elif m.group(7):
            out.append(0x0a)
        elif m.group(8):
            out += m.group(8).encode('ascii')
        else:
            ch = m.group(9)
            if ord(ch) < 0x7f and ch not in cmap:
                out.append(ord(ch)); continue
            if ch not in cmap:
                raise KeyError('no glyph for %r in %r' % (ch, s))
            c = cmap[ch]
            if c < 0x100: out.append(c)
            else: out += bytes([c >> 8, c & 255])
    return bytes(out)

def visible(s):
    """characters needing glyphs"""
    return [m.group(9) for m in TOK.finditer(s) if m.group(9) and (ord(m.group(9)) >= 0x7f or m.group(9) in ',.?!~:()-/%+')]

def plain(s):
    return TOK.sub(lambda m: m.group(9) or '', s)

def is_texty(t, minchars=1):
    try:
        s = decode(t)
    except Exception:
        return False
    if '{' in re.sub(r'\{[A-Z]\d\}', '', s):  # raw hex bytes -> reject
        return False
    return len(visible(s)) >= minchars

def rd(p):
    return open(os.path.join(EXT, p), 'rb').read()
