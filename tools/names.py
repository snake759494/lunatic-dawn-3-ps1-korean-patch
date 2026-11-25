"""NPC name transliteration constrained to the 8px syllable set (S8).
Writes tr/names_ko.json (DATMODL 'names/i' + GAME name ids) and tr/s8.json.
"""
import os, sys, json
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
from translit import translit, decompose, compose, CHO, JUNG, JONG
from ld3 import WORK, visible

TR = os.path.join(WORK, 'tr')
S8_BUDGET = 197
KOREAN_NAME = '틱민수지훈현준영희서연우진호성하윤은정혜경미재동태석철상용원주아유나예다소시도한빈규혁승찬율'

def J(p): return json.load(open(p, encoding='utf-8'))

VSIM = {'ㅟ': 'ㅣ', 'ㅞ': 'ㅔ', 'ㅝ': 'ㅓ', 'ㅘ': 'ㅏ', 'ㅙ': 'ㅐ', 'ㅚ': 'ㅔ', 'ㅢ': 'ㅣ', 'ㅖ': 'ㅔ', 'ㅒ': 'ㅐ',
        'ㅛ': 'ㅗ', 'ㅠ': 'ㅜ', 'ㅑ': 'ㅏ', 'ㅕ': 'ㅓ', 'ㅐ': 'ㅔ', 'ㅡ': 'ㅜ', 'ㅓ': 'ㅗ', 'ㅔ': 'ㅐ', 'ㅜ': 'ㅡ', 'ㅗ': 'ㅓ'}
CSIM = {'ㅋ': 'ㄱ', 'ㄱ': 'ㅋ', 'ㅌ': 'ㄷ', 'ㄷ': 'ㅌ', 'ㅍ': 'ㅂ', 'ㅂ': 'ㅍ', 'ㅊ': 'ㅈ', 'ㅈ': 'ㅊ', 'ㅆ': 'ㅅ',
        'ㄲ': 'ㄱ', 'ㄸ': 'ㄷ', 'ㅃ': 'ㅂ', 'ㅉ': 'ㅈ', 'ㅎ': 'ㅇ', 'ㄹ': 'ㄴ', 'ㄴ': 'ㄹ', 'ㅁ': 'ㄴ'}

def dist(a, b):
    ca, va, fa = decompose(a); cb, vb, fb = decompose(b)
    d = 0
    if ca != cb: d += 3 if CSIM.get(ca) == cb else 8
    if va != vb: d += 2 if (VSIM.get(va) == vb or VSIM.get(vb) == va) else 7
    if fa != fb: d += 1 if (fa == ' ' or fb == ' ') else 2
    return d

def nearest(ch, S):
    return min(S, key=lambda s: (dist(ch, s), s))

def run(allowed12=None):
    gin = J(os.path.join(TR, 'names_in.json'))
    din = J(os.path.join(WORK, 'text', 'names.json'))
    items = [(x['id'], x['jp']) for x in gin + din]
    raw = {i: translit(jp) for i, jp in items}
    C = Counter(ch for v in raw.values() for ch in v if ch != ' ')
    S = set(KOREAN_NAME)
    for ch, n in C.most_common():
        if len(S) >= S8_BUDGET: break
        if allowed12 is not None and ch not in allowed12: continue
        S.add(ch)
    out = {}; changed = 0
    for i, v in raw.items():
        w = ''.join(ch if (ch == ' ' or ch in S) else nearest(ch, S) for ch in v)
        if w != v: changed += 1
        out[i] = w
    json.dump(out, open(os.path.join(TR, 'names_ko.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump(sorted(S), open(os.path.join(TR, 's8.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('names', len(out), 'S8', len(S), 'names adjusted', changed)
    return out, S

if __name__ == '__main__':
    out, S = run()
    import random; random.seed(3)
    gin = J(os.path.join(TR, 'names_in.json')) + J(os.path.join(WORK, 'text', 'names.json'))
    for x in random.sample(gin, 40): print(x['jp'], translit(x['jp']), out[x['id']])
