"""Check a translation output against its input.
usage: python tools/trcheck.py tr/X_in.json tr/X_ko.json [--terms]
"""
import json, re, sys
from collections import Counter

TOKRE = re.compile(r'\{[A-Z]\d\}|<[PW]>|<[A-Za-z]\d>|\{[0-9a-f]{2}\}|\\[a-z0-9]|%-?\d*[ds]')
ALLOWED_PUNCT = set(' ,.?!~:()-/%…・「」『』○×△□※＆＋０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ')

def nbytes(s):
    n = 0
    for m in re.finditer(r'\{[A-Z]\d\}|<[PW]>|<[A-Za-z]\d>|\{[0-9a-f]{2}\}|(.)', s, re.S):
        if m.group(1) is None:
            t = m.group(0)
            n += 3 if (t.startswith('{') and len(t) == 4) or (t.startswith('<') and len(t) == 4) else (2 if t.startswith('<') else 1)
        else:
            ch = m.group(1)
            n += 1 if ord(ch) < 0x80 else 2
    return n

def vis(s):
    return len(TOKRE.sub('', s).replace('\n', ''))

def main():
    a = json.load(open(sys.argv[1], encoding='utf-8'))
    b = json.load(open(sys.argv[2], encoding='utf-8'))
    terms = '--terms' in sys.argv
    bad = 0
    for x in a:
        i = x['id']
        if i not in b:
            print('MISSING', i); bad += 1; continue
        ko = b[i]; jp = x['jp']
        tj = Counter(TOKRE.findall(jp)); tk = Counter(TOKRE.findall(ko))
        if tj != tk:
            print('TOKENS', i, dict(tj), dict(tk)); bad += 1
        if jp.count('\n') != ko.count('\n'):
            print('NEWLINES', i, jp.count('\n'), ko.count('\n'), repr(ko)); bad += 1
        rest = TOKRE.sub('', ko).replace('\n', '')
        for ch in rest:
            if not ('가' <= ch <= '힣' or ch in ALLOWED_PUNCT):
                print('CHAR', i, repr(ch), repr(ko)); bad += 1; break
        if 'max' in x and nbytes(ko) > x['max']:
            print('TOOLONG(bytes)', i, nbytes(ko), '>', x['max'], repr(ko)); bad += 1
        if terms and 'max' not in x and '\n' not in jp and vis(ko) > vis(jp) + 1 and vis(jp) <= 16:
            print('LONG(chars)', i, vis(jp), vis(ko), jp, '->', ko); bad += 1
    # budgets
    from collections import defaultdict
    tot = defaultdict(int); orig = defaultdict(int)
    for x in a:
        i = x['id']; parts = i.split('/')
        key = None
        if parts[0] == 'msg': key = 'msg/' + parts[1]
        elif parts[0] == 'adv': key = 'adv'
        if key and i in b:
            tot[key] += nbytes(b[i]) + 1; orig[key] += nbytes(x['jp']) + 1
    for k in sorted(tot):
        lim = 11272 if k.startswith('msg/') and int(k.split('/')[1]) < 15 else (520 if k.startswith('msg/') else int(orig[k] * 1.04))
        flag = 'OVER BUDGET!' if tot[k] > lim else 'ok'
        if tot[k] > lim: bad += 1
        print('BUDGET %-8s %6d / limit %6d (orig %6d) %s' % (k, tot[k], lim, orig[k], flag))
    extra = set(b) - set(x['id'] for x in a)
    if extra: print('EXTRA ids', list(extra)[:5]); bad += 1
    print('issues:', bad)

if __name__ == '__main__':
    main()
