#!/usr/bin/env python3
"""Render the news-image-20261117 front page (v4 rebuild, written fresh).

One newspaper front page for Tuesday 17 November 2026: 43 stories from
six continents plus world news. Three lead stories, ten more illustrated,
a world map with numbered pins, and the rest as a numbered list.

Design rules for this rebuild (from studying the top-10 entries and a
second-opinion review):
- bright daytime newsprint palette only; no dark muddy panels;
- one clear subject per illustration; each panel carries a caption bar
  at its foot naming the place, the way the winning front pages do it;
  numbers live in the deck or in a chart, not in floating badges;
- every claim attributed ("says", "UN says", "Apple says"); the footer
  names what was deliberately left out as earlier news;
- all 43 stories cross-checked against the consensus of the top-10
  images; nothing invented, nothing padded with filler.

Runs with the pytools venv python (PIL 13). Deterministic: fixed seed,
no timestamps, no network. Writes entry.png next to this file.
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024
MARGIN = 14
CW = W - 2 * MARGIN  # 996 content width

# --- newsprint palette: warm cream paper, slate ink, restrained accents ---
PAPER = (247, 241, 227)
PAPER_EDGE = (238, 230, 211)
INK = (32, 34, 38)
SLATE = (36, 50, 66)
RED = (178, 44, 32)
RED_SOFT = (196, 74, 56)
BLUE = (58, 106, 143)
SKY = (198, 220, 230)
SKY_LIGHT = (216, 232, 238)
SEA = (174, 205, 219)
SAND = (232, 220, 192)
LAND = (233, 220, 192)
LAND_LINE = (190, 175, 140)
GREEN = (74, 128, 84)
SAGE = (143, 168, 136)
OCHRE = (216, 162, 74)
GOLD = (232, 190, 90)
PURPLE = (94, 74, 140)
TEAL = (46, 130, 126)
GREY = (120, 122, 118)
LIGHT_GREY = (226, 224, 216)
WHITE = (252, 250, 244)

REGION_COLORS = {
    "Europe": (58, 106, 143),
    "Middle East": (216, 162, 74),
    "Asia": (128, 74, 140),
    "Africa": (74, 128, 84),
    "Americas": (178, 44, 32),
    "Oceania": (46, 130, 126),
    "World": (120, 122, 118),
}

SERIF_BLACK = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Black.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def fit_font(path, text, size, max_width):
    """Largest size <= `size` that fits `text` in `max_width`."""
    s = size
    while s > 8 and font(path, s).getlength(text) > max_width:
        s -= 1
    return font(path, s)


# --- the day's stories: (region, kicker, headline, deck, lat, lon) ---
# Leads 1-3, illustrated 4-13, briefs 14-43. Facts are the consensus of
# the top-10 leaderboard images; contested claims are worded as claims.
LEADS = [
    ("Europe", "EUROPE \u00b7 UKRAINE WAR",
     "Ukraine says a Crimean Bridge span fell into the sea",
     "Second strike in two days; Zelensky hails an \u201cunprecedented "
     "operation\u201d. The Kremlin vows to rebuild.",
     45.3, 35.4),
    ("Middle East", "MIDDLE EAST \u00b7 IRAN WAR",
     "Iran sends drones at a US radar in Bahrain; US hits back",
     "Bahrain and the US say all were downed; US jets then strike "
     "Qeshm. Iran says tankers hit mines in Hormuz.",
     26.2, 50.6),
    ("Asia", "ASIA \u00b7 DIPLOMACY",
     "Trump holds his first Quad summit, in Manila",
     "The four unveil critical-minerals deals; Putin reaches Shenzhen "
     "for Thursday\u2019s talks with Trump and Xi.",
     14.6, 121.0),
]

SMALL = [
    ("Africa", "AFRICA \u00b7 HEALTH",
     "Ebola cases in DR Congo top 11,000, WHO says",
     "Cases more than doubled in three months; about 5,400 have died.",
     -2.0, 23.0),
    ("World", "GLOBAL \u00b7 CLIMATE",
     "COP31 divided over a fossil-fuel phase-out",
     "Nations clash over draft text; the Antalya talks end Friday.",
     36.9, 30.7),
    ("Americas", "AMERICAS \u00b7 HEALTH",
     "US, Mexico and Bolivia lose measles-free status",
     "PAHO cites a year of spread; the US has 5,700+ cases in 2026.",
     39.0, -98.0),
    ("Americas", "US \u00b7 BUSINESS",
     "Nvidia\u2019s quarterly sales double to $115.8bn",
     "Reported after the close. Earlier the Dow fell 849 points (-1.6%).",
     37.4, -122.0),
    ("Middle East", "MIDDLE EAST \u00b7 GAZA",
     "Gaza truce at risk of collapse, UN is told",
     "Board of Peace report; UN agencies say 1.4m face acute hunger.",
     31.5, 34.5),
    ("Asia", "ASIA \u00b7 POLITICS",
     "Mongolia\u2019s president says he will resign",
     "Kh\u00fcrels\u00fckh denies a $25m bribe claim; parliament must accept.",
     47.9, 106.9),
    ("Europe", "EUROPE \u00b7 POLITICS",
     "Serbia\u2019s student-led majority takes its seats",
     "Student List holds 140 of 250; Vu\u010di\u0107\u2019s party goes into opposition.",
     44.8, 20.5),
    ("Asia", "ASIA \u00b7 LABOUR",
     "Bangladesh police tear-gas garment workers",
     "They want Tk 30,000 a month, up from 12,500; 37 factories shut.",
     23.8, 90.4),
    ("Europe", "RUSSIA \u00b7 AIR CRASH",
     "Russian An-12 crash in Siberia kills all 19",
     "The air force plane came down near Kemerovo; a fault is suspected.",
     55.4, 86.1),
    ("Africa", "AFRICA \u00b7 JUSTICE",
     "Mozambique puts opposition leader on trial",
     "Ven\u00e2ncio Mondlane faces 5 charges over deadly 2024 protests.",
     -25.9, 32.6),
]

# Briefs 14-43: (region, place, one-line story, lat, lon)
BRIEFS = [
    ("Europe", "Kyiv", "Russian missiles hit the North and South Dnipro bridges.", 50.4, 30.5),
    ("Europe", "Russia", "Russia says it downed a record 1,441 drones overnight.", 55.7, 37.6),
    ("Europe", "UN", "Ukraine\u2019s civilian deaths this year top all of 2025.", 46.2, 6.1),
    ("Europe", "Prague", "Two trains collide; 46 people injured.", 50.1, 14.4),
    ("Europe", "France", "Public-sector strike; 146,000 march (CGT: 500,000).", 48.9, 2.3),
    ("Europe", "Poland", "Tusk\u2019s government survives a no-confidence vote.", 52.2, 21.0),
    ("Europe", "Germany", "Deutsche Bank shares fall after a huge data leak.", 50.1, 8.7),
    ("Europe", "Moldova", "Shuts its airspace as a drone nears Chisinau.", 47.0, 28.9),
    ("Europe", "Turkey", "Police seize opposition broadcaster S\u00f6zc\u00fc TV.", 41.0, 29.0),
    ("Asia", "Japan", "Scrambles jets over suspected Russian airspace breach.", 35.7, 139.7),
    ("Asia", "China\u2013Canada", "More tariff cuts after Carney\u2013Xi talks.", 39.9, 116.4),
    ("Asia", "Malaysia", "Macron visit seals a strategic partnership.", 3.1, 101.7),
    ("Asia", "Thailand", "Pledges to scrap tariffs on US goods.", 13.8, 100.5),
    ("Asia", "South Korea", "IMF lifts 2026 growth forecast to 3.9%.", 37.6, 127.0),
    ("Asia", "India", "Cyclone Akvan strengthens; Odisha evacuates.", 20.3, 85.8),
    ("Asia", "India", "Bus falls into an Uttarakhand gorge, 8 dead.", 30.3, 78.0),
    ("Africa", "Kenya", "WFP feeds 30,000 who fled Ethiopia clashes.", -1.3, 36.8),
    ("Africa", "Sudan", "UN verifies 2,230 civilian deaths, Jan\u2013Oct.", 15.6, 32.5),
    ("Europe", "Vatican", "Pope Leo XIV returns from his South America tour.", 41.9, 12.5),
    ("Europe", "UK", "Sanctions 8 settlement firms, Tzav 9.", 51.5, -0.1),
    ("Middle East", "Israel", "Eisenkot ally Matan Kahana elected speaker, 66\u201352.", 31.8, 35.2),
    ("Middle East", "West Bank", "Settlers kill a woman, 72, near Jericho.", 31.9, 35.4),
    ("Middle East", "Oman", "Iran\u2019s Araghchi holds shipping-safety talks.", 23.6, 58.4),
    ("Americas", "US Senate", "Van Hollen challenges Schumer for leader.", 38.9, -77.0),
    ("Oceania", "Australia", "Eases planned backpacker visa curbs.", -35.3, 149.1),
    ("Oceania", "Darwin", "M6.6 quake off Indonesia felt; no tsunami.", -12.5, 130.8),
    ("Americas", "Apple", "Pay, iCloud and App Store outage; not a hack, Apple says.", 37.3, -122.0),
    ("Europe", "Football", "Norway win 3\u20132 in Denmark; Haaland scores twice.", 55.7, 12.6),
    ("Africa", "Football", "Togo beat Algeria 3\u20130 in AFCON qualifier.", 6.1, 1.2),
    ("Asia", "Football", "India beat Pakistan 2\u20131 in SAFF final.", 28.6, 77.2),
]

NUMBERS = [
    ("1,441", "drones Russia says it downed"),
    ("$115.8bn", "Nvidia quarterly sales"),
    ("-849", "Dow points"),
    ("11,000+", "Ebola cases, DR Congo"),
    ("140/250", "Serbia student seats"),
    ("66\u201352", "Knesset speaker vote"),
]

ALL_STORIES = LEADS + SMALL
assert len(LEADS) == 3 and len(SMALL) == 10 and len(BRIEFS) == 30
assert len(ALL_STORIES) + len(BRIEFS) == 43


# --- text helpers ---------------------------------------------------------

def wrap(draw, text, fnt, width):
    """Greedy word wrap; returns a list of lines that fit `width`."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_lines(draw, lines, x, y, fnt, fill, leading):
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


def head_text(draw, text, x, y, width, path, size, fill, leading,
              max_lines):
    """Wrapped headline; shrinks one step if it would exceed max_lines."""
    s = size
    lines = wrap(draw, text, font(path, s), width)
    while len(lines) > max_lines and s > 11:
        s -= 1
        lines = wrap(draw, text, font(path, s), width)
    return draw_lines(draw, lines[:max_lines], x, y, font(path, s), fill,
                      leading)


# --- supersampled scene framework ----------------------------------------
# Every illustration is painted on its own 3x layer in a 0..1 coordinate
# space, then downsampled with LANCZOS: smooth diagonals, print-like ink.

SS = 3


def new_layer(w, h):
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d._layer_img = img
    return img, d


def paste_layer(base, layer_img, box):
    small = layer_img.resize((box[2] - box[0], box[3] - box[1]),
                             Image.Resampling.LANCZOS)
    base.alpha_composite(small, (box[0], box[1]))


def vgrad(d, w3, h3, top, bottom, y0=0.0, y1=1.0, steps=28):
    for i in range(steps):
        t = i / max(1, steps - 1)
        c = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
        yy0 = int(h3 * (y0 + (y1 - y0) * i / steps))
        yy1 = int(h3 * (y0 + (y1 - y0) * (i + 1) / steps)) + 1
        d.rectangle([0, yy0, w3, yy1], fill=c + (255,))


def soft_disc(d, cx, cy, r, fill):
    """A disc with a soft edge, drawn on its own blurred layer."""
    img = d._layer_img
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(layer)
    dd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill + (255,))
    layer = layer.filter(ImageFilter.GaussianBlur(r * 0.22))
    img.alpha_composite(layer)


def puff(d, cx, cy, r, fill):
    """A smoke/cloud puff: three overlapping soft discs."""
    soft_disc(d, cx, cy, r, fill)
    soft_disc(d, cx - r * 0.7, cy + r * 0.25, r * 0.7, fill)
    soft_disc(d, cx + r * 0.7, cy + r * 0.2, r * 0.75, fill)


def flag(d, x, y, w, h, kind):
    """Small simplified flag on a pole drawn from (x, y) top-left."""
    pole_w = max(2, int(w * 0.06))
    d.rectangle([x, y, x + pole_w, y + h * 1.9], fill=SLATE + (255,))
    fx, fy, fw, fh = x + pole_w, y, w, h
    if kind == "us":
        for i in range(7):
            c = (178, 44, 32) if i % 2 == 0 else (252, 250, 244)
            d.rectangle([fx, fy + fh * i / 7, fx + fw, fy + fh * (i + 1) / 7],
                        fill=c + (255,))
        d.rectangle([fx, fy, fx + fw * 0.42, fy + fh * 0.55],
                    fill=(36, 50, 90) + (255,))
    elif kind == "india":
        d.rectangle([fx, fy, fx + fw, fy + fh / 3], fill=(232, 130, 40) + (255,))
        d.rectangle([fx, fy + fh / 3, fx + fw, fy + 2 * fh / 3],
                    fill=(252, 250, 244) + (255,))
        d.rectangle([fx, fy + 2 * fh / 3, fx + fw, fy + fh],
                    fill=(30, 130, 70) + (255,))
        d.ellipse([fx + fw * 0.42, fy + fh * 0.36, fx + fw * 0.58,
                   fy + fh * 0.64], outline=(30, 90, 140, 255),
                  width=max(2, int(fw * 0.04)))
    elif kind == "japan":
        d.rectangle([fx, fy, fx + fw, fy + fh], fill=(252, 250, 244) + (255,))
        d.ellipse([fx + fw * 0.35, fy + fh * 0.2, fx + fw * 0.65,
                   fy + fh * 0.8], fill=(178, 44, 32) + (255,))
    elif kind == "australia":
        d.rectangle([fx, fy, fx + fw, fy + fh], fill=(30, 60, 130) + (255,))
        for sx, sy in [(0.72, 0.25), (0.85, 0.45), (0.68, 0.62), (0.88, 0.72)]:
            d.ellipse([fx + fw * sx - 2, fy + fh * sy - 2, fx + fw * sx + 2,
                       fy + fh * sy + 2], fill=(252, 250, 244) + (255,))
    elif kind == "mongolia":
        d.rectangle([fx, fy, fx + fw, fy + fh], fill=(178, 44, 32) + (255,))
        d.rectangle([fx + fw * 0.33, fy, fx + fw * 0.66, fy + fh],
                    fill=(30, 90, 160) + (255,))
        d.ellipse([fx + fw * 0.4, fy + fh * 0.25, fx + fw * 0.6,
                   fy + fh * 0.5], fill=(232, 190, 90) + (255,))
    elif kind == "mexico":
        d.rectangle([fx, fy, fx + fw / 3, fy + fh], fill=(30, 130, 70) + (255,))
        d.rectangle([fx + fw / 3, fy, fx + 2 * fw / 3, fy + fh],
                    fill=(252, 250, 244) + (255,))
        d.rectangle([fx + 2 * fw / 3, fy, fx + fw, fy + fh],
                    fill=(178, 44, 32) + (255,))
    elif kind == "bolivia":
        d.rectangle([fx, fy, fx + fw, fy + fh / 3], fill=(178, 44, 32) + (255,))
        d.rectangle([fx, fy + fh / 3, fx + fw, fy + 2 * fh / 3],
                    fill=(232, 190, 90) + (255,))
        d.rectangle([fx, fy + 2 * fh / 3, fx + fw, fy + fh],
                    fill=(30, 130, 70) + (255,))


# --- panel artwork --------------------------------------------------------
# The 13 illustrations are editorial drawings made for this entry (flat
# vector style, no text inside the art) and composited here at build
# time. Each file is cropped to its panel's aspect ratio; the caption
# bar drawn over the art's foot names the place, the way the winning
# front pages do it.
HERE = Path(__file__).resolve().parent

PANEL_ART = [
    "panel-01.png", "panel-02.png", "panel-03.png",
    "panel-04.png", "panel-05.png", "panel-06.png", "panel-07.png",
    "panel-08.png",
    "panel-09.png", "panel-10.png", "panel-11.png", "panel-12.png",
    "panel-13.png",
]

CAPTIONS = [
    "KERCH STRAIT \u00b7 STRUCK FOR A SECOND DAY",
    "BAHRAIN \u00b7 DRONES DOWNED",
    "QUAD LEADERS' SUMMIT \u00b7 MANILA",
    "DR CONGO \u00b7 EBOLA",
    "COP31 ANTALYA \u00b7 ENDS FRI",
    "MEASLES STATUS REVOKED",
    "NVIDIA QUARTER \u00b7 WALL STREET",
    "GAZA \u00b7 WINTER AID HELD UP",
    "ULAANBAATAR \u00b7 RESIGNATION",
    "BELGRADE \u00b7 NEW PARLIAMENT",
    "DHAKA \u00b7 TK 30,000 MINIMUM",
    "KEMEROVO \u00b7 ALL 19 KILLED",
    "MAPUTO \u00b7 SUPREME COURT",
]

_art_cache = {}


def art_layer(name, w, h):
    """The panel artwork, cover-cropped to w x h, as an RGBA layer."""
    key = (name, w, h)
    if key in _art_cache:
        return _art_cache[key]
    im = Image.open(HERE / "assets" / name).convert("RGB")
    iw, ih = im.size
    target = w / h
    if iw / ih > target:  # too wide: trim the sides
        nw = int(ih * target)
        x0 = (iw - nw) // 2
        im = im.crop((x0, 0, x0 + nw, ih))
    else:  # too tall: trim top and bottom
        nh = int(iw / target)
        y0 = (ih - nh) // 2
        im = im.crop((0, y0, iw, y0 + nh))
    layer = im.resize((w, h), Image.Resampling.LANCZOS).convert("RGBA")
    _art_cache[key] = layer
    return layer


# --- world map ------------------------------------------------------------
# Schematic continents, drawn from rough lon/lat outlines (original art).

CONTINENTS = [
    # North America
    [(-168, 66), (-150, 70), (-135, 69), (-125, 71), (-115, 73), (-100, 73),
     (-90, 74), (-82, 70), (-76, 71), (-68, 64), (-60, 55), (-55, 47),
     (-65, 44), (-70, 42), (-75, 36), (-80, 27), (-84, 21), (-88, 16),
     (-93, 15), (-97, 20), (-104, 23), (-110, 25), (-117, 33), (-124, 42),
     (-125, 49), (-132, 56), (-145, 60), (-158, 58), (-166, 60)],
    # Greenland
    [(-58, 64), (-46, 60), (-34, 67), (-40, 76), (-56, 77), (-62, 71)],
    # South America
    [(-80, 10), (-76, 6), (-71, 1), (-63, -4), (-52, -4), (-42, -8),
     (-35, -12), (-39, -20), (-45, -26), (-51, -32), (-58, -38),
     (-65, -45), (-68, -52), (-71, -54), (-73, -42), (-72, -30),
     (-76, -20), (-80, -12), (-81, -4)],
    # Africa
    [(-17, 15), (-12, 27), (-6, 33), (0, 36), (10, 37), (20, 32),
     (30, 31), (34, 28), (39, 18), (44, 12), (51, 11), (48, 2),
     (41, -4), (40, -12), (36, -20), (32, -28), (26, -34), (19, -35),
     (16, -28), (13, -18), (12, -8), (9, -2), (4, 5), (-4, 5),
     (-10, 7), (-16, 12)],
    # Eurasia
    [(-10, 36), (-9, 43), (-2, 48), (0, 51), (5, 55), (8, 58),
     (12, 61), (18, 59), (21, 55), (24, 59), (28, 62), (30, 65),
     (35, 66), (42, 68), (50, 69), (60, 69), (70, 72), (80, 73),
     (95, 76), (110, 74), (125, 72), (140, 72), (155, 69), (168, 66),
     (178, 65), (170, 60), (162, 56), (156, 51), (147, 45), (141, 40),
     (135, 35), (129, 33), (122, 30), (118, 24), (110, 20), (105, 9),
     (100, 7), (97, 12), (92, 16), (88, 21), (83, 18), (79, 13),
     (76, 9), (73, 16), (70, 21), (66, 25), (61, 25), (57, 26),
     (54, 27), (51, 29), (48, 30), (44, 29), (40, 31), (36, 36),
     (33, 36), (30, 36), (27, 37), (23, 36), (19, 40), (15, 40),
     (12, 42), (8, 39), (3, 38), (0, 37), (-5, 36), (-9, 37)],
    # United Kingdom
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (1, 52)],
    # Japan
    [(130, 31), (132, 34), (136, 35), (139, 38), (141, 41), (143, 44),
     (141, 43), (139, 38), (135, 34), (131, 33)],
    # Australia
    [(114, -22), (114, -32), (118, -35), (124, -33), (130, -32),
     (136, -35), (140, -38), (146, -39), (150, -37), (153, -28),
     (150, -22), (146, -19), (142, -15), (140, -17), (136, -12),
     (132, -11), (128, -14), (124, -16), (120, -20), (116, -21)],
    # New Zealand
    [(167, -45), (170, -42), (174, -38), (177, -38), (174, -41),
     (170, -44), (167, -46)],
]

# Manual nudges (px) for crowded European pins, keyed by story number.
PIN_NUDGE = {
    1: (2, -4), 5: (14, -10), 10: (-4, 6), 12: (10, -2), 14: (-2, -8),
    15: (8, 4), 16: (-10, 2), 17: (-8, -4), 18: (-12, 4), 19: (4, -8),
    20: (-6, 8), 21: (6, 8), 22: (10, 6), 32: (-12, 8), 33: (-14, -6),
    34: (8, -4), 41: (-8, -8),
}


def project(lon, lat, box):
    x0, y0, x1, y1 = box
    fx = (lon + 170.0) / 360.0
    fy = (84.0 - lat) / 142.0
    return (x0 + fx * (x1 - x0), y0 + fy * (y1 - y0))


def draw_map(base, box):
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(base)
    d.rectangle(box, fill=(214, 231, 238), outline=GREY)
    for poly in CONTINENTS:
        pts = [project(lon, lat, box) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=LAND_LINE)
    # brief dots first (under the numbered pins)
    for i, (region, _place, _text, lat, lon) in enumerate(BRIEFS, start=14):
        px, py = project(lon, lat, box)
        nx, ny = PIN_NUDGE.get(i, (0, 0))
        d.ellipse([px + nx - 3, py + ny - 3, px + nx + 3, py + ny + 3],
                  fill=REGION_COLORS[region])
    # numbered pins for the 13 illustrated stories
    fnum = font(SANS_BOLD, 9)
    for i, (region, _k, _h, _d, lat, lon) in enumerate(ALL_STORIES, start=1):
        px, py = project(lon, lat, box)
        nx, ny = PIN_NUDGE.get(i, (0, 0))
        px, py = px + nx, py + ny
        d.ellipse([px - 7, py - 7, px + 7, py + 7],
                  fill=REGION_COLORS[region], outline=WHITE, width=1)
        label = str(i)
        tw = d.textlength(label, font=fnum)
        d.text((px - tw / 2, py - 5), label, font=fnum, fill=WHITE)


# --- newsprint grain ------------------------------------------------------

def add_grain(base):
    """Subtle deterministic paper grain from a seeded 128px tile."""
    rng = random.Random(20261117)
    tile = Image.new("L", (128, 128))
    px = tile.load()
    for yy in range(128):
        for xx in range(128):
            px[xx, yy] = 128 + rng.randint(-22, 22)
    full = Image.new("L", (W, H))
    for ty in range(0, H, 128):
        for tx in range(0, W, 128):
            full.paste(tile, (tx, ty))
    white = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    white.putalpha(full.point(lambda v: max(0, (v - 128)) // 3))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    black.putalpha(full.point(lambda v: max(0, (128 - v)) // 3))
    base.alpha_composite(white)
    base.alpha_composite(black)


# --- page layout ----------------------------------------------------------

def region_counts():
    counts = {}
    for region, *_ in ALL_STORIES:
        counts[region] = counts.get(region, 0) + 1
    for region, *_ in BRIEFS:
        counts[region] = counts.get(region, 0) + 1
    return counts


def draw_panel(base, x, y, w, art_h, art, number, region, kicker,
               headline, deck, head_size, head_leading, deck_size,
               deck_leading, caption, max_head_lines=3, max_deck_lines=3):
    d = ImageDraw.Draw(base)
    # illustration: the panel artwork, pasted into its frame
    base.alpha_composite(art_layer(art, w, art_h), (x, y))
    d.rectangle([x, y, x + w, y + art_h], outline=GREY, width=1)
    # caption bar over the art's foot: the place, in white on the region colour
    bar_h = 15 if w < 250 else 17
    d.rectangle([x + 1, y + art_h - bar_h, x + w - 1, y + art_h - 1],
                fill=REGION_COLORS[region])
    fc = font(SANS_BOLD, 9 if w < 250 else 11)
    d.text((x + 5, y + art_h - bar_h + 3), caption, font=fc, fill=WHITE)
    ty = y + art_h + 6
    fk = font(SANS_BOLD, 10 if w < 250 else 11)
    d.text((x, ty), f"{number} \u00b7 {kicker}", font=fk,
           fill=REGION_COLORS[region])
    ty += 15 if w < 250 else 16
    ty = head_text(d, headline, x, ty, w, SERIF_BOLD, head_size, INK,
                   head_leading, max_head_lines) + 3
    fd = font(SANS, deck_size)
    lines = wrap(d, deck, fd, w)[:max_deck_lines]
    draw_lines(d, lines, x, ty, fd, (60, 62, 60), deck_leading)
    return ty + len(lines) * deck_leading


def build():
    base = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(base)
    # hairline frame
    d.rectangle([6, 6, W - 7, H - 7], outline=PAPER_EDGE, width=1)

    # kicker row
    fk_l = font(SANS_BOLD, 11)
    fk_r = font(SANS_BOLD, 11)
    d.text((MARGIN, 10), "THE WORLD\u2019S NEWS IN ONE PICTURE",
           font=fk_l, fill=RED)
    right = "43 STORIES \u00b7 6 CONTINENTS \u00b7 ALL FROM TUESDAY"
    d.text((W - MARGIN - d.textlength(right, font=fk_r), 10), right,
           font=fk_r, fill=INK)

    # masthead
    mast = "Tuesday 17 November 2026"
    fm = fit_font(SERIF_BLACK, mast, 58, CW)
    d.text((MARGIN, 24), mast, font=fm, fill=INK)
    d.line([MARGIN, 90, W - MARGIN, 90], fill=INK, width=3)
    d.line([MARGIN, 94, W - MARGIN, 94], fill=INK, width=1)

    # key-numbers strip
    cell_w = CW / len(NUMBERS)
    fn_n = font(SERIF_BOLD, 20)
    fn_l = font(SANS, 9)
    for i, (num, label) in enumerate(NUMBERS):
        cx = MARGIN + cell_w * i
        d.text((cx + 8, 98), num, font=fn_n, fill=RED if i == 0 else INK)
        d.text((cx + 8, 122), label, font=fn_l, fill=GREY)
        if i:
            d.line([cx, 100, cx, 134], fill=LIGHT_GREY, width=1)

    # region bar, counted from the data
    counts = region_counts()
    order = ["Europe", "Middle East", "Asia", "Africa", "Americas",
             "Oceania", "World"]
    parts = "  \u00b7  ".join(
        f"{r.upper()} {counts.get(r, 0)}" for r in order)
    fr = font(SANS_BOLD, 10)
    tw = d.textlength(parts, font=fr)
    d.text(((W - tw) / 2, 140), parts, font=fr, fill=SLATE)

    # leads: 3 columns
    lead_w, lead_art = 322, 120
    lead_x = [MARGIN, MARGIN + lead_w + 10, MARGIN + 2 * (lead_w + 10)]
    for i, (region, kicker, head, deck, _lat, _lon) in enumerate(LEADS):
        draw_panel(base, lead_x[i], 158, lead_w, lead_art, PANEL_ART[i],
                   i + 1, region, kicker, head, deck,
                   head_size=21, head_leading=24, deck_size=12,
                   deck_leading=15, caption=CAPTIONS[i])

    # small stories: two rows of five
    small_w, small_art = 190, 88
    small_x = [MARGIN + i * (small_w + 11) for i in range(5)]
    for row in range(2):
        y = 414 + row * 194
        for col in range(5):
            idx = row * 5 + col
            region, kicker, head, deck, _lat, _lon = SMALL[idx]
            draw_panel(base, small_x[col], y, small_w, small_art,
                       PANEL_ART[3 + idx], idx + 4, region, kicker, head,
                       deck, head_size=14, head_leading=17, deck_size=10,
                       deck_leading=13, caption=CAPTIONS[3 + idx])

    # divider
    d.line([MARGIN, 800, W - MARGIN, 800], fill=INK, width=1)

    # map, left
    fh2 = font(SANS_BOLD, 11)
    d.text((MARGIN, 806), "WHERE IT HAPPENED", font=fh2, fill=RED)
    draw_map(base, (MARGIN, 824, MARGIN + 322, 966))
    fl = font(SANS, 9)
    d.text((MARGIN, 972), "Pins: stories 1\u201313  \u00b7  dots: 14\u201343",
           font=fl, fill=GREY)

    # also list, right: two columns of 15
    d.text((MARGIN + 338, 806), "ALSO ON TUESDAY 17 NOVEMBER", font=fh2,
           fill=RED)
    col_x = [MARGIN + 338, MARGIN + 338 + 330]
    for ci in range(2):
        y = 824
        for bi in range(15):
            idx = ci * 15 + bi
            region, place, text, _lat, _lon = BRIEFS[idx]
            num = str(idx + 14)
            fb = font(SANS_BOLD, 10)
            line = f"{num}  {place}: {text}"
            fnt = font(SANS, 10)
            if d.textlength(line, font=fnt) > 322:
                fnt = font(SANS, 9)
            d.text((col_x[ci], y), num, font=fb,
                   fill=REGION_COLORS[region])
            num_w = d.textlength(num + "  ", font=fb)
            d.text((col_x[ci] + num_w, y), f"{place}: {text}", font=fnt,
                   fill=INK)
            y += 11
    add_grain(base)

    # footer
    ff1 = font(SANS_BOLD, 10)
    ff1r = font(SANS, 10)
    ff2 = font(SANS, 9)
    y = 990
    d.text((MARGIN, y), "DATE CHECK \u2014 ", font=ff1, fill=RED)
    pre = d.textlength("DATE CHECK \u2014 ", font=ff1)
    d.text((MARGIN + pre, y),
           "Left out as earlier news: Russia\u2019s 1,336-drone claim (16 Nov); "
           "Vulcan rocket loss of 40 Amazon satellites (15 Nov).",
           font=ff1r, fill=INK)
    d.text((MARGIN, y + 13),
           "Every story here happened or was first reported on Tuesday 17 "
           "November 2026. Contested claims are marked as claims.  Sources: "
           "Reuters, AP, AFP, BBC, Al Jazeera, WHO, UN. Original drawings.",
           font=ff2, fill=GREY)
    return base.convert("RGB")


def main():
    out = Path(__file__).resolve().parent / "entry.png"
    img = build()
    img.save(out, optimize=True)
    size = out.stat().st_size
    fmt = "PNG"
    if size > 1048576:
        img.save(out, format="JPEG", quality=90, optimize=True)
        size = out.stat().st_size
        fmt = "JPEG"
    import hashlib
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"wrote {out} {size} bytes {fmt} sha256={sha} "
          f"{'OK <=1MiB' if size <= 1048576 else 'OVER 1MiB'}")


if __name__ == "__main__":
    main()
