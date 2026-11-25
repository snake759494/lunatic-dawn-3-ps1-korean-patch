"""check tr/rare_ko.json: tokens/limits like trcheck + every syllable must be in tr/allowed.json"""
import json, sys, os, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from ld3 import visible
a = json.load(open('tr/rare_in.json', encoding='utf-8'))
b = json.load(open('tr/rare_ko.json', encoding='utf-8'))
allowed = set(json.load(open('tr/allowed.json', encoding='utf-8')))
bad = 0
for x in a:
    v = b.get(x['id'])
    if v is None: print('MISSING', x['id']); bad += 1; continue
    nz = [ch for ch in visible(v) if '가' <= ch <= '힣' and ch not in allowed]
    if nz: print('NOT-ALLOWED', x['id'], ''.join(sorted(set(nz))), repr(v)); bad += 1
print('allowed-check issues:', bad)
r = subprocess.run([sys.executable, 'tools/trcheck.py', 'tr/rare_in.json', 'tr/rare_ko.json'], capture_output=True, text=True, encoding='utf-8')
print('\n'.join(l for l in r.stdout.splitlines() if not l.startswith('BUDGET')))
