"""Compute 12px charset vs budget; write tr/allowed.json and tr/rare_in.json (lines needing rephrase)."""
import os, sys, json
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
from ld3 import WORK, visible
import build
TR = os.path.join(WORK, 'tr')
def J(p): return json.load(open(p, encoding='utf-8'))
ko = build.load_tr()
s8 = set(J(os.path.join(TR, 's8.json')))
C = Counter()
for v in ko.values():
    for ch in visible(v): C[ch] += 1
sym = set(ch for ch in C if not ('가' <= ch <= '힣'))
codes = set((build.PUNCT.get(ch) or build.FULLW.get(ch)) for ch in sym)
nfixed = 1 + len(codes)
budget = 882 - nfixed - 1
H = Counter({k: v for k, v in C.items() if '가' <= k <= '힣'})
forced = set(s8)
for v in J(os.path.join(TR, 'terms_ko.json')).values():
    forced |= set(ch for ch in visible(v) if '가' <= ch <= '힣')
print('forced (names+terms)', len(forced))
order = sorted(H, key=lambda k: (k not in forced, -H[k], k))
allowed = set(order[:budget]) | forced
rare = set(H) - allowed
print('symbols', len(codes), 'budget hangul', budget, 'distinct', len(H), 'rare', len(rare), 'occurrences', sum(H[r] for r in rare))
json.dump(sorted(allowed), open(os.path.join(TR, 'allowed.json'), 'w', encoding='utf-8'), ensure_ascii=False)
# lines with rare syllables (exclude names: they are constrained already)
ins = {}
for fn in os.listdir(TR):
    if fn.endswith('_in.json') and fn not in ('names_in.json', 'rare_in.json'):
        for x in J(os.path.join(TR, fn)): ins[x['id']] = x
out = []
for i, v in ko.items():
    bad = sorted(set(ch for ch in visible(v) if ch in rare))
    if bad:
        x = dict(ins[i]); x['ko'] = v; x['rare'] = ''.join(bad)
        out.append(x)
json.dump(out, open(os.path.join(TR, 'rare_in.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('lines to fix', len(out))
print(''.join(sorted(rare)))
