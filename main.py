#!/usr/bin/env python3
"""THE WORLD IN ONE DAY - Sunday, 22 November 2026.

Draws a one-page newspaper front page summing up the world news of
22 November 2026. Python standard library only, no network, no PIL:
the PNG encoder is written by hand (struct + zlib).

Deterministic: no time, no randomness, no dict-order dependence in the
output; fixed zlib level; no timestamp chunks in the PNG.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (253, 250, 242)
INK = (17, 17, 17)
GREY = (90, 90, 90)
RED = (178, 34, 34)
BLUE = (31, 78, 121)
ORANGE = (214, 106, 20)
GREEN = (30, 132, 73)
GOLD = (176, 141, 26)
LIGHT = (238, 232, 218)
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 bits, written as strings of '0'/'1'.
# Uppercase letters, digits and common punctuation only; all copy is
# written in uppercase so this set covers everything on the page.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
}


def text_width(text, scale):
    """Pixel width of text at the given scale (1 blank column between glyphs)."""
    return len(text) * (6 * scale) - scale if text else 0


# ---------------------------------------------------------------- PNG encoder
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(pixels, width, height):
    """pixels: bytes of RGB rows, top to bottom. Returns PNG bytes."""
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)  # filter: none
        raw += pixels[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, width, height, bg):
        self.w = width
        self.h = height
        self.buf = bytearray(bg * (width * height))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham line with square brush of side `thick`."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.rect(x - thick // 2, y - thick // 2, thick, thick, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, color, fill=False, thick=1):
        if fill:
            for yy in range(-r, r + 1):
                half = int((r * r - yy * yy) ** 0.5)
                self.rect(cx - half, cy + yy, 2 * half + 1, 1, color)
            return
        x, y, d = 0, r, 1 - r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx + y, cy + x),
                           (cx - x, cy + y), (cx - y, cy + x),
                           (cx + x, cy - y), (cx + y, cy - x),
                           (cx - x, cy - y), (cx - y, cy - x)):
                self.rect(px - thick // 2, py - thick // 2, thick, thick, color)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1

    def ellipse(self, cx, cy, rx, ry, color, thick=1):
        """Outline ellipse by sampling angles (fine enough to look solid)."""
        import math
        steps = max(48, int(2 * math.pi * max(rx, ry)))
        prev = None
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            px = int(round(cx + rx * math.cos(a)))
            py = int(round(cy + ry * math.sin(a)))
            if prev is not None:
                self.line(prev[0], prev[1], px, py, color, thick)
            prev = (px, py)

    def triangle(self, pts, color):
        """Filled triangle, scanline fill."""
        pts = sorted(pts, key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = pts
        if y0 == y2:
            return
        for y in range(y0, y2 + 1):
            xs = []
            for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x0, y0), (x2, y2))):
                if ay == by:
                    continue
                if min(ay, by) <= y <= max(ay, by):
                    xs.append(ax + (bx - ax) * (y - ay) / (by - ay))
            if len(xs) >= 2:
                xa, xb = int(min(xs)), int(max(xs))
                self.rect(xa, y, xb - xa + 1, 1, color)

    # -- text -------------------------------------------------------------
    def glyph(self, x, y, ch, scale, color):
        rows = FONT.get(ch)
        if rows is None:
            rows = FONT["?"]
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit == "1":
                    self.rect(x + c * scale, y + r * scale, scale, scale, color)

    def text(self, x, y, s, scale, color):
        for i, ch in enumerate(s):
            self.glyph(x + i * 6 * scale, y, ch, scale, color)

    def text_center(self, x, y, w, s, scale, color):
        tw = text_width(s, scale)
        self.text(x + (w - tw) // 2, y, s, scale, color)


def wrap(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = word if not cur else cur + " " + word
            if text_width(trial, scale) <= max_width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


# ---------------------------------------------------------------- illustrations
# Each draws a small geometric scene inside the story's picture band.
# (cx, cy) is the centre of the band; all art is simple shapes on purpose.

def art_globe(cv, cx, cy):
    # COP31: the Earth, with a warming sun and a rising red line.
    cv.circle(cx, cy, 34, BLUE, fill=False, thick=3)
    cv.ellipse(cx, cy, 34, 13, BLUE, 2)
    cv.ellipse(cx, cy, 13, 34, BLUE, 2)
    cv.line(cx - 34, cy, cx + 34, cy, BLUE, 2)
    cv.circle(cx + 52, cy - 26, 12, ORANGE, fill=True)
    for dx, dy in ((0, -18), (13, -13), (18, 0), (13, 13),
                   (0, 18), (-13, 13), (-18, 0), (-13, -13)):
        cv.line(cx + 52 + dx * 2 // 3, cy - 26 + dy * 2 // 3,
                cx + 52 + dx, cy - 26 + dy, ORANGE, 2)
    # rising temperature arrow
    cv.line(cx - 62, cy + 30, cx - 30, cy + 6, RED, 3)
    cv.line(cx - 30, cy + 6, cx - 30, cy + 16, RED, 3)
    cv.line(cx - 30, cy + 6, cx - 40, cy + 6, RED, 3)


def art_radar(cv, cx, cy):
    # Iran / Bahrain: radar sweeps and a missile, with a blast star.
    for r in (16, 26, 36):
        cv.circle(cx - 18, cy, r, GREEN, fill=False, thick=2)
    cv.line(cx - 18, cy, cx + 12, cy - 26, GREEN, 2)
    # missile
    cv.triangle([(cx + 26, cy - 30), (cx + 40, cy - 6), (cx + 12, cy - 6)], RED)
    cv.rect(cx + 22, cy - 8, 6, 12, RED)
    cv.rect(cx + 32, cy - 8, 6, 12, RED)
    # blast star
    bx, by = cx + 56, cy + 18
    for dx, dy in ((0, -14), (10, -10), (14, 0), (10, 10),
                   (0, 14), (-10, 10), (-14, 0), (-10, -10)):
        cv.line(bx, by, bx + dx, by + dy, ORANGE, 3)
    cv.circle(bx, by, 5, RED, fill=True)


def art_trade(cv, cx, cy):
    # EU - Indonesia: two flags, an arrow of trade between them.
    # EU flag: blue field, ring of gold dots.
    cv.rect(cx - 78, cy - 22, 52, 36, BLUE)
    for i in range(8):
        import math
        a = 2 * math.pi * i / 8
        cv.circle(cx - 52 + int(11 * math.cos(a)),
                  cy - 4 + int(11 * math.sin(a)), 2, GOLD, fill=True)
    # Indonesia flag: red over white.
    cv.rect(cx + 26, cy - 22, 52, 18, RED)
    cv.rect(cx + 26, cy - 4, 52, 18, WHITE)
    cv.rect(cx + 26, cy - 22, 52, 36, INK)  # placeholder overwritten below
    cv.rect(cx + 27, cy - 21, 50, 34, RED)
    cv.rect(cx + 27, cy - 3, 50, 16, WHITE)
    # trade arrow between the flags
    cv.line(cx - 22, cy - 4, cx + 20, cy - 4, GREEN, 4)
    cv.line(cx + 20, cy - 4, cx + 10, cy - 12, GREEN, 4)
    cv.line(cx + 20, cy - 4, cx + 10, cy + 4, GREEN, 4)
    cv.text_center(cx - 90, cy + 26, 180, "98.5% TARIFFS CUT", 1, INK)


def art_hospital(cv, cx, cy):
    # Bolsonaro: hospital cross and a heartbeat line.
    cv.circle(cx - 28, cy, 30, RED, fill=False, thick=3)
    cv.rect(cx - 38, cy - 8, 20, 16, RED)
    cv.rect(cx - 33, cy - 13, 10, 26, RED)
    pts = [(cx + 6, cy + 6), (cx + 20, cy + 6), (cx + 28, cy - 16),
           (cx + 36, cy + 20), (cx + 44, cy - 6), (cx + 52, cy + 6),
           (cx + 66, cy + 6)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        cv.line(ax, ay, bx, by, BLUE, 3)


def art_fire(cv, cx, cy):
    # Cikande candy factory fire: flames over a factory block.
    cv.rect(cx - 70, cy + 6, 140, 28, GREY)
    cv.rect(cx - 70, cy + 6, 140, 4, INK)
    cv.rect(cx - 58, cy + 14, 14, 12, INK)
    cv.rect(cx - 34, cy + 14, 14, 12, INK)
    cv.rect(cx - 10, cy + 14, 14, 12, INK)
    cv.rect(cx + 14, cy + 14, 14, 12, INK)
    cv.rect(cx + 38, cy + 14, 14, 12, INK)
    cv.rect(cx + 52, cy - 14, 10, 22, GREY)
    cv.circle(cx + 57, cy - 16, 4, GREY, fill=True)
    # flames
    cv.triangle([(cx - 52, cy + 6), (cx - 34, cy - 34), (cx - 16, cy + 6)], ORANGE)
    cv.triangle([(cx - 24, cy + 6), (cx - 2, cy - 44), (cx + 20, cy + 6)], RED)
    cv.triangle([(cx + 8, cy + 6), (cx + 30, cy - 30), (cx + 52, cy + 6)], ORANGE)
    cv.triangle([(cx - 14, cy + 6), (cx - 2, cy - 18), (cx + 10, cy + 6)], GOLD)


def art_scales(cv, cx, cy):
    # Bayer / Roundup: scales of justice over a weedkiller spray bottle.
    cv.line(cx, cy - 30, cx, cy + 28, INK, 3)
    cv.line(cx - 44, cy - 26, cx + 44, cy - 26, INK, 3)
    cv.circle(cx, cy - 34, 5, GOLD, fill=True)
    for sx in (-44, 44):
        cv.line(sx + cx, cy - 26, sx + cx - 12, cy + 2, INK, 2)
        cv.line(sx + cx, cy - 26, sx + cx + 12, cy + 2, INK, 2)
        cv.triangle([(sx + cx - 16, cy + 2), (sx + cx + 16, cy + 2),
                     (sx + cx, cy + 16)], GOLD)
    cv.line(cx - 14, cy + 28, cx + 14, cy + 28, INK, 3)
    # spray bottle at right, clear of the scales
    cv.rect(cx + 66, cy - 2, 18, 30, GREEN)
    cv.rect(cx + 70, cy - 10, 10, 8, GREEN)
    cv.line(cx + 70, cy - 10, cx + 58, cy - 18, GREEN, 2)


# ---------------------------------------------------------------- stories
# (kicker, headline, body, illustration)
STORIES = [
    ("CLIMATE - ANTALYA, TURKEY",
     "COP31 TALKS GO INTO OVERTIME",
     "CLIMATE NEGOTIATIONS ENTER A SECOND DAY OF OVERTIME AS NATIONS "
     "REMAIN DEADLOCKED OVER PHASING OUT FOSSIL FUELS.",
     art_globe),
    ("MIDDLE EAST - BAHRAIN",
     "IRAN STRIKES US BASES IN BAHRAIN",
     "IRAN SAYS IT HIT US AIR DEFENCE RADARS AT AL-RIFFA AND AWALI AIR "
     "BASES. BAHRAIN REPORTS DAMAGE TO CIVILIAN SITES AS TENSIONS RISE "
     "IN THE STRAIT OF HORMUZ.",
     art_radar),
    ("TRADE - BRUSSELS / JAKARTA",
     "EU AND INDONESIA SIGN TRADE DEAL",
     "A DECADE OF TALKS ENDS WITH A DEAL SCRAPPING 98.5% OF TARIFFS "
     "BETWEEN THE EUROPEAN UNION AND INDONESIA.",
     art_trade),
    ("BRAZIL - BRASILIA",
     "BOLSONARO IN INTENSIVE CARE",
     "BRAZIL'S FORMER PRESIDENT IS IN INTENSIVE CARE WITH A BOWEL "
     "OBSTRUCTION.",
     art_hospital),
    ("INDONESIA - CIKANDE, BANTEN",
     "CANDY FACTORY FIRE KILLS 3",
     "AT LEAST 3 PEOPLE ARE DEAD AND 36 MISSING AFTER A FIRE AT A "
     "CANDY FACTORY IN CIKANDE, BANTEN.",
     art_fire),
    ("COURTS - UNITED STATES",
     "BAYER 7.25 BILLION ROUNDUP DEAL APPROVED",
     "A JUDGE APPROVES A 7.25 BILLION USD SETTLEMENT OVER ROUNDUP "
     "WEEDKILLER CANCER CLAIMS FROM THOUSANDS OF NON-HODGKIN LYMPHOMA "
     "PATIENTS.",
     art_scales),
]

TICKER_1 = ("ALSO TODAY: NEPAL PM BALENDRA SHAH BEGINS A TWO-DAY "
            "STATE VISIT TO INDIA")
TICKER_2 = ("CRICKET: INDIA 720/9, LEAD NZ BY 352  |  "
            "FBI DATABASE HACKED, TRUMP CONFIRMS")


def draw_story(cv, x, y, w, h, story):
    kicker, headline, body, art = story
    # frame
    cv.rect(x, y, w, 2, INK)
    cv.rect(x, y + h - 2, w, 2, INK)
    cv.rect(x, y, 2, h, INK)
    cv.rect(x + w - 2, y, 2, h, INK)
    # kicker
    cv.text(x + 12, y + 10, kicker, 1, RED)
    # picture band
    band_y = y + 28
    cv.rect(x + 10, band_y, w - 20, 76, LIGHT)
    art(cv, x + w // 2, band_y + 38)
    # headline (up to 2 lines, scale 2)
    hy = band_y + 88
    for i, line in enumerate(wrap(headline, 2, w - 24)[:2]):
        cv.text(x + 12, hy + i * 19, line, 2, INK)
    # divider
    cv.hline(x + 12, hy + 40, w - 24, GREY, 1)
    # body (scale 2)
    by = hy + 48
    for i, line in enumerate(wrap(body, 2, w - 24)):
        cv.text(x + 12, by + i * 15, line, 2, INK)


def draw_page():
    cv = Canvas(W, H, PAPER)

    # ---- masthead ------------------------------------------------------
    cv.hline(36, 26, W - 72, INK, 3)
    cv.text_center(0, 44, W, "THE WORLD IN ONE DAY", 6, INK)
    cv.text_center(0, 100, W, "SUNDAY, 22 NOVEMBER 2026", 3, INK)
    cv.text_center(0, 128, W, "THE DAY'S WORLD NEWS IN ONE PAGE", 1, GREY)
    cv.hline(36, 148, W - 72, INK, 3)
    cv.hline(36, 154, W - 72, INK, 1)

    # ---- story grid: 2 columns x 3 rows --------------------------------
    col_w = 464
    row_h = 246
    xs = (36, 528)
    ys = (168, 428, 688)
    for i, story in enumerate(STORIES):
        draw_story(cv, xs[i % 2], ys[i // 2], col_w, row_h, story)

    # ---- bottom ticker --------------------------------------------------
    ty = 950
    cv.rect(36, ty, W - 72, 56, INK)
    cv.text(52, ty + 9, TICKER_1, 2, WHITE)
    cv.text(52, ty + 32, TICKER_2, 2, WHITE)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = draw_page()
    png = encode_png(bytes(cv.buf), W, H)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)
    print(f"wrote {path}: {len(png)} bytes, {W}x{H}")


if __name__ == "__main__":
    main()
