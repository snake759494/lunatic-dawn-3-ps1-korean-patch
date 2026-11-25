"""Extract all game text into work/text/<src>.json  (id, jp, [max])"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(__file__))
from ld3 import *

OUT = os.path.join(WORK, 'text'); os.makedirs(OUT, exist_ok=True)

def cstr(d, o):
    e = d.index(0, o); return d[o:e]

def save(name, items):
    json.dump(items, open(os.path.join(OUT, name + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(name, len(items), sum(len(plain(x['jp'])) for x in items))

GAME = rd('GAME.BIN'); GBASE = 0x80170a38
MSGTAB = 0x801d125c - GBASE

def msg_blocks():
    d = rd('MSG/MSG.DAT'); res = []
    for k in range(45):
        off, sz = struct.unpack_from('<2I', GAME, MSGTAB + 8 * k)
        blk = d[off:off + sz]
        tot, pb, tl = struct.unpack_from('<3I', blk, 0)
        ps = tot - tl - pb
        offs = struct.unpack_from('<%dH' % (pb // 2), blk, ps)
        txt = blk[ps + pb:]
        res.append((k, blk[:ps], offs, txt))
    return res

def ex_msg():
    items = []
    for k, hdr, offs, txt in msg_blocks():
        seen = {}
        for i, o in enumerate(offs):
            if o in seen: continue
            seen[o] = i
            items.append({'id': 'msg/%d/%d' % (k, i), 'jp': decode(cstr(txt, o))})
    save('msg', items)

def ptr_overlay(name, fname, base, tab, n):
    d = rd(fname); items = []; seen = set()
    for i in range(n):
        p = struct.unpack_from('<I', d, tab + 4 * i)[0] - base
        if p in seen or not (4 <= p < tab): continue
        seen.add(p)
        items.append({'id': '%s/%d' % (name, i), 'jp': decode(cstr(d, p))})
    save(name, items)

def ex_req():
    d = rd('REQUEST/REQUEST.DAT'); items = []
    for r in range(119):
        o = 8 + 119 * 48 + r * 640
        for f, (fo, fl) in enumerate([(0, 40), (40, 200), (240, 200), (440, 200)]):
            t = d[o + fo:o + fo + fl]; t = t[:t.index(0)] if 0 in t else t
            if t:
                items.append({'id': 'req/%d/%d' % (r, f), 'jp': decode(t), 'max': fl - 1})
    save('req', items)

def game_targets():
    """all word/code-referenced text strings in GAME.BIN -> {off: (bytes, [refs])}"""
    from refs import code_refs
    d = GAME; T = {}
    for j in range(0, len(d) - 3, 4):
        w = struct.unpack_from('<I', d, j)[0] - GBASE
        if 4 <= w < len(d): T.setdefault(w, []).append(('w', j))
    for a, L in code_refs(d, GBASE + 4, GBASE + len(d), 0x7500).items():
        T.setdefault(a - GBASE, []).extend(L)
    res = {}
    for p, refs in T.items():
        c = d[p]
        if not (lead(c) or c in (0x1b, 0x5c, 0x01)): continue
        try: e = d.index(0, p)
        except ValueError: continue
        t = d[p:e]
        if is_texty(t, 1): res[p] = (t, refs)
    return res

def ex_game():
    items = []
    for p, (t, refs) in sorted(game_targets().items()):
        items.append({'id': 'game/%x' % p, 'jp': decode(t)})
    save('game', items)

def inplace(name, fname, ranges=None, minchars=1):
    """strings found by scanning (null-separated), translated in place; max = available bytes."""
    d = rd(fname); items = []
    i = 0; n = len(d)
    while i < n:
        if lead(d[i]) or d[i] == 0x1b:
            j = i
            while j < n and d[j] != 0: j += 1
            t = d[i:j]
            if is_texty(t, minchars) and (i == 0 or d[i - 1] == 0):
                k = j
                while k < n and d[k] == 0: k += 1
                avail = (k - i) - 1  # keep at least one terminator
                # keep alignment of following data: only use up to next 4-aligned boundary before k
                items.append({'id': '%s/%x' % (name, i), 'jp': decode(t), 'max': avail, 'orig': len(t)})
            i = j + 1
        else:
            i += 1
    save(name, items)

if __name__ == '__main__':
    ex_msg()
    ptr_overlay('adv', 'ADVMSG.BIN', 0x801f19a0, 0x8024, 743)
    ptr_overlay('names', 'DATMODL.BIN', 0x801f19a0, 0x420c, 1318)
    ex_req()
    ex_game()
    for nm, f in [('mod1', 'MODULE1.BIN'), ('mod2', 'MODULE2.BIN'), ('cdconf', 'CDCONF.BIN'),
                  ('movie', 'MOVIE.BIN'), ('exe', 'SLPS_017.49')]:
        inplace(nm, f, minchars=2)
