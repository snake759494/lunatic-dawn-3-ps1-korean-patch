"""Rule-based kana -> Hangul transliteration for fantasy NPC names (written for this project)."""
import unicodedata

CHO = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'
JUNG = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'
JONG = ' ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ'

def compose(c, v, f=' '):
    return chr(0xAC00 + (CHO.index(c) * 21 + JUNG.index(v)) * 28 + JONG.index(f))

def decompose(s):
    k = ord(s) - 0xAC00
    return CHO[k // 588], JUNG[(k % 588) // 28], JONG[k % 28]

def add_final(syl, f):
    c, v, ff = decompose(syl)
    if ff != ' ': return None
    return compose(c, v, f)

# base kana (katakana) -> (initial, vowel)
ROW = {
 'ア':'ㅇㅏ','イ':'ㅇㅣ','ウ':'ㅇㅜ','エ':'ㅇㅔ','オ':'ㅇㅗ',
 'カ':'ㅋㅏ','キ':'ㅋㅣ','ク':'ㅋㅜ','ケ':'ㅋㅔ','コ':'ㅋㅗ',
 'ガ':'ㄱㅏ','ギ':'ㄱㅣ','グ':'ㄱㅜ','ゲ':'ㄱㅔ','ゴ':'ㄱㅗ',
 'サ':'ㅅㅏ','シ':'ㅅㅣ','ス':'ㅅㅡ','セ':'ㅅㅔ','ソ':'ㅅㅗ',
 'ザ':'ㅈㅏ','ジ':'ㅈㅣ','ズ':'ㅈㅡ','ゼ':'ㅈㅔ','ゾ':'ㅈㅗ',
 'タ':'ㅌㅏ','チ':'ㅊㅣ','ツ':'ㅊㅡ','テ':'ㅌㅔ','ト':'ㅌㅗ',
 'ダ':'ㄷㅏ','ヂ':'ㅈㅣ','ヅ':'ㅈㅡ','デ':'ㄷㅔ','ド':'ㄷㅗ',
 'ナ':'ㄴㅏ','ニ':'ㄴㅣ','ヌ':'ㄴㅜ','ネ':'ㄴㅔ','ノ':'ㄴㅗ',
 'ハ':'ㅎㅏ','ヒ':'ㅎㅣ','フ':'ㅍㅜ','ヘ':'ㅎㅔ','ホ':'ㅎㅗ',
 'バ':'ㅂㅏ','ビ':'ㅂㅣ','ブ':'ㅂㅜ','ベ':'ㅂㅔ','ボ':'ㅂㅗ',
 'パ':'ㅍㅏ','ピ':'ㅍㅣ','プ':'ㅍㅜ','ペ':'ㅍㅔ','ポ':'ㅍㅗ',
 'マ':'ㅁㅏ','ミ':'ㅁㅣ','ム':'ㅁㅜ','メ':'ㅁㅔ','モ':'ㅁㅗ',
 'ヤ':'ㅇㅑ','ユ':'ㅇㅠ','ヨ':'ㅇㅛ',
 'ラ':'ㄹㅏ','リ':'ㄹㅣ','ル':'ㄹㅜ','レ':'ㄹㅔ','ロ':'ㄹㅗ',
 'ワ':'ㅇㅘ','ヲ':'ㅇㅗ','ヴ':'ㅂㅜ',
 'ァ':'ㅇㅏ','ィ':'ㅇㅣ','ゥ':'ㅇㅜ','ェ':'ㅇㅔ','ォ':'ㅇㅗ','ャ':'ㅇㅑ','ュ':'ㅇㅠ','ョ':'ㅇㅛ',
}
# combinations with small kana
COMBO = {
 'ティ':'ㅌㅣ','ディ':'ㄷㅣ','トゥ':'ㅌㅜ','ドゥ':'ㄷㅜ','テュ':'ㅌㅠ','デュ':'ㄷㅠ',
 'ファ':'ㅍㅏ','フィ':'ㅍㅣ','フェ':'ㅍㅔ','フォ':'ㅍㅗ','フュ':'ㅍㅠ',
 'ヴァ':'ㅂㅏ','ヴィ':'ㅂㅣ','ヴェ':'ㅂㅔ','ヴォ':'ㅂㅗ','ヴュ':'ㅂㅠ',
 'ウィ':'ㅇㅟ','ウェ':'ㅇㅞ','ウォ':'ㅇㅝ',
 'シェ':'ㅅㅔ','ジェ':'ㅈㅔ','チェ':'ㅊㅔ','ツァ':'ㅊㅏ','ツィ':'ㅊㅣ','ツェ':'ㅊㅔ','ツォ':'ㅊㅗ',
 'クァ':'ㅋㅘ','クィ':'ㅋㅟ','クェ':'ㅋㅞ','クォ':'ㅋㅝ','グァ':'ㄱㅘ','グィ':'ㄱㅟ','グェ':'ㄱㅞ','グォ':'ㄱㅝ',
 'イェ':'ㅇㅖ','スィ':'ㅅㅣ','ズィ':'ㅈㅣ','ホゥ':'ㅎㅗ',
}
YOON = {'ャ':'ㅑ','ュ':'ㅠ','ョ':'ㅛ'}
YOON_BASE = {'キ':'ㅋ','ギ':'ㄱ','シ':'ㅅ','ジ':'ㅈ','チ':'ㅊ','ヂ':'ㅈ','ニ':'ㄴ','ヒ':'ㅎ','ビ':'ㅂ','ピ':'ㅍ','ミ':'ㅁ','リ':'ㄹ'}
# sibilants: シャ->샤 but ジャ/チャ -> 자/차 (Korean loanword norm)
YOON_PLAIN = {'ジ', 'チ', 'ヂ'}
CONS_FINAL_ROWS = set('トドクグフブプスズツッルムンァィゥェォャュョー')

def hira2kata(s):
    return ''.join(chr(ord(c) + 0x60) if 'ぁ' <= c <= 'ゖ' else c for c in s)

def units(s):
    """split katakana string into units [(cho, jung, src)] plus markers"""
    out = []; i = 0
    while i < len(s):
        two = s[i:i+2]
        if two in COMBO:
            cv = COMBO[two]; out.append([cv[0], cv[1], two]); i += 2; continue
        c = s[i]
        if c in YOON_BASE and i + 1 < len(s) and s[i+1] in YOON:
            v = YOON[s[i+1]]
            if c in YOON_PLAIN: v = {'ㅑ':'ㅏ','ㅠ':'ㅜ','ㅛ':'ㅗ'}[v]
            out.append([YOON_BASE[c], v, s[i:i+2]]); i += 2; continue
        if c in ('ー', 'ン', 'ッ', '・', '　', ' '):
            out.append([c, None, c]); i += 1; continue
        if c in ROW:
            cv = ROW[c]; out.append([cv[0], cv[1], c]); i += 1; continue
        out.append(['?', None, c]); i += 1
    return out

def is_cons_like(u):
    """kana unit that, in a foreign name, often stands for a bare consonant"""
    return u[1] in ('ㅜ', 'ㅡ', 'ㅗ') and u[2] in ('ト','ド','ク','グ','フ','ブ','プ','ス','ズ','ツ','ル','ム')

def translit_jp(name):
    """Japanese given names (hiragana): plain syllable mapping."""
    s = hira2kata(name); U = units(s); res = []
    for k, u in enumerate(U):
        c, v, src = u
        if c == 'ー': continue
        if c in ('・', '　', ' '): res.append(' '); continue
        if c == 'ン':
            if res and add_final(res[-1], 'ㄴ'): res[-1] = add_final(res[-1], 'ㄴ')
            else: res.append('은')
            continue
        if c == 'ッ':
            if res and add_final(res[-1], 'ㅅ'): res[-1] = add_final(res[-1], 'ㅅ')
            continue
        if c in ('?', 'skip'): continue
        if src == 'ツ': v = 'ㅡ'
        if src == 'ウ' and res and decompose(res[-1])[1] in ('ㅗ', 'ㅛ') and decompose(res[-1])[2] == ' ':
            continue
        if k == 0 and c in ('ㅋ', 'ㅌ', 'ㅊ') and src not in ('ツ',):
            c = {'ㅋ': 'ㄱ', 'ㅌ': 'ㄷ', 'ㅊ': 'ㅈ'}[c]
        res.append(compose(c, v))
    return ''.join(res)

def translit(name):
    if name and all('ぁ' <= ch <= 'ゖ' or ch == 'ー' for ch in name):
        return translit_jp(name)
    s = hira2kata(name)
    U = units(s)
    res = []  # list of syllables (str) or separators
    n = len(U)
    for k, u in enumerate(U):
        c, v, src = u
        nxt = U[k+1] if k + 1 < n else None
        at_end = nxt is None or nxt[0] in ('・', '　', ' ')
        if c == 'ー':
            # English-like 'ee' after e: ゲート -> 게이트
            if res and res[-1] != ' ' and decompose(res[-1])[1] == 'ㅔ' and decompose(res[-1])[2] == ' ' and nxt is not None and nxt[0] not in ('ン','ー','・') :
                res.append('이')
            continue
        if c in ('・', '　', ' '):
            res.append(' '); continue
        if c == 'ン':
            if res and res[-1] != ' ' and add_final(res[-1], 'ㄴ'):
                res[-1] = add_final(res[-1], 'ㄴ')
            else:
                res.append('은')
            continue
        if c == 'ッ':
            # geminate: before k-sounds -> final ㄱ, before p -> ㅂ, before t/s -> ㅅ
            if nxt and res and res[-1] != ' ':
                f = {'ㅋ':'ㄱ','ㄱ':'ㄱ','ㅍ':'ㅂ','ㅂ':'ㅂ'}.get(nxt[0])
                if f and add_final(res[-1], f):
                    res[-1] = add_final(res[-1], f)
                    # bare k after geminate at word end: ロック -> 록
                    if nxt[2] == 'ク' and (k + 2 >= n or U[k+2][0] in ('・','　',' ')):
                        U[k+1] = ['skip', None, '']
            continue
        if c == 'skip':
            continue
        if c == '?':
            continue
        prev = res[-1] if res and res[-1] != ' ' else None
        # ル before consonant / at end -> final ㄹ on previous
        if src == 'ル' and prev and (at_end or (nxt and nxt[0] not in ('ㅇ', 'ー', 'ン', 'ッ') and nxt[1] is not None)):
            f = add_final(prev, 'ㄹ')
            if f and k > 0:
                res[-1] = f; continue
        # ム / ン at word end -> final ㅁ
        if src == 'ム' and prev and at_end:
            f = add_final(prev, 'ㅁ')
            if f: res[-1] = f; continue
        # bare consonant vowel: ト/ド/ク/グ/フ/ブ/プ at end or before consonant -> ㅡ
        first = (k == 0 or U[k-1][0] in ('・', '　', ' '))
        if first and nxt and nxt[2] and nxt[2][0] in 'ラリルレロ':
            first = False
        if src in ('ト','ド') and not first and (at_end or (nxt and nxt[1] is not None and nxt[0] != 'ㅇ')):
            v = 'ㅡ'
        if src in ('ク','グ','フ','ブ','プ') and not first and (at_end or (nxt and nxt[1] is not None and nxt[0] not in ('ㅇ',))):
            v = 'ㅡ'
        res.append(compose(c, v))
    out = ''.join(res).strip()
    while '  ' in out: out = out.replace('  ', ' ')
    return out

if __name__ == '__main__':
    import sys
    for w in sys.argv[1:]:
        print(w, translit(w))
