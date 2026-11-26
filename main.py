#!/usr/bin/env python3
"""THE WORLD TODAY -- a one-image front page for Thursday 26 November 2026.

Generates a 1024x1024 PNG newspaper front page that sums up the day's
world news.  Everything is drawn by this program itself: a small hand-made
5x7 pixel font, a framebuffer, rules, boxes and a hand-drawn chart, and a
hand-rolled PNG encoder.  No downloaded images, no network access, no
external fonts or image files, only the Python standard library.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py
Output: <MAKEFUN_OUTPUT_DIR>/entry.png  (deterministic)
"""

import binascii
import os
import struct
import sys
import zlib

# ---------------------------------------------------------------- palette
PAPER = (250, 247, 238)   # warm newsprint
INK = (20, 20, 20)        # near-black type
RED = (158, 27, 27)       # kicker red
GREY = (112, 106, 94)     # secondary type
PALE = (233, 228, 215)    # panel fill
RULE = (60, 56, 48)       # rule grey

PAGE_W, PAGE_H = 1024, 1024

# ------------------------------------------------- hand-made 5x7 pixel font
# Each glyph is 7 rows of 5 bits.  Uppercase only; all copy is uppercased
# before rendering, which suits a newspaper front page.
GLYPHS = {
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
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
}

BLANK = ("00000",) * 7
CHAR_W, CHAR_H, CHAR_ADV = 5, 7, 6  # glyph cell is 5 wide, advance 6


def normalise(text):
    """Fold copy into the characters the font can draw."""
    table = {
        "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2026": ".", "\u00a0": " ",
    }
    for src, dst in table.items():
        text = text.replace(src, dst)
    return text.upper()


# ------------------------------------------------------------------- canvas
class Page:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bg * (w * h))

    def px(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(colour)

    def fill(self, x, y, w, h, colour):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        row = bytes(colour) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, w, colour, thick=1):
        self.fill(x, y, w, thick, colour)

    def vline(self, x, y, h, colour, thick=1):
        self.fill(x, y, thick, h, colour)

    def frame(self, x, y, w, h, colour, thick=1):
        self.hline(x, y, w, colour, thick)
        self.hline(x, y + h - thick, w, colour, thick)
        self.vline(x, y, h, colour, thick)
        self.vline(x + w - thick, y, h, colour, thick)

    def line(self, x0, y0, x1, y1, colour, thick=1):
        """Bresenham line, with a square brush of `thick` pixels."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        half = thick // 2
        while True:
            self.fill(x - half, y - half, thick, thick, colour)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    # ------------------------------------------------------------- text
    def text_width(self, text, scale):
        return len(normalise(text)) * CHAR_ADV * scale - scale

    def draw_text(self, x, y, text, scale, colour):
        cx = x
        for ch in normalise(text):
            glyph = GLYPHS.get(ch, BLANK)
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == "1":
                        self.fill(cx + col * scale, y + row * scale,
                                  scale, scale, colour)
            cx += CHAR_ADV * scale
        return cx

    def text_centred(self, cx, y, text, scale, colour):
        w = self.text_width(text, scale)
        return self.draw_text(cx - w // 2, y, text, scale, colour)

    def text_right(self, right, y, text, scale, colour):
        w = self.text_width(text, scale)
        return self.draw_text(right - w, y, text, scale, colour)

    def wrap(self, text, max_w, scale):
        """Greedy word wrap; returns a list of lines that fit max_w px."""
        limit = max_w // (CHAR_ADV * scale)
        words, lines, cur = normalise(text).split(), [], ""
        for word in words:
            trial = (cur + " " + word).strip() if cur else word
            if len(trial) <= limit:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                # a single over-long word is hard-split
                while len(word) > limit:
                    lines.append(word[:limit])
                    word = word[limit:]
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def paragraph(self, x, y, text, max_w, scale, colour, leading=None):
        leading = leading if leading is not None else CHAR_H * scale + 6
        for line in self.wrap(text, max_w, scale):
            self.draw_text(x, y, line, scale, colour)
            y += leading
        return y


# -------------------------------------------------------------- PNG writer
def write_png(page, path):
    raw = bytearray()
    stride = page.w * 3
    for yy in range(page.h):
        raw.append(0)  # filter: none
        raw += page.buf[yy * stride:(yy + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)
        return out

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", page.w, page.h,
                                      8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)

# ------------------------------------------------------------ the day's news
# Headlines and facts as reported on Thursday 26 November 2026.
# Sources: BBC, Reuters (via SimpleLife.news), AP reporting syndicated
# in the 26 Nov 2026 school-assembly / daily-news round-ups.
LEAD = {
    "kicker": "LEAD STORY - TRADE",
    "headline": ["US UNVEILS NEW TARIFFS", "ON CHINA, JAPAN AND EU"],
    "body": ("Washington unveils a sweeping new tariff plan covering "
             "China, Japan, the European Union and more, rattling global "
             "markets on Thanksgiving Day."),
}

STORIES = [
    {
        "kicker": "MIDDLE EAST - ENERGY",
        "headline": "HOUTHIS CLAIM STRIKE ON SAUDI REFINERY AS BRENT TOPS $94",
        "body": ("Yemen's Houthis say they hit Saudi Arabia's Ras "
                 "Tanura refinery, causing fires, as Brent crude climbs "
                 "above $94."),
    },
    {
        "kicker": "MIDDLE EAST - GAZA",
        "headline": "ISRAEL STRIKES IN GAZA; CEASEFIRE UNDER STRAIN",
        "body": ("An Israeli strike kills Hamas security chief Mohammad "
                 "Abuelouf, his wife and two children, Gaza medics say."),
    },
    {
        "kicker": "SPACE",
        "headline": "PAKISTAN'S FIRST ASTRONAUT HEADS FOR TIANGONG",
        "body": ("Muhammad Zeeshan Ali flies aboard China's Shenzhou-24, "
                 "the first foreign astronaut on the Tiangong station."),
    },
    {
        "kicker": "UKRAINE WAR",
        "headline": "RUSSIA'S OWN FIGURES: NEARLY 500,000 LOST IN WAR",
        "body": ("Moscow's own figures show Russia has lost nearly half "
                 "a million people in the Ukraine war, the BBC reports."),
    },
]

BRIEFS = [
    ("SCIENCE", "BepiColombo reaches Mercury orbit after an eight-year "
                "journey; close-up images reveal a stadium-sized crater."),
    ("EGYPT", "Fuel tanker crash ignites a massive fire on a Cairo "
             "highway, killing at least 30 people."),
    ("MUSIC", "Duran Duran guitarist Andy Taylor dies aged 65."),
    ("ASIA", "Bangladesh raises the minimum wage for garment workers "
            "by 36%. India marks 18 years since the 26/11 Mumbai attacks."),
]

BRENT_WEEK = [62, 66, 65, 71, 78, 84, 89, 94]  # $/barrel, week to 26 Nov


# ------------------------------------------------------------------- layout
def build_page():
    p = Page(PAGE_W, PAGE_H, PAPER)
    M = 40                      # side margin inside the frame
    R = PAGE_W - M              # right edge of the text column

    # -- double frame -------------------------------------------------
    p.frame(14, 14, PAGE_W - 28, PAGE_H - 28, INK, 3)
    p.frame(22, 22, PAGE_W - 44, PAGE_H - 44, RULE, 1)

    # -- masthead -----------------------------------------------------
    p.text_centred(PAGE_W // 2, 44, "THE WORLD TODAY", 6, INK)
    p.hline(M, 104, R - M, INK, 2)
    # dateline row: volume line left, date centre, price right
    p.draw_text(M, 116, "VOL. I - NO. 330", 1, GREY)
    p.text_centred(PAGE_W // 2, 116, "THURSDAY 26 NOVEMBER 2026", 2, INK)
    p.text_right(R, 116, "PRICE: ONE IMAGE", 1, GREY)
    p.hline(M, 140, R - M, INK, 3)
    p.hline(M, 146, R - M, INK, 1)

    # -- lead story + oil chart ---------------------------------------
    lead_x, lead_y = M, 168
    chart_x, chart_y = 668, 168
    chart_w, chart_h = R - chart_x, 168
    p.draw_text(lead_x, lead_y, LEAD["kicker"], 2, RED)
    hy = lead_y + 28
    for line in LEAD["headline"]:
        p.draw_text(lead_x, hy, line, 3, INK)
        hy += 30
    p.paragraph(lead_x, hy + 10, LEAD["body"], chart_x - lead_x - 28,
                2, INK, leading=28)

    # chart panel: Brent crude climbing to $94
    p.fill(chart_x, chart_y, chart_w, chart_h, PALE)
    p.frame(chart_x, chart_y, chart_w, chart_h, INK, 2)
    p.draw_text(chart_x + 14, chart_y + 12, "BRENT CRUDE", 2, INK)
    p.text_right(chart_x + chart_w - 14, chart_y + 12, "$94 / BARREL", 2, RED)
    plot_x, plot_y = chart_x + 16, chart_y + 46
    plot_w, plot_h = chart_w - 32, chart_h - 46 - 30
    p.hline(plot_x, plot_y + plot_h, plot_w, RULE, 1)
    pts = []
    for i, v in enumerate(BRENT_WEEK):
        px = plot_x + int(i * plot_w / (len(BRENT_WEEK) - 1))
        py = plot_y + plot_h - int((v - 55) * plot_h / 45)
        pts.append((px, py))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        p.line(x0, y0, x1, y1, RED, 3)
    for px, py in pts:
        p.fill(px - 3, py - 3, 7, 7, RED)
    p.draw_text(plot_x, plot_y + plot_h + 8, "WEEK TO 26 NOV", 1, GREY)
    p.text_right(chart_x + chart_w - 16, plot_y + plot_h + 8,
                 "UP FROM $62", 1, GREY)

    # -- rule under the lead ------------------------------------------
    p.hline(M, 352, R - M, INK, 2)

    # -- 2 x 2 story grid ---------------------------------------------
    col_w = (R - M - 24) // 2
    col_x = [M, M + col_w + 24]
    row_y = [372, 572]
    cell_h = 180
    for idx, story in enumerate(STORIES):
        cx = col_x[idx % 2]
        cy = row_y[idx // 2]
        p.draw_text(cx, cy, story["kicker"], 2, RED)
        hy = cy + 26
        for line in p.wrap(story["headline"], col_w, 2):
            p.draw_text(cx, hy, line, 2, INK)
            hy += 26
        p.paragraph(cx, hy + 8, story["body"], col_w, 2, GREY, leading=26)
        if idx % 2 == 0:
            p.vline(cx + col_w + 12, cy, cell_h, RULE, 1)
        if idx < 2:
            p.hline(M, cy + cell_h + 8, R - M, RULE, 1)

    # -- briefs band ----------------------------------------------------
    by = 776
    p.hline(M, by, R - M, INK, 2)
    p.draw_text(M, by + 12, "IN BRIEF", 2, INK)
    p.text_right(R, by + 12, "AROUND THE WORLD IN FOUR LINES", 1, GREY)
    bx = [M, M + col_w + 24]
    byy = [by + 44, by + 104]
    for idx, (tag, text) in enumerate(BRIEFS):
        cx = bx[idx % 2]
        cy = byy[idx // 2]
        p.fill(cx, cy + 3, 10, 10, RED)
        p.paragraph(cx + 18, cy, tag + " - " + text, col_w - 18,
                    1, INK, leading=12)

    # -- footer ---------------------------------------------------------
    p.hline(M, 928, R - M, INK, 1)
    p.text_centred(PAGE_W // 2, 942,
                   "SOURCES: BBC, REUTERS, AP - ALL STORIES REPORTED "
                   "26 NOVEMBER 2026", 1, GREY)
    p.text_centred(PAGE_W // 2, 958,
                   "DRAWN ENTIRELY BY CODE - NO PHOTOGRAPHS", 1, GREY)
    return p


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    page = build_page()
    size = write_png(page, path)
    print("Wrote %s (%d bytes, %dx%d)" % (path, size, PAGE_W, PAGE_H))
    return 0


if __name__ == "__main__":
    sys.exit(main())
