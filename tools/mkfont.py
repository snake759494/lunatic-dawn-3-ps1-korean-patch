"""Build Korean STRING1.TH4 (2 x 2bpp sheets of 21x21 12px cells) + glyph code table.

Layout of the 882-entry table (sorted by u16 SJIS code, binary searched by the game):
  index 0..440   -> low 2 bits of STRING1.TH4  (palette 0..7)
  index 441..881 -> high 2 bits                 (palette 8..15)
Pixel values: 0 = transparent, 1 = shadow, 2 = mid, 3 = body.
"""
import os, sys, json, struct
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from ld3 import WORK, EXT

FONT = os.path.join(os.path.dirname(__file__), 'Galmuri11.ttf')
N = 882; PER = 441; COLS = 21; CELL = 12
ORIG_TAB = 0x54424  # file offset of glyph table in SLPS_017.49

def orig_table():
    b = open(os.path.join(EXT, 'SLPS_017.49'), 'rb').read()
    return list(struct.unpack_from('<%dH' % N, b, ORIG_TAB))

def orig_cell(idx):
    """2bpp cell of original font as 12x12 list"""
    d = open(os.path.join(EXT, 'ETC/STRING1.TH4'), 'rb').read()
    layer, k = divmod(idx, PER); r, c = divmod(k, COLS)
    out = []
    for y in range(CELL):
        row = []
        for x in range(CELL):
            X = c * CELL + x; Y = r * CELL + y
            n = (d[Y * 128 + X // 2] >> (4 * (X & 1))) & 15
            row.append((n >> (2 * layer)) & 3)
        out.append(row)
    return out

_font = None
def render(ch, dx=0, dy=0):
    """Galmuri11 at its native 12px size, 1-bit, + drop shadow (right/down)."""
    global _font
    if _font is None:
        _font = ImageFont.truetype(FONT, 12)
    im = Image.new('1', (CELL + 4, CELL + 4), 0)
    d = ImageDraw.Draw(im); d.fontmode = '1'
    d.text((dx, dy), ch, font=_font, fill=1)
    px = im.load()
    body = [[px[x, y] for x in range(CELL)] for y in range(CELL)]
    out = [[0] * CELL for _ in range(CELL)]
    for y in range(CELL):
        for x in range(CELL):
            if body[y][x]:
                out[y][x] = 3
            elif (x > 0 and body[y][x-1]) or (y > 0 and body[y-1][x]) or (x > 0 and y > 0 and body[y-1][x-1]):
                out[y][x] = 1
    return out

def bbox_check(ch):
    im = Image.new('1', (40, 40), 0); d = ImageDraw.Draw(im); d.fontmode = '1'
    d.text((10, 10), ch, font=ImageFont.truetype(FONT, 12), fill=1)
    return im.getbbox()

def build(entries):
    """entries: list of 882 (code, cell12x12) sorted by code. returns (th4 bytes, table bytes)"""
    assert len(entries) == N
    codes = [c for c, _ in entries]
    assert codes == sorted(codes) and len(set(codes)) == N, 'codes must be unique & sorted'
    th4 = bytearray(32768)
    for idx, (code, cell) in enumerate(entries):
        layer, k = divmod(idx, PER); r, c = divmod(k, COLS)
        for y in range(CELL):
            for x in range(CELL):
                v = cell[y][x] & 3
                if not v: continue
                X = c * CELL + x; Y = r * CELL + y
                th4[Y * 128 + X // 2] |= (v << (2 * layer)) << (4 * (X & 1))
    tab = struct.pack('<%dH' % N, *codes)
    return bytes(th4), tab

def preview(th4, path):
    im = Image.new('L', (512, 256))
    px = im.load()
    pal = [0, 70, 150, 255]
    for layer in range(2):
        for y in range(256):
            for x in range(256):
                n = (th4[y * 128 + x // 2] >> (4 * (x & 1))) & 15
                px[layer * 256 + x, y] = pal[(n >> (2 * layer)) & 3]
    im.resize((1024, 512), Image.NEAREST).save(path)
