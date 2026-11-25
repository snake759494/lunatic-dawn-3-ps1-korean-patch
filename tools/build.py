"""Lunatic Dawn III Korean patch builder.
python tools/build.py [--test]   -> writes ../Lunatic Dawn III (Korean) (Track 1).bin etc.
"""
import os, sys, json, struct, shutil, re
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
from ld3 import *
from extract_text import msg_blocks, game_targets, GAME as GAME_ORIG, GBASE, MSGTAB, cstr
import mkfont
from translit import translit

ROOT = os.path.dirname(WORK)
SRC_BIN = os.path.join(ROOT, 'Lunatic Dawn III (Japan) (Track 1).bin')
SRC_BIN2 = os.path.join(ROOT, 'Lunatic Dawn III (Japan) (Track 2).bin')
OUT_BIN = os.path.join(ROOT, 'Lunatic Dawn III (Korean) (Track 1).bin')
OUT_BIN2 = os.path.join(ROOT, 'Lunatic Dawn III (Korean) (Track 2).bin')
OUT_CUE = os.path.join(ROOT, 'Lunatic Dawn III (Korean).cue')
TR = os.path.join(WORK, 'tr')

def J(p): return json.load(open(p, encoding='utf-8'))

# ---------------------------------------------------------------- translations
def load_tr():
    ko = {}
    late = ['names_ko.json', 'rare_ko.json']
    for fn in sorted(os.listdir(TR)):
        if fn.endswith('_ko.json') and fn not in late:
            ko.update(J(os.path.join(TR, fn)))
    for fn in late:
        if os.path.exists(os.path.join(TR, fn)): ko.update(J(os.path.join(TR, fn)))
    fx = os.path.join(TR, 'fixups.json')
    if os.path.exists(fx): ko.update(J(fx))
    n = 0
    for k, v in ko.items():
        w = josa(v)
        if w != v: ko[k] = w; v = w; n += 1
    print('josa: %d strings' % n); n = 0
    for k, v in ko.items():
        if balloon_id(k):
            w = wordwrap(v)
            if w != v: ko[k] = w; n += 1
    print('wordwrap: %d strings' % n)
    return ko

# particle after a runtime-substituted name -> both forms
_JOSA = {'은': '은(는)', '는': '은(는)', '이': '이(가)', '가': '이(가)', '을': '을(를)', '를': '을(를)', '와': '와(과)', '과': '와(과)'}
_JRE = re.compile(r'(\{[A-Z]\d\}|\\[prdtm]|%s)((?:<C\d>)?)([은는이가을를와과])(?=[ \n.,!?…~」』<　]|$)')
def josa(s):
    return _JRE.sub(lambda m: m.group(1) + m.group(2) + _JOSA[m.group(3)], s)

# balloon text wraps hard at 16 cells in-game; pre-break at spaces instead
WRAP_W = 16
_WTOK = re.compile(r'(\{[A-Z]\d\}|\\[a-z0-9])|(<[PW]>|<[A-Za-z]\d>|\{[0-9a-f]{2}\}|%-?\d*[ds])|(.)', re.S)
def balloon_id(k):
    if k.startswith(('msg/', 'adv/')): return True
    if k.startswith('req/') and k.endswith('/3'): return True
    if k.startswith('game/'):
        o = int(k[5:], 16)
        return o >= 0x79f4
    return False
def _width(s):
    w = 0
    for m in _WTOK.finditer(s):
        if m.group(1): w += 4
        elif m.group(3): w += 1
    return w
def wordwrap(s):
    parts = re.split(r'(\n|<P>)', s)
    out = []
    for p in parts:
        if p in ('\n', '<P>') or _width(p) <= WRAP_W:
            out.append(p); continue
        words = p.split(' '); line = words[0]; lines = []
        for wd in words[1:]:
            if _width(line + ' ' + wd) <= WRAP_W: line += ' ' + wd
            else: lines.append(line); line = wd
        lines.append(line)
        out.append('\n'.join(lines))
    return ''.join(out)

# ------------------------------------------------------------------ char codes
# Korean-side punctuation -> SJIS code slots (glyph drawn by us or kept from original)
PUNCT = {
    # single-byte ASCII punctuation: rendered through table entries with code = ASCII value
    ',': 0x2C, '.': 0x2E, '?': 0x3F, '!': 0x21, '~': 0x7E, ':': 0x3A, '(': 0x28, ')': 0x29,
    '-': 0x2D, '/': 0x2F, '+': 0x2B,
    # double-byte (original SJIS slots)
    '・': 0x8145, 'ー': 0x815B, '…': 0x8163, '「': 0x8175, '」': 0x8176,
    '『': 0x8177, '』': 0x8178, '×': 0x817E, '％': 0x8193, '＆': 0x8195,
    '○': 0x819B, '□': 0x81A0, '△': 0x81A2, '※': 0x81A6, '＋': 0x817B,
}
# glyphs drawn from Galmuri instead of the Japanese original
RENDER_PUNCT = {',': 1, '.': 1, '?': 1, '!': 1, '~': 1, '(': 4, ')': 1, ':': 3, '-': 2, '/': 3, '+': 2}
FULLW = {chr(0xFF10 + i): 0x824F + i for i in range(10)}
FULLW.update({chr(0xFF21 + i): 0x8260 + i for i in range(26)})
FULLW_ORIG = dict(FULLW)
SJIS_ORIG = {}  # code -> original index

HANGUL_START = 0x8890

def next_code(c):
    hi, lo = c >> 8, c & 255
    lo += 1
    if lo == 0x7F: lo = 0x80
    if lo > 0xFC:
        lo = 0x40; hi += 1
        if hi == 0xA0: hi = 0xE0
    return (hi << 8) | lo

def plan_font(texts12, s8):
    """texts12: all strings shown with 12px font. returns (cmap, entries12, entries8)"""
    otab = mkfont.orig_table()
    oidx = {c: i for i, c in enumerate(otab)}
    freq = Counter()
    for s in texts12:
        for ch in visible(s): freq[ch] += 1
    need_punct = sorted(set(ch for ch in freq if ch in PUNCT or ch in FULLW))
    hangul = sorted(ch for ch in freq if '가' <= ch <= '힣')
    other = [ch for ch in freq if not ('가' <= ch <= '힣') and ch not in PUNCT and ch not in FULLW and ch != '　']
    if other:
        raise SystemExit('unsupported chars: %r' % other[:50])
    for ch in s8:
        if ch not in hangul and '가' <= ch <= '힣': hangul.append(ch)
    hangul.sort()
    cmap = {}
    entries = []  # (code, cell)
    blank = [[0] * 12 for _ in range(12)]
    sym = {0x20: blank, 0x8140: blank}
    for ch in need_punct:
        code = PUNCT.get(ch) or FULLW.get(ch)
        cmap[ch] = code
        if code in sym: continue
        if ch in RENDER_PUNCT:
            cell = mkfont.render(ch, dx=RENDER_PUNCT[ch], dy=-1)
        else:
            cell = mkfont.orig_cell(oidx[code])
        sym[code] = cell
    for code in sorted(sym): entries.append((code, sym[code]))
    assert entries[0][0] == 0x20
    budget = mkfont.N - len(entries) - 1  # -1: dummy blank at index 441 (cell 0 of layer B)
    if len(hangul) > budget:
        raise SystemExit('too many hangul syllables: %d > %d' % (len(hangul), budget))
    code = HANGUL_START
    it = iter(hangul)
    while len(entries) < mkfont.N:
        if len(entries) == mkfont.PER:
            entries.append((code, blank))          # dummy, never referenced by text
        else:
            ch = next(it, None)
            if ch is None:
                entries.append((code, blank))
            else:
                cmap[ch] = code
                entries.append((code, mkfont.render(ch, dy=-1)))
        code = next_code(code)
    assert len(entries) == mkfont.N
    return cmap, entries, freq

# ---------------------------------------------------------------- 8px font
def render8(ch, dx=0, dy=-1):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(os.path.join(os.path.dirname(__file__), 'Galmuri7.ttf'), 8)
    im = Image.new('1', (12, 12), 0); d = ImageDraw.Draw(im); d.fontmode = '1'
    d.text((dx, dy), ch, font=f, fill=1)
    px = im.load()
    body = [[px[x, y] for x in range(8)] for y in range(8)]
    out = [[0] * 8 for _ in range(8)]
    for y in range(8):
        for x in range(8):
            if body[y][x]: out[y][x] = 3
            elif (x and body[y][x-1]) or (y and body[y-1][x]) or (x and y and body[y-1][x-1]): out[y][x] = 1
    return out

TABB = mkfont.ORIG_TAB + 882 * 2
def orig_tabB():
    b = rd('SLPS_017.49'); return list(struct.unpack_from('<242H', b, TABB))

def orig_cell8(idx):
    d = rd('ETC/STRING2.TH4'); r, c = divmod(idx, 32)
    out = []
    for y in range(8):
        row = []
        for x in range(8):
            X = c * 8 + x; Y = r * 8 + y
            row.append((d[Y * 128 + X // 2] >> (4 * (X & 1))) & 3)
        out.append(row)
    return out

KEEP8 = ' 　0123456789/:・-?!…ABCDEFGHIJKLMNOPQRSTUVWXYZ'
def build_font8(cmap, s8):
    tb = orig_tabB(); oi = {c: i for i, c in enumerate(tb)}
    ents = []
    for ch in KEEP8:
        if ch == ' ':
            ents.append((0x20, [[0] * 8 for _ in range(8)])); continue
        if ch in '/:-?!':
            ents.append((PUNCT[ch], render8(ch, dx=1))); continue
        if ch == '　': code = 0x8140
        elif ch.isdigit(): code = 0x824F + int(ch)
        elif 'A' <= ch <= 'Z': code = 0x8260 + ord(ch) - 65
        else: code = PUNCT[ch]
        ents.append((code, orig_cell8(oi[code]) if code in oi else render8(ch)))
    for ch in sorted(s8):
        ents.append((cmap[ch], render8(ch)))
    ents.sort()
    assert len(ents) <= 242, len(ents)
    while len(ents) < 242:
        ents.append((0xFFFF - (242 - len(ents)), [[0] * 8 for _ in range(8)]))
    ents.sort()
    th = bytearray(8192)
    for i, (code, cell) in enumerate(ents):
        r, c = divmod(i, 32)
        for y in range(8):
            for x in range(8):
                v = cell[y][x]
                if v:
                    X = c * 8 + x; Y = r * 8 + y
                    th[Y * 128 + X // 2] |= v << (4 * (X & 1))
    # keep original high layer bits (unused by font) as they were
    o = rd('ETC/STRING2.TH4')
    for i in range(8192):
        th[i] |= o[i] & 0xCC
    return bytes(th), struct.pack('<242H', *[c for c, _ in ents])

# ------------------------------------------------------------------ encoders
class Enc:
    def __init__(s, cmap, wide=True):
        s.cmap = dict(cmap); s.cmap['　'] = 0x8140; s.wide = wide
        s.cmap_w = dict(cmap); s.cmap_w[' '] = 0x8140; s.cmap_w['　'] = 0x8140
    def __call__(s, text, wide=None, limit=None):
        # literal percent (not printf) -> fullwidth slot
        text = re.sub(r'%(?!-?\d*[a-z])', '％', text)
        w = s.wide if wide is None else wide
        if not w:
            return encode(text, s.cmap)
        b = encode(text, s.cmap_w)
        if limit is None or len(b) <= limit:
            return b
        # widen spaces left-to-right while it still fits
        parts = text.split(' ')
        nsp = len(parts) - 1
        best = encode(text, s.cmap)
        for k in range(1, nsp + 1):
            t = '　'.join(parts[:k + 1]) + (' ' + ' '.join(parts[k + 1:]) if k < nsp else '')
            bb = encode(t, dict(s.cmap, **{'　': 0x8140}))
            if len(bb) <= limit: best = bb
            else: break
        return best

def tr_of(ko, i, jp):
    if i in ko: return ko[i]
    raise KeyError('missing translation ' + i)

# ------------------------------------------------------------------ MSG.DAT
def build_msg(ko, enc):
    out = bytearray(); table = []
    for k, hdr, offs, txt in msg_blocks():
        first = {}
        for i, o in enumerate(offs):
            first.setdefault(o, i)
        newoff = {}; text = bytearray(); cache = {}
        for o, i in sorted(first.items(), key=lambda t: t[1]):
            b = enc(ko['msg/%d/%d' % (k, i)])
            if b in cache: newoff[o] = cache[b]; continue
            newoff[o] = len(text); cache[b] = len(text)
            text += b + b'\0'
        lim = 11272 if k < 15 else 520
        if len(text) > lim:
            raise SystemExit('MSG block %d text %d > %d' % (k, len(text), lim))
        ptrs = struct.pack('<%dH' % len(offs), *[newoff[o] for o in offs])
        h = bytearray(hdr)
        tot = len(h) + len(ptrs) + len(text)
        struct.pack_into('<3I', h, 0, tot, len(ptrs), len(text))
        blk = bytes(h) + ptrs + bytes(text)
        table.append((len(out), len(blk)))
        out += blk
        out += b'\0' * ((-len(out)) % 2048)
    return bytes(out), table

# ------------------------------------------------------------------ pointer overlays
def build_ptr_overlay(fname, prefix, base, tab, n, ko, enc, region_end=None, alloc=None, strings=None):
    d = bytearray(rd(fname))
    ptrs = list(struct.unpack_from('<%dI' % n, d, tab))
    tgt = {}
    for i, p in enumerate(ptrs):
        o = p - base
        if 4 <= o < tab and o not in tgt: tgt[o] = i
    texts = {}
    for o, i in tgt.items():
        texts[o] = strings[o] if strings is not None else enc(ko['%s/%d' % (prefix, i)])
    # repack strings 4..tab, overflow after table end
    tab_end = tab + 4 * n
    tail = bytearray(d[tab_end:])
    newpos = {}; cache = {}
    cur = 4; region = bytearray()
    over = bytearray()
    for o in sorted(texts, key=lambda o: tgt[o]):
        b = texts[o]
        if b in cache: newpos[o] = cache[b]; continue
        if cur + len(b) + 1 <= tab:
            newpos[o] = cur; region += b + b'\0'; cur += len(b) + 1
        else:
            pos = tab_end + len(tail) + len(over)
            newpos[o] = pos; over += b + b'\0'
        cache[b] = newpos[o]
    d[4:tab] = bytes(region).ljust(tab - 4, b'\0')
    for i, p in enumerate(ptrs):
        o = p - base
        if o in newpos: ptrs[i] = base + newpos[o]
    struct.pack_into('<%dI' % n, d, tab, *ptrs)
    d = d[:tab_end] + tail + over
    while len(d) % 4: d.append(0)
    if alloc and len(d) > alloc:
        raise SystemExit('%s too big: %d > %d' % (fname, len(d), alloc))
    return bytes(d)

# ------------------------------------------------------------------ REQUEST.DAT
def build_req(ko, enc):
    d = bytearray(rd('REQUEST/REQUEST.DAT'))
    for r in range(119):
        o = 8 + 119 * 48 + r * 640
        for f, (fo, fl) in enumerate([(0, 40), (40, 200), (240, 200), (440, 200)]):
            i = 'req/%d/%d' % (r, f)
            if i not in ko: continue
            b = enc(ko[i], limit=fl - 1)
            if len(b) > fl - 1: raise SystemExit('REQ %s too long %d' % (i, len(b)))
            d[o + fo:o + fo + fl] = b.ljust(fl, b'\0')
    return bytes(d)

# ------------------------------------------------------------------ in-place
def build_inplace(fname, prefix, ko, enc, items, base=None, skip=(), wide=True, narrow=()):
    d = bytearray(rd(fname))
    for x in items:
        i = x['id']
        if i in skip or i not in ko: continue
        o = int(i.split('/')[1], 16)
        b = enc(ko[i], wide=(wide and i not in narrow), limit=x['max'])
        if len(b) > x['max']: raise SystemExit('%s too long %d > %d' % (i, len(b), x['max']))
        d[o:o + x['max'] + 1] = b.ljust(x['max'] + 1, b'\0')
    return d

# ------------------------------------------------------------------ GAME.BIN
def patch_ref(d, ref, addr):
    if ref[0] == 'w':
        struct.pack_into('<I', d, ref[1], addr)
    else:
        _, hi_at, lo_at = ref
        w = struct.unpack_from('<I', d, lo_at)[0]
        op = w >> 26
        if op == 0xd:  # ori
            hi = addr >> 16; lo = addr & 0xffff
        else:
            hi = (addr + 0x8000) >> 16; lo = addr & 0xffff
        wh = struct.unpack_from('<I', d, hi_at)[0]
        struct.pack_into('<I', d, hi_at, (wh & 0xffff0000) | hi)
        struct.pack_into('<I', d, lo_at, (w & 0xffff0000) | lo)

def _writes(x):
    """register written by MIPS instruction x (or None)"""
    op = x >> 26
    if op == 0:
        f = x & 63
        if f in (8, 0x18, 0x19, 0x1a, 0x1b, 0x11, 0x13): return None  # jr, mult/div, mthi/lo
        return (x >> 11) & 31
    if op in (8, 9, 0xa, 0xb, 0xc, 0xd, 0xe, 0xf, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26): return (x >> 16) & 31
    if op == 3: return 31
    return None

def fix_branch_hi(d, items, new):
    """A lo half (addiu/lw..) may be reached by a branch whose delay slot holds another
    'lui r,hi' (not seen by the linear ref scanner). Patch those lui to the new hi too."""
    lo_new = {}
    for p, bb, refs in items:
        for r in refs:
            if r[0] == 'c': lo_new[r[2]] = (r[1], GBASE + new[p])
    n = len(d) // 4
    W = struct.unpack_from('<%dI' % n, d)
    O = struct.unpack_from('<%dI' % n, GAME_ORIG)
    fixed = 0
    for i, x in enumerate(O):
        op = x >> 26
        if op in (4, 5, 6, 7) or (op == 1):
            off = x & 0xffff; off = off - 0x10000 if off & 0x8000 else off
            T = i + 1 + off
        elif op == 2:
            T = (x & 0x3ffffff) - ((GBASE & 0x0fffffff) >> 2)
        else:
            continue
        if not (0 <= T < n) or i + 1 >= n: continue
        ds = O[i + 1]
        if ds >> 26 != 0xf: continue
        r = (ds >> 16) & 31
        for k in range(T, min(n, T + 24)):
            y = O[k]
            if (k * 4) in lo_new and ((y >> 21) & 31) == r:
                hi_at, a = lo_new[k * 4]
                if (O[hi_at // 4] & 0xffff) != (ds & 0xffff): break
                w = W[k]
                hi = (a >> 16) if (w >> 26) == 0xd else ((a + 0x8000) >> 16)
                for k2 in range(i + 2, min(n, i + 26)):
                    y2 = O[k2]
                    if ((y2 >> 21) & 31) == r and (y2 >> 26) in (9, 0xd, 0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2b):
                        a2 = lo_new.get(k2 * 4)
                        h2 = None if a2 is None else ((a2[1] >> 16) if (y2 >> 26) == 0xd else ((a2[1] + 0x8000) >> 16))
                        if h2 != hi: raise SystemExit('branch-delay lui conflict at %x' % (GBASE + (i + 1) * 4))
                        break
                    if _writes(y2) == r: break
                struct.pack_into('<I', d, (i + 1) * 4, (ds & 0xffff0000) | hi)
                fixed += 1
                print('  branch-delay lui fixed at %x -> lo %x' % (GBASE + (i + 1) * 4, GBASE + k * 4))
                break
            if _writes(y) == r: break
    print('branch-delay lui fixes:', fixed)

def build_game(ko, enc, msgtab, names_bytes):
    d = bytearray(GAME_ORIG)
    T = game_targets()
    # free regions = union of original string extents
    spans = sorted((p, p + len(t) + 1) for p, (t, r) in T.items())
    regions = []
    for a, b in spans:
        if regions and a <= regions[-1][1] + 3 and all(x == 0 for x in d[regions[-1][1]:a]):
            regions[-1][1] = max(regions[-1][1], b)
        else:
            regions.append([a, b])
    # code-ref hi words shared?  collect lui sites
    lui_users = Counter()
    for p, (t, refs) in T.items():
        for r in refs:
            if r[0] == 'c': lui_users[r[1]] += 1
    for a, b in regions: d[a:b] = b'\0' * (b - a)
    free = [[a, b] for a, b in regions]
    new = {}
    items = []
    for p, (t, refs) in T.items():
        i = 'game/%x' % p
        if i in names_bytes: bb = names_bytes[i]
        else: bb = enc(ko[i])
        items.append((p, bb, refs))
    items.sort(key=lambda x: -len(x[1]))
    cache = {}
    for p, bb, refs in items:
        if bb in cache:
            new[p] = cache[bb]; continue
        need = len(bb) + 1
        for fr in free:
            if fr[1] - fr[0] >= need:
                new[p] = fr[0]; d[fr[0]:fr[0] + len(bb)] = bb; fr[0] += need; break
        else:
            raise SystemExit('GAME.BIN pool full (need %d)' % need)
        cache[bb] = new[p]
    hi_need = {}
    for p, bb, refs in items:
        for r in refs:
            if r[0] == 'c':
                a = GBASE + new[p]
                w = struct.unpack_from('<I', d, r[2])[0]
                hi = (a >> 16) if (w >> 26) == 0xd else ((a + 0x8000) >> 16)
                if hi_need.setdefault(r[1], hi) != hi:
                    raise SystemExit('shared lui conflict for %x' % p)
            patch_ref(d, r, GBASE + new[p])
    fix_branch_hi(d, items, new)
    json.dump({'%x' % p: v for p, v in new.items()}, open(os.path.join(WORK, 'gamemap.json'), 'w'))
    # MSG table
    for k, (off, sz) in enumerate(msgtab):
        struct.pack_into('<2I', d, MSGTAB + 8 * k, off, sz)
    left = sum(b - a for a, b in free)
    print('GAME.BIN pool free bytes left:', left)
    return bytes(d)

# ------------------------------------------------------------------ name entry grid
GRID_P1 = ['1914','1908','18fc','18f0','18e4','18d8','18cc','18c0','18b4','198c','1998','19a4','19b0','19bc','19c8','19d0','19dc','19e8']
GRID_P2 = ['19f4','1a00','1a0c','1a18','1a24','1a30','1a3c','1a48','1a54','1a60','1a6c','1a78','1a84','1a90','1a9c','1aa8','1ab4']
GRID_LOW = ['1b0c','1b18','1b24','1b30','1b3c']
def grid_strings(s8):
    exe = {x['id']: x for x in J(os.path.join(WORK, 'text', 'exe.json'))}
    syl = sorted(s8)
    out = {}
    it = iter(syl)
    for key in GRID_P1 + GRID_P2 + GRID_LOW:
        x = exe['exe/' + key]; jp = x['jp']
        n = len(jp.replace('\n', ''))
        cells = ''.join(next(it, '　') for _ in range(n))
        out['exe/' + key] = cells.replace('　', ' ') + ('\n' if jp.endswith('\n') else '')
    out['exe/1b58'] = '한１\n'; out['exe/1b60'] = '한２\n'; out['exe/1b68'] = 'ＡＢＣ\n'; out['exe/1b70'] = '결정\n'
    left = list(it)
    if left: print('grid: syllables not placed:', ''.join(left))
    return out

INPUT_TAB = 0x54e00   # u16[250]: name-entry codes, page1 90 / page2 90 / page3 70 (left column rows first)
def input_table(grid, cmap):
    exe = {x['id']: x for x in J(os.path.join(WORK, 'text', 'exe.json'))}
    def row(key, fixed=None):
        s = grid.get('exe/' + key)
        if s is None: s = fixed
        cells = [ch for ch in s.replace(chr(10), '')]
        codes = [0x8140 if ch == ' ' else cmap[ch] if ch in cmap else FULLW.get(ch, 0x8140) for ch in cells]
        while len(codes) < 5: codes.append(codes[0] if codes else 0x8140)
        return codes[:5]
    t = []
    p1 = GRID_P1; p2 = GRID_P2
    for k in p1[:9]: t += row(k)
    for k in p1[9:18]: t += row(k)
    for k in p2[:9]: t += row(k)
    for k in p2[9:17]: t += row(k)
    t += row(p1[17])
    up = ['ＡＢＣＤＥ', 'ＦＧＨＩＪ', 'ＫＬＭＮＯ', 'ＰＱＲＳＴ', 'ＵＶＷＸＹ', 'Ｚ', '０１２３４']
    for r in up:
        c = [FULLW[ch] for ch in r]
        while len(c) < 5: c.append(0x8250)
        t += c
    for k in GRID_LOW: t += row(k)
    t += [0x8140] * 5
    t += [FULLW[ch] for ch in '５６７８９']
    assert len(t) == 250, len(t)
    return struct.pack('<250H', *t)

# printf format strings missed by extraction (start with '%'): (file, offset, original, new)
FMT = [
    ('SLPS_017.49', 0x1fbc, '%4d個', '%4d개'),
    ('SLPS_017.49', 0x201c, '%3d日', '%3d일'),
    ('SLPS_017.49', 0x2024, '%3d日', '%3d일'),
    ('SLPS_017.49', 0x854, '□ボタン', '□버튼'),
    ('SLPS_017.49', 0x1b7c, '%4d／%2d／%2d　%2d：００', '%4d/%2d/%2d %2d:００'),
    ('SLPS_017.49', 0x1bc0, '%4d／%2d／%2d', '%4d/%2d/%2d'),
    ('SLPS_017.49', 0x1bfc, '%2d／%2dうまれ'+chr(10), '%2d/%2d'+chr(10)),
    ('MODULE1.BIN', 0x9ac, '%4d／%2d／%2d', '%4d/%2d/%2d'),
    ('MODULE1.BIN', 0x9bc, '%3d：００', '%3d:００'),
]
from fmt_extra import FMT_EXTRA
FMT += FMT_EXTRA
def apply_fmt(fname, d, enc):
    for f, o, old, new in FMT:
        if f != fname: continue
        ob = old.encode('cp932')
        assert bytes(d[o:o + len(ob)]) == ob, (f, hex(o))
        nb = enc(new, wide=False)
        if d[o + len(ob)] != 0:      # string continues: must keep exact length
            assert len(nb) == len(ob), (new, len(nb), len(ob))
            d[o:o + len(ob)] = nb; continue
        room = len(ob)
        while o + room < len(d) and d[o + room] == 0: room += 1
        room -= 1  # keep a terminator
        nb = enc(new, wide=True, limit=room)
        assert len(nb) <= room, (new, len(nb), room)
        L = max(len(ob), len(nb))
        d[o:o + L + 1] = nb.ljust(L + 1, bytes(1))

# ------------------------------------------------------------------ title logo
def build_title():
    from PIL import Image, ImageDraw, ImageFont
    import tim
    d = bytearray(rd('TIM/TITLE.TIM')); t = tim.parse(bytes(d))
    return bytes(d)  # (logo subtitle handled in imgpatch step)

# ------------------------------------------------------------------ main
FILES_ALLOC = {}
def main(test=False):
    ko = load_tr()
    s8 = set(J(os.path.join(TR, 's8.json')))
    ko.update(grid_strings(s8))
    texts12 = [x[3] for x in FMT] + [re.sub(r'%(?!-?\d*[a-z])', '％', v) for v in ko.values()]
    cmap, entries, freq = plan_font(texts12, s8)
    enc = Enc(cmap)
    th1, tabA = mkfont.build(entries)
    th2, tabB = build_font8(cmap, s8)
    mkfont.preview(th1, os.path.join(WORK, 'shots', 'font12.png'))
    nh = sum(1 for ch in cmap if '가' <= ch <= '힣')
    print('12px: hangul', nh, ' 8px: hangul', len(s8))
    out = {}
    # MSG
    msgdat, msgtab = build_msg(ko, enc)
    out['/MSG/MSG.DAT'] = msgdat
    # pointer overlays
    out['/ADVMSG.BIN'] = build_ptr_overlay('ADVMSG.BIN', 'adv', 0x801f19a0, 0x8024, 743, ko, enc, alloc=36864)
    out['/DATMODL.BIN'] = build_ptr_overlay('DATMODL.BIN', 'names', 0x801f19a0, 0x420c, 1318, ko, enc, alloc=22528)
    out['/REQUEST/REQUEST.DAT'] = build_req(ko, enc)
    out['/GAME.BIN'] = build_game(ko, enc, msgtab, {})
    # in-place overlays
    for nm, fn in [('mod1', 'MODULE1.BIN'), ('mod2', 'MODULE2.BIN'), ('cdconf', 'CDCONF.BIN'), ('movie', 'MOVIE.BIN')]:
        items = J(os.path.join(WORK, 'text', nm + '.json'))
        dd = build_inplace(fn, nm, ko, enc, items, skip=('mod1/4216',))
        apply_fmt(fn, dd, enc)
        out['/' + fn] = bytes(dd)
    # exe
    items = [x for x in J(os.path.join(WORK, 'text', 'exe.json')) if int(x['id'].split('/')[1], 16) < 0x3000]
    exe = build_inplace('SLPS_017.49', 'exe', ko, enc, items, wide=True,
                        narrow={'exe/' + k for k in GRID_P1 + GRID_P2 + GRID_LOW + ['1b58', '1b60', '1b68', '1b70']})
    apply_fmt('SLPS_017.49', exe, enc)
    exe[mkfont.ORIG_TAB:mkfont.ORIG_TAB + len(tabA)] = tabA
    exe[TABB:TABB + len(tabB)] = tabB
    gs = {k: v for k, v in ko.items() if k.startswith('exe/') and k[4:] in GRID_P1 + GRID_P2 + GRID_LOW}
    exe[INPUT_TAB:INPUT_TAB + 500] = input_table(gs, cmap)
    assert exe[0x1b48:0x1b4c] == bytes([0x82, 0x9a, 0x0a, 0x00])
    exe[0x1b48:0x1b4c] = bytes([0x20, 0x0a, 0x00, 0x00])
    # kinsoku (hanging punctuation) check at 0x8001ebf8: 0x8141/0x8142/0x8148/0x8149 -> ',' '-' / '.' / '?'
    def pw(addr, old, new):
        o = addr - 0x80010000 + 0x800
        assert struct.unpack_from('<I', exe, o)[0] == old, hex(addr)
        struct.pack_into('<I', exe, o, new)
    pw(0x8001ebfc, 0x24847ebf, 0x2484ffd4)   # addiu a0,a0,-0x2c   (',' '-')
    pw(0x8001ec10, 0x34028148, 0x3402002e)   # ori v0,zero,'.'
    pw(0x8001ec18, 0x34028149, 0x3402003f)   # ori v0,zero,'?'
    out['/SLPS_017.49'] = bytes(exe)
    out['/ETC/STRING1.TH4'] = th1
    out['/ETC/STRING2.TH4'] = th2
    import imgpatch
    out.update(imgpatch.patch_all())
    # write disc
    from isowrite import DiscW
    print('copying disc image...')
    shutil.copyfile(SRC_BIN, OUT_BIN)
    dw = DiscW(OUT_BIN)
    L = sorted((v[0], k) for k, v in dw.index.items() if v[0] > 0)
    nxt = {k: (L[i + 1][0] if i + 1 < len(L) else 120619) for i, (l, k) in enumerate(L)}
    for name, data in out.items():
        lba = dw.index[name][0]
        alloc = nxt[name] - lba
        dw.replace(name, data, alloc)
        print('  %-22s %7d bytes (%d/%d sectors)' % (name, len(data), (len(data) + 2047) // 2048, alloc))
    dw.f.close()
    open(OUT_CUE, 'w').write('FILE "%s" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\nFILE "%s" BINARY\n  TRACK 02 AUDIO\n    INDEX 00 00:00:00\n    INDEX 01 00:02:00\n'
                             % (os.path.basename(OUT_BIN), os.path.basename(SRC_BIN2)))
    json.dump({k: '%04X' % v for k, v in cmap.items()}, open(os.path.join(WORK, 'cmap.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('done')

if __name__ == '__main__':
    main('--test' in sys.argv)
