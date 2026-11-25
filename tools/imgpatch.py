"""Graphics with Japanese text -> Korean.
TITLE.TIM: katakana subtitle 'ルナティックドーン III' (x 87..179, y 60..73) -> '루나틱 던 III' (Galmuri9, native 10px)
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import tim
from ld3 import rd, WORK

HERE = os.path.dirname(__file__)

def text_mask(text, font, size):
    f = ImageFont.truetype(os.path.join(HERE, font), size)
    im = Image.new('1', (200, 30), 0); d = ImageDraw.Draw(im); d.fontmode = '1'
    d.text((2, 2), text, font=f, fill=1)
    bb = im.getbbox(); return im.crop(bb)

def patch_title():
    d = bytearray(rd('TIM/TITLE.TIM')); t = tim.parse(bytes(d))
    po = t['pixoff']; W = 256
    def get(x, y): return (d[po + y * 128 + x // 2] >> (4 * (x & 1))) & 15
    def put(x, y, v):
        i = po + y * 128 + x // 2
        d[i] = (d[i] & (0xF0 if x & 1 == 0 else 0x0F)) | (v << (4 * (x & 1)))
    X0, X1, Y0, Y1 = 87, 180, 60, 74
    for y in range(Y0, Y1):
        for x in range(X0, X1): put(x, y, 0)
    m = text_mask('루나틱 던 III', 'Galmuri9.ttf', 10)
    w, h = m.size
    ox = X0 + (X1 - X0 - w) // 2; oy = 62 + (9 - h) // 2 if h < 9 else 62
    mp = m.load()
    body = set((ox + x, oy + y) for y in range(h) for x in range(w) if mp[x, y])
    # outline (index 1 dark) then body: top rows lighter (0xc), lower rows (0xa) like the original gradient
    for (x, y) in body:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                p = (x + dx, y + dy)
                if p not in body and get(*p) == 0: put(p[0], p[1], 1)
    ys = sorted(set(y for _, y in body)); ymid = (ys[0] + ys[-1]) / 2
    for (x, y) in body:
        put(x, y, 0xc if y <= ymid else 0xa)
    return bytes(d)

def patch_all():
    out = {'/TIM/TITLE.TIM': patch_title()}
    im = tim.toimg(tim.parse(out['/TIM/TITLE.TIM']))
    bg = Image.new('RGBA', im.size, (40, 40, 40, 255)); bg.paste(im, (0, 0), im)
    bg.resize((512, 224), Image.NEAREST).save(os.path.join(WORK, 'shots', 'title_ko.png'))
    return out

if __name__ == '__main__':
    patch_all()
