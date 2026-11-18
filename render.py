#!/usr/bin/env python3
"""Render the news-image-20261117 front page: THE WORLD'S NEWS IN ONE PICTURE.

Build-time renderer. Run:  python3 render.py   (writes entry.png next to this file)
Deterministic: fixed seeds, no timestamps, no network. The entrypoint main.py
only copies the rendered entry.png to $MAKEFUN_OUTPUT_DIR, so the shipped
program is standard-library only.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
PAPER = (247, 243, 232)
INK = (26, 26, 26)
RED = (176, 42, 32)
NAVY = (31, 58, 95)
GREY = (110, 108, 100)
RULE = (60, 58, 52)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF_IT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
SANS_IT = "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def text_w(draw, s, fnt):
    return draw.textlength(s, font=fnt)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap to pixel width; returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_lines(draw, lines, x, y, fnt, fill, leading=None, max_lines=None,
               align="left", width=None):
    """Draw lines, truncating with an ellipsis if max_lines is exceeded."""
    if leading is None:
        leading = int(fnt.size * 1.22)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        # trim last line so the ellipsis fits
        while lines and draw.textlength(lines[-1] + " …", font=fnt) > (width or 10 ** 6):
            lines[-1] = lines[-1].rsplit(" ", 1)[0] if " " in lines[-1] else lines[-1][:-1]
        lines[-1] = lines[-1] + " …"
    for i, line in enumerate(lines):
        xx = x
        if align == "center" and width is not None:
            xx = x + (width - draw.textlength(line, font=fnt)) / 2
        draw.text((xx, y + i * leading), line, font=fnt, fill=fill)
    return y + len(lines) * leading


def vgrad(img, box, top, bottom):
    """Vertical gradient inside box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    h = max(1, y1 - y0)
    grad = Image.new("RGB", (1, h))
    px = grad.load()
    for j in range(h):
        t = j / (h - 1)
        px[0, j] = tuple(int(top[c] + (bottom[c] - top[c]) * t) for c in range(3))
    img.paste(grad.resize((x1 - x0, h)), (x0, y0))


def grain(draw, box, seed, n, color, alpha_box=None):
    """Sparse deterministic speckles for a painterly texture."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(n):
        x = rnd.randint(x0, x1 - 1)
        y = rnd.randint(y0, y1 - 1)
        v = rnd.randint(0, 2)
        c = (color[0] + v * 8, color[1] + v * 8, color[2] + v * 8)
        draw.point((x, y), fill=c)


def sun(draw, cx, cy, r, color):
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)


def silhouette_city(draw, x0, ybase, x1, color, seed, hmin=14, hmax=52):
    """Jagged skyline silhouette along ybase."""
    rnd = random.Random(seed)
    x = x0
    while x < x1:
        w = rnd.randint(10, 26)
        h = rnd.randint(hmin, hmax)
        draw.rectangle((x, ybase - h, x + w, ybase), fill=color)
        if rnd.random() < 0.4:
            draw.rectangle((x + w * 0.3, ybase - h - 6, x + w * 0.6, ybase - h), fill=color)
        x += w + rnd.randint(1, 5)


def sea(draw, box, color, seed, waves=6):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=color)
    rnd = random.Random(seed)
    for i in range(waves):
        yy = y0 + (i + 1) * (y1 - y0) // (waves + 1)
        for x in range(x0, x1, 14):
            draw.arc((x, yy - 3, x + 12, yy + 3), 180, 360,
                     fill=(220, 225, 230))


def frame(draw, box, fill=None, outline=RULE, width=1):
    draw.rectangle(box, fill=fill, outline=outline, width=width)


# ---------------------------------------------------------------- scenes
# Each painter draws inside box (x0, y0, x1, y1) on the given ImageDraw.
# Skies are gradients; foregrounds are dark silhouettes; a few accent shapes
# keep every panel painterly instead of flat vector art.


def sc_iran(draw, box, seed=11):
    x0, y0, x1, y1 = box
    vgrad_box = (x0, y0, x1, y1)
    vgrad(draw._image, vgrad_box, (58, 28, 44), (214, 122, 54))
    sun(draw, x0 + (x1 - x0) * 0.72, y0 + (y1 - y0) * 0.34, 16, (255, 214, 130))
    # missile streaks
    rnd = random.Random(seed)
    for _ in range(3):
        sx = rnd.randint(x0 + 10, x1 - 60)
        sy = rnd.randint(y0 + 8, y0 + 40)
        draw.line((sx, sy, sx + 34, sy + 26), fill=(255, 236, 180), width=2)
        draw.ellipse((sx + 34, sy + 24, sx + 40, sy + 30), fill=(255, 200, 90))
    # sea + island
    sea(draw, (x0, y1 - 34, x1, y1), (38, 52, 78), seed + 1, waves=3)
    draw.polygon([(x0 + 18, y1 - 34), (x0 + 60, y1 - 62), (x0 + 120, y1 - 52),
                  (x0 + 150, y1 - 34)], fill=(24, 20, 28))
    draw.polygon([(x0 + 60, y1 - 62), (x0 + 66, y1 - 78), (x0 + 72, y1 - 62)],
                 fill=(24, 20, 28))
    # jet silhouette
    jx, jy = x0 + (x1 - x0) * 0.30, y0 + 26
    draw.polygon([(jx, jy), (jx + 34, jy + 6), (jx, jy + 12), (jx + 6, jy + 6)],
                 fill=(16, 14, 18))
    draw.polygon([(jx + 10, jy + 2), (jx + 18, jy - 8), (jx + 20, jy + 4)],
                 fill=(16, 14, 18))
    grain(draw, box, seed, 60, (90, 60, 60))


def sc_kerch(draw, box, seed=21):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (74, 96, 122), (196, 205, 210))
    # broken bridge deck
    deck_y = y0 + (y1 - y0) * 0.42
    draw.line((x0, deck_y, x0 + 78, deck_y), fill=(30, 30, 34), width=5)
    draw.line((x0 + 118, deck_y + 26, x1, deck_y + 30), fill=(30, 30, 34), width=5)
    draw.line((x0 + 78, deck_y, x0 + 96, deck_y + 44), fill=(30, 30, 34), width=4)
    draw.line((x0 + 100, deck_y + 46, x0 + 118, deck_y + 26), fill=(30, 30, 34), width=4)
    # pylons
    draw.rectangle((x0 + 34, deck_y - 34, x0 + 38, deck_y), fill=(30, 30, 34))
    draw.rectangle((x1 - 30, deck_y + 30 - 30, x1 - 26, deck_y + 30), fill=(30, 30, 34))
    # smoke
    for cx, cy, r in ((x0 + 92, deck_y - 6, 12), (x0 + 104, deck_y - 18, 9),
                      (x0 + 84, deck_y - 16, 7)):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(120, 118, 112))
    # water + fallen span
    sea(draw, (x0, y1 - 46, x1, y1), (52, 84, 108), seed + 1, waves=3)
    draw.polygon([(x0 + 84, y1 - 40), (x0 + 112, y1 - 46), (x0 + 120, y1 - 30),
                  (x0 + 92, y1 - 24)], fill=(24, 24, 28))
    grain(draw, box, seed, 50, (90, 90, 95))


def sc_manila(draw, box, seed=31):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (16, 96, 110), (255, 196, 110))
    sun(draw, x0 + (x1 - x0) * 0.5, y0 + (y1 - y0) * 0.42, 18, (255, 232, 150))
    silhouette_city(draw, x0, y1 - 22, x1, (22, 26, 40), seed, 20, 58)
    # flags on poles
    for i, col in enumerate(((176, 42, 32), (31, 58, 95), (200, 160, 40))):
        fx = x0 + 26 + i * 34
        draw.line((fx, y1 - 66, fx, y1 - 22), fill=(22, 26, 40), width=2)
        draw.polygon([(fx, y1 - 66), (fx + 20, y1 - 61), (fx, y1 - 56)], fill=col)
    # crowd silhouettes
    rnd = random.Random(seed + 2)
    for _ in range(14):
        cx = rnd.randint(x0 + 6, x1 - 6)
        draw.ellipse((cx - 3, y1 - 20, cx + 3, y1 - 14), fill=(16, 16, 20))
        draw.rectangle((cx - 4, y1 - 14, cx + 4, y1 - 2), fill=(16, 16, 20))
    grain(draw, box, seed, 50, (120, 90, 60))


def sc_tanker(draw, box, seed=41):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (30, 40, 66), (120, 90, 80))
    # tanker hull
    draw.polygon([(x0 + 12, y1 - 52), (x0 + 26, y1 - 58), (x1 - 20, y1 - 58),
                  (x1 - 8, y1 - 52), (x1 - 8, y1 - 40), (x0 + 12, y1 - 40)],
                 fill=(18, 18, 22))
    draw.rectangle((x0 + 96, y1 - 74, x0 + 118, y1 - 58), fill=(18, 18, 22))
    # flames
    for cx, cy, r, col in ((x0 + 52, y1 - 66, 12, (255, 140, 40)),
                           (x0 + 66, y1 - 74, 9, (255, 190, 80)),
                           (x0 + 40, y1 - 70, 7, (230, 90, 30))):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    # smoke
    for cx, cy, r in ((x0 + 56, y1 - 92, 11), (x0 + 70, y1 - 100, 8)):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(90, 86, 84))
    sea(draw, (x0, y1 - 38, x1, y1), (44, 66, 92), seed + 1, waves=3)
    grain(draw, box, seed, 45, (80, 70, 70))


def sc_dirtybomb(draw, box, seed=51):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (40, 52, 84), (168, 178, 190))
    # capitol dome silhouette
    cx = x0 + (x1 - x0) // 2
    draw.rectangle((cx - 52, y1 - 46, cx + 52, y1 - 30), fill=(28, 30, 44))
    draw.polygon([(cx - 52, y1 - 46), (cx, y1 - 78), (cx + 52, y1 - 46)],
                 fill=(28, 30, 44))
    draw.rectangle((cx - 3, y1 - 92, cx + 3, y1 - 76), fill=(28, 30, 44))
    draw.ellipse((cx - 4, y1 - 96, cx + 4, y1 - 88), fill=(28, 30, 44))
    # warning triangle
    tx, ty = x0 + (x1 - x0) * 0.78, y0 + 26
    draw.polygon([(tx, ty - 14), (tx + 15, ty + 12), (tx - 15, ty + 12)],
                 fill=(232, 178, 30), outline=(26, 26, 26))
    draw.text((tx - 2, ty - 6), "!", font=font(SANS_B, 13), fill=(26, 26, 26))
    # radar arcs
    for r in (10, 18, 26):
        draw.arc((x0 + 12, y0 + 12, x0 + 12 + 2 * r, y0 + 12 + 2 * r), 270, 360,
                 fill=(232, 178, 30), width=2)
    grain(draw, box, seed, 40, (90, 90, 100))


def sc_kyiv(draw, box, seed=61):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (52, 62, 88), (206, 178, 140))
    # river + bridge
    draw.rectangle((x0, y1 - 30, x1, y1), fill=(70, 100, 130))
    draw.line((x0, y1 - 44, x1, y1 - 44), fill=(30, 30, 34), width=4)
    for px in (x0 + 30, x0 + 80, x0 + 130):
        draw.line((px, y1 - 44, px, y1 - 30), fill=(30, 30, 34), width=3)
    silhouette_city(draw, x0, y1 - 44, x1, (26, 28, 42), seed, 12, 40)
    # smoke columns
    for cx in (x0 + 44, x0 + 118):
        for k, r in enumerate((9, 7, 5)):
            draw.ellipse((cx - r, y1 - 92 - k * 12 - r, cx + r, y1 - 92 - k * 12 + r),
                         fill=(110, 106, 100))
    grain(draw, box, seed, 45, (100, 95, 85))


def sc_jets(draw, box, seed=71):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (150, 178, 205), (250, 208, 160))
    sun(draw, x0 + (x1 - x0) * 0.24, y0 + (y1 - y0) * 0.62, 13, (255, 220, 140))
    # cloud streaks
    rnd = random.Random(seed)
    for _ in range(5):
        cx = rnd.randint(x0 + 4, x1 - 50)
        cy = rnd.randint(y0 + 6, y1 - 20)
        draw.ellipse((cx, cy, cx + 44, cy + 7), fill=(240, 238, 230))
    # two jets with contrails
    for jx, jy, s in ((x0 + 60, y0 + 26, 1.0), (x0 + 108, y0 + 48, 0.7)):
        draw.line((jx - 52, jy + 10, jx, jy + 6), fill=(255, 255, 255), width=2)
        draw.polygon([(jx, jy), (jx + int(30 * s), jy + 5),
                      (jx, jy + 10), (jx + 5, jy + 5)], fill=(24, 26, 34))
        draw.polygon([(jx + 9, jy + 2), (jx + 16, jy - 7), (jx + 18, jy + 4)],
                     fill=(24, 26, 34))
    grain(draw, box, seed, 40, (120, 120, 120))


def sc_gaza(draw, box, seed=81):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (96, 104, 116), (168, 164, 152))
    # rain streaks
    rnd = random.Random(seed)
    for _ in range(26):
        rx = rnd.randint(x0 + 4, x1 - 4)
        ry = rnd.randint(y0 + 4, y1 - 30)
        draw.line((rx, ry, rx - 3, ry + 9), fill=(210, 212, 214), width=1)
    # tents
    for i, tx in enumerate((x0 + 12, x0 + 66, x0 + 122)):
        ty = y1 - 26
        col = (196, 182, 150) if i % 2 == 0 else (176, 168, 148)
        draw.polygon([(tx, ty), (tx + 22, ty - 24), (tx + 44, ty)], fill=col)
        draw.line((tx + 22, ty - 24, tx + 22, ty), fill=(90, 84, 70), width=1)
    draw.rectangle((x0, y1 - 8, x1, y1), fill=(110, 108, 96))
    grain(draw, box, seed, 45, (90, 90, 90))


def sc_measles(draw, box, seed=91):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (214, 226, 232), (240, 238, 228))
    # hospital block with red cross
    draw.rectangle((x0 + 14, y1 - 58, x0 + 78, y1 - 12), fill=(245, 245, 240),
                   outline=(60, 60, 60))
    draw.rectangle((x0 + 40, y1 - 52, x0 + 52, y1 - 28), fill=(176, 42, 32))
    draw.rectangle((x0 + 34, y1 - 46, x0 + 58, y1 - 34), fill=(176, 42, 32))
    for wx in (x0 + 20, x0 + 60):
        draw.rectangle((wx, y1 - 22, wx + 8, y1 - 14), fill=(120, 150, 180))
    # rising case bars
    bx = x0 + 92
    for i, h in enumerate((10, 18, 30, 44)):
        draw.rectangle((bx + i * 20, y1 - 12 - h, bx + i * 20 + 13, y1 - 12),
                       fill=(176, 42, 32) if i == 3 else (200, 90, 70))
    grain(draw, box, seed, 35, (150, 150, 150))


def sc_markets(draw, box, seed=101):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(18, 24, 34))
    # grid
    for gy in range(y0 + 14, y1 - 8, 16):
        draw.line((x0 + 6, gy, x1 - 6, gy), fill=(48, 58, 74), width=1)
    # falling line
    pts = [(x0 + 10, y0 + 26), (x0 + 46, y0 + 34), (x0 + 82, y0 + 30),
           (x0 + 118, y0 + 48), (x0 + 152, y0 + 58), (x1 - 12, y0 + 72)]
    draw.line(pts, fill=(230, 70, 55), width=3)
    draw.ellipse((pts[-1][0] - 3, pts[-1][1] - 3, pts[-1][0] + 3, pts[-1][1] + 3),
                 fill=(230, 70, 55))
    draw.rectangle((x0 + 10, y0 + 8, x0 + 62, y0 + 22), fill=(34, 120, 60))
    draw.text((x0 + 14, y0 + 10), "NVDA", font=font(SANS_B, 10), fill=(255, 255, 255))
    draw.text((x1 - 52, y0 + 8), "-1%", font=font(SANS_B, 13), fill=(230, 70, 55))
    grain(draw, box, seed, 35, (60, 70, 90))


def sc_houthi(draw, box, seed=111):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (96, 60, 52), (238, 178, 110))
    sun(draw, x0 + (x1 - x0) * 0.68, y0 + (y1 - y0) * 0.36, 14, (255, 214, 130))
    # dunes
    draw.polygon([(x0, y1 - 34), (x0 + 50, y1 - 56), (x0 + 110, y1 - 40),
                  (x0 + 150, y1 - 52), (x1, y1 - 36), (x1, y1), (x0, y1)],
                 fill=(150, 104, 62))
    draw.polygon([(x0, y1 - 18), (x0 + 70, y1 - 30), (x1, y1 - 20),
                  (x1, y1), (x0, y1)], fill=(120, 80, 48))
    # convoy silhouettes
    for tx in (x0 + 22, x0 + 58, x0 + 96):
        draw.rectangle((tx, y1 - 30, tx + 24, y1 - 20), fill=(28, 22, 20))
        draw.rectangle((tx + 16, y1 - 36, tx + 24, y1 - 30), fill=(28, 22, 20))
        draw.ellipse((tx + 4, y1 - 21, tx + 9, y1 - 16), fill=(16, 14, 12))
        draw.ellipse((tx + 15, y1 - 21, tx + 20, y1 - 16), fill=(16, 14, 12))
    grain(draw, box, seed, 45, (140, 100, 60))


def sc_lebanon(draw, box, seed=121):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (140, 168, 150), (226, 214, 180))
    # hills
    draw.polygon([(x0, y1 - 40), (x0 + 60, y1 - 66), (x0 + 130, y1 - 46),
                  (x1, y1 - 58), (x1, y1), (x0, y1)], fill=(96, 128, 84))
    draw.polygon([(x0, y1 - 22), (x0 + 80, y1 - 36), (x1, y1 - 24),
                  (x1, y1), (x0, y1)], fill=(70, 100, 62))
    # village blocks
    for vx, vw in ((x0 + 18, 16), (x0 + 44, 12), (x0 + 96, 18), (x0 + 128, 12)):
        draw.rectangle((vx, y1 - 46, vx + vw, y1 - 30), fill=(232, 224, 200),
                       outline=(90, 84, 70))
    # smoke columns
    for cx in (x0 + 52, x0 + 118):
        for k, r in enumerate((8, 6, 4)):
            draw.ellipse((cx - r, y1 - 84 - k * 11 - r, cx + r, y1 - 84 - k * 11 + r),
                         fill=(105, 102, 96))
    # cypress trees
    for tx in (x0 + 78, x0 + 152):
        draw.polygon([(tx, y1 - 52), (tx + 5, y1 - 30), (tx + 10, y1 - 52)],
                     fill=(40, 70, 40))
    grain(draw, box, seed, 40, (110, 110, 95))


def sc_depardieu(draw, box, seed=131):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (72, 28, 36), (150, 60, 52))
    # cinema facade
    draw.rectangle((x0 + 16, y1 - 62, x1 - 16, y1 - 10), fill=(38, 22, 28),
                   outline=(200, 170, 90))
    draw.rectangle((x0 + 26, y1 - 52, x1 - 26, y1 - 34), fill=(232, 196, 90))
    draw.text((x0 + 34, y1 - 50), "CINEMA", font=font(SANS_B, 12),
              fill=(38, 22, 28))
    # doors + poster frames
    draw.rectangle((x0 + 52, y1 - 30, x0 + 76, y1 - 10), fill=(90, 40, 44))
    draw.rectangle((x0 + 96, y1 - 30, x0 + 120, y1 - 10), fill=(90, 40, 44))
    # film reel
    rx, ry = x0 + 150, y0 + 26
    draw.ellipse((rx - 13, ry - 13, rx + 13, ry + 13), outline=(232, 196, 90),
                 width=3)
    for ang in (30, 150, 270):
        a = math.radians(ang)
        draw.ellipse((rx + int(7 * math.cos(a)) - 3, ry + int(7 * math.sin(a)) - 3,
                      rx + int(7 * math.cos(a)) + 3, ry + int(7 * math.sin(a)) + 3),
                     fill=(232, 196, 90))
    grain(draw, box, seed, 40, (120, 70, 70))


def sc_outages(draw, box, seed=141):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (24, 34, 58), (70, 84, 110))
    # control tower
    draw.rectangle((x0 + 138, y0 + 22, x0 + 146, y1 - 24), fill=(18, 20, 28))
    draw.ellipse((x0 + 130, y0 + 12, x0 + 154, y0 + 30), fill=(18, 20, 28))
    draw.rectangle((x0 + 134, y0 + 16, x0 + 150, y0 + 24), fill=(255, 200, 90))
    # departure board
    draw.rectangle((x0 + 12, y0 + 18, x0 + 112, y0 + 62), fill=(14, 16, 20),
                   outline=(120, 120, 120))
    for i, yy in enumerate((y0 + 24, y0 + 38, y0 + 52)):
        draw.rectangle((x0 + 18, yy, x0 + 58, yy + 8), fill=(60, 64, 70))
        draw.rectangle((x0 + 64, yy, x0 + 106, yy + 8), fill=(150, 40, 34))
    # grounded plane silhouette
    draw.polygon([(x0 + 20, y1 - 30), (x0 + 110, y1 - 30), (x0 + 128, y1 - 24),
                  (x0 + 20, y1 - 24)], fill=(14, 16, 22))
    draw.polygon([(x0 + 56, y1 - 30), (x0 + 66, y1 - 46), (x0 + 72, y1 - 30)],
                 fill=(14, 16, 22))
    grain(draw, box, seed, 40, (70, 80, 110))


# ---------------------------------------------------------------- world map
# Coarse continent outlines in (lon, lat); drawn equirectangular into the box.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-75, 73), (-55, 60),
     (-60, 47), (-75, 35), (-80, 25), (-97, 16), (-105, 20), (-117, 33),
     (-125, 40), (-124, 48), (-150, 60), (-168, 66)],
    [(-58, 64), (-40, 70), (-30, 76), (-55, 80), (-68, 76), (-58, 64)],
    [(-80, 10), (-60, 5), (-50, -5), (-35, -8), (-40, -20), (-48, -28),
     (-58, -35), (-65, -41), (-70, -52), (-73, -40), (-75, -20), (-80, -5),
     (-80, 10)],
    [(-10, 36), (-2, 48), (5, 58), (10, 58), (18, 56), (23, 60), (30, 60),
     (28, 55), (20, 45), (12, 44), (3, 42), (-9, 38), (-10, 36)],
    [(-17, 15), (-10, 30), (10, 37), (20, 32), (30, 31), (35, 28), (43, 12),
     (51, 11), (48, 0), (40, -15), (35, -25), (28, -33), (18, -35), (12, -18),
     (9, 4), (-8, 5), (-17, 15)],
    [(30, 60), (45, 68), (60, 70), (75, 73), (90, 75), (110, 74), (130, 72),
     (150, 70), (160, 62), (158, 52), (142, 45), (135, 35), (127, 33),
     (120, 25), (110, 20), (105, 10), (100, 8), (95, 15), (90, 22), (80, 8),
     (77, 8), (70, 25), (60, 25), (52, 28), (48, 30), (43, 38), (38, 42),
     (30, 45), (30, 60)],
    [(114, -22), (122, -14), (132, -12), (142, -11), (146, -19), (150, -23),
     (153, -27), (146, -39), (140, -38), (130, -32), (124, -33), (115, -35),
     (114, -22)],
]

# story number -> (lon, lat) pin position on the map
# At this scale 1 deg ~ 1.25 px, so genuinely close stories overlap:
# Gaza (7) hid behind Lebanon (11), Kerch (2) behind Kyiv (5), and
# Iran (1) behind Oman (4). Each pair is nudged apart along the coast
# or region just far enough that all 13 circles clear each other
# (every nearest-neighbour pair is >= 15 px apart, pins are 14 px wide).
PINS = {
    1: (53, 30), 2: (40, 47), 3: (121, 15), 4: (59, 19), 5: (28, 52),
    6: (139, 36), 7: (30, 27), 8: (-98, 39), 9: (-74, 41), 10: (45, 13),
    11: (39, 35), 12: (2, 49), 13: (-122, 47),
}

# story number -> region colour, same RGB values as the legend in build()
PIN_REGION = {
    1: (200, 130, 40), 2: (31, 58, 95), 3: (120, 80, 160),
    4: (200, 130, 40), 5: (31, 58, 95), 6: (120, 80, 160),
    7: (200, 130, 40), 8: (176, 42, 32), 9: (176, 42, 32),
    10: (200, 130, 40), 11: (200, 130, 40), 12: (31, 58, 95),
    13: (176, 42, 32),
}


def draw_map(draw, box):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(188, 208, 222))
    for poly in CONTINENTS:
        pts = [(x0 + (lon + 170) / 360.0 * (x1 - x0),
                y0 + (75 - lat) / 130.0 * (y1 - y0)) for lon, lat in poly]
        draw.polygon(pts, fill=(232, 214, 170), outline=(150, 132, 96))
    for n, (lon, lat) in PINS.items():
        px = x0 + (lon + 170) / 360.0 * (x1 - x0)
        py = y0 + (75 - lat) / 130.0 * (y1 - y0)
        draw.ellipse((px - 7, py - 7, px + 7, py + 7), fill=PIN_REGION[n],
                     outline=(255, 255, 255), width=1)
        t = str(n)
        tw = draw.textlength(t, font=font(SANS_B, 9))
        draw.text((px - tw / 2, py - 5), t, font=font(SANS_B, 9),
                  fill=(255, 255, 255))


# ---------------------------------------------------------------- stories
# n, kicker, headline, deck, scene painter (None for list-only stories)
HEROES = [
    (1, "MIDDLE EAST · IRAN WAR",
     "US strikes Iran after Hormuz tanker attacks",
     "Warplanes hit missile sites on Qeshm Island after attacks on ships in the Strait of Hormuz. A tanker burned off Oman; Iran denies a 'dirty bomb' report.",
     sc_iran),
    (2, "UKRAINE · WAR",
     "Ukraine hits Kerch Bridge; span falls into the sea",
     "Drones and missiles brought a span down and halted traffic. Russia hit Kyiv's Dnipro bridges, cutting heat to hundreds of buildings.",
     sc_kerch),
    (3, "ASIA · DIPLOMACY",
     "Trump in Manila ahead of Xi-Putin summit in China",
     "Protests met the ASEAN summit as hundreds were arrested. NVIDIA posted record revenue amid scandal claims around chief Jensen Huang.",
     sc_manila),
]

MEDIUM = [
    (4, "GULF · TANKER FIRE",
     "Tanker ablaze off Oman; 24 seafarers evacuated",
     "The gas tanker Tara Gas burned off Musandam; Oman evacuated the crew.",
     sc_tanker),
    (5, "UKRAINE · KYIV",
     "Kyiv bridges hit; heat cut to hundreds of buildings",
     "Russia struck the South and North bridges over the Dnipro.",
     sc_kyiv),
    (6, "ASIA · JAPAN",
     "Japan scrambles jets as Russian planes enter airspace",
     "Two suspected Russian aircraft violated airspace; Tokyo protested.",
     sc_jets),
    (7, "MIDDLE EAST · GAZA",
     "West urges Israel to open Gaza crossings for aid",
     "The UK, Australia, Canada and Italy called the situation catastrophic.",
     sc_gaza),
    (8, "HEALTH · UNITED STATES",
     "US loses measles elimination status",
     "First loss since 2000; experts blame declining vaccination rates.",
     sc_measles),
    (9, "MARKETS",
     "Wall Street falls as AI and tech stocks drop",
     "Indexes closed lower despite NVIDIA's record revenue.",
     sc_markets),
    (10, "MIDDLE EAST · YEMEN",
     "Houthis advance on Aden; drones fired at Saudi pipeline",
     "Government forces pulled back from the Red Sea coast.",
     sc_houthi),
    (11, "MIDDLE EAST · LEBANON",
     "Airstrikes and shelling shake southern Lebanon",
     "Airstrikes, artillery fire and detonations were reported on Tuesday.",
     sc_lebanon),
    (12, "EUROPE · FRANCE",
     "Depardieu pleads guilty to sexual assault",
     "The French actor dropped his appeal in Paris and admitted the charge.",
     sc_depardieu),
    (13, "UNITED STATES · OUTAGES",
     "Outage week hits airports, banks, Apple and the NSA",
     "A classified NSA system went down; the DNI denied a cyberattack.",
     sc_outages),
]

ALSO_ON = [
    "NATO cancels 2027 summit planned for Albania",
    "Imran Khan fears dying in jail, seeks hospital",
    "Phuket fire kills 11, injures 16",
    "Dubai airport traffic down 28.1% in nine months",
    "Pattinson named the next James Bond",
    "National Geographic Pictures of the Year out",
    "Tiger Woods returns to golf",
    "Waymo robotaxis pulled from freeways",
    "Hungary recovers $19.5M in bribery probe",
    "UK sanctions eight Israeli settlement builders",
    "Five EU states plan Rwanda return hub",
    "FIFA and ICC 2030 World Cups to overlap",
    "Zelenskyy urges SpaceX to lift Starshield limits",
    "Irish activist charged over $60M C-130 damage",
    "Illinois ethanol plant bomb plot alleged",
    "Florida flooding; western storm hits",
    "Trump takes 'dirty bomb' report seriously",
    "California landfill explosion",
    "US air-traffic failure grounds flights nationwide",
    "Apple sign-in and App Store problems resolved",
    "Bahrain says drone attack on US radar intercepted",
    "Saudi Arabia replaces coalition commander",
    "Kerch strike: two deaths reported, trains resume",
    "Russia claims 1,336 drones shot down",
    "Second tanker strike reported near Khasab",
    "Dubai job-loss payouts top AED 250 million",
    "Nvidia chief accused of threatening executive",
    "Albania offers to host 2028 NATO summit",
    "Trump to meet Xi and Putin in Shenzhen Thursday",
    "US officials split on outage cause; AI speculated",
    "Forensic expert doubts Epstein suicide ruling",
    "Houthis reported about 60 km from Aden",
    "UN: winter rains flood Gaza shelters",
    "Houthis say five drones fired at Saudi pipeline",
]


# ---------------------------------------------------------------- layout
def paint_clipped(draw, painter, box):
    """Render a scene painter onto its own layer, then paste it clipped
    to the box. No pixel of the scene may escape the panel frame:
    smoke, skylines and sea arcs that used to spill into the gutter
    or over neighbouring text are cut off at the box edge."""
    base = draw._image
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ldraw = ImageDraw.Draw(layer)
    painter(ldraw, (0, 0, w, h))
    base.paste(layer, (x0, y0), layer)


def story_block(draw, x, y, w, s, img_h, hero=False):
    n, kicker, headline, deck, painter = s
    box = (x, y, x + w, y + img_h)
    if painter is not None:
        paint_clipped(draw, painter, box)
    frame(draw, box)
    ty = y + img_h + 7
    # number badge + kicker
    draw.ellipse((x, ty, x + 16, ty + 16), fill=RED)
    t = str(n)
    tw = draw.textlength(t, font=font(SANS_B, 10))
    draw.text((x + 8 - tw / 2, ty + 3), t, font=font(SANS_B, 10),
              fill=(255, 255, 255))
    draw.text((x + 21, ty + 2), kicker, font=font(SANS_B, 10), fill=RED)
    hy = ty + 20
    if hero:
        lines = wrap(draw, headline, font(SERIF, 20), w)
        hy = draw_lines(draw, lines, x, hy, font(SERIF, 20), INK, leading=23,
                        max_lines=3, width=w)
        dlines = wrap(draw, deck, font(SANS, 11), w)
        hy = draw_lines(draw, dlines, x, hy + 3, font(SANS, 11),
                        (64, 62, 56), leading=14, max_lines=3, width=w)
    else:
        lines = wrap(draw, headline, font(SANS_B, 13), w)
        hy = draw_lines(draw, lines, x, hy, font(SANS_B, 13), INK, leading=15,
                        max_lines=3, width=w)
        dlines = wrap(draw, deck, font(SANS, 10), w)
        hy = draw_lines(draw, dlines, x, hy + 2, font(SANS, 10),
                        (64, 62, 56), leading=12, max_lines=2, width=w)
    return hy


def fit_one_line(draw, text, fnt, max_w):
    """Truncate to one line with an ellipsis if it does not fit."""
    if draw.textlength(text, font=fnt) <= max_w:
        return text
    while text and draw.textlength(text + " …", font=fnt) > max_w:
        text = text.rsplit(" ", 1)[0] if " " in text else text[:-1]
    return text + " …"


def build():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    M = 22
    CW = W - 2 * M  # 980

    # masthead
    draw.text((M, 12), "THE WORLD'S NEWS IN ONE PICTURE",
              font=font(SANS_B, 15), fill=RED)
    ed = "TUESDAY EDITION"
    draw.text((W - M - draw.textlength(ed, font=font(SANS_B, 11)), 14), ed,
              font=font(SANS_B, 11), fill=GREY)
    draw.text((M, 30), "Tuesday 17 November 2026",
              font=font(SERIF, 54), fill=INK)
    draw.line((M, 90, W - M, 90), fill=RULE, width=1)
    draw.line((M, 94, W - M, 94), fill=RULE, width=3)
    count = "47 STORIES · 6 CONTINENTS · ALL REPORTED ON TUESDAY 17 NOVEMBER 2026"
    draw.text(((W - draw.textlength(count, font=font(SANS_B, 12))) / 2, 101),
              count, font=font(SANS_B, 12), fill=(64, 62, 56))

    # heroes: 3 columns
    hx = [M, M + 330, M + 660]
    for x, s in zip(hx, HEROES):
        story_block(draw, x, 122, 320, s, 148, hero=True)
    draw.line((M, 410, W - M, 410), fill=RULE, width=1)

    # medium: 2 rows x 5 columns
    mw, gap = 192, 5
    for row, y0 in enumerate((418, 594)):
        for col in range(5):
            s = MEDIUM[row * 5 + col]
            story_block(draw, M + col * (mw + gap), y0, mw, s, 84)
    draw.line((M, 770, W - M, 770), fill=RULE, width=1)

    # bottom band: map + also-on list
    draw.text((M, 778), "WHERE IT HAPPENED", font=font(SANS_B, 12), fill=RED)
    draw_map(draw, (M, 800, M + 452, 962))
    legend = [("Americas", (176, 42, 32)), ("Europe", (31, 58, 95)),
              ("Middle East", (200, 130, 40)), ("Asia", (120, 80, 160)),
              ("Africa", (60, 140, 70)), ("Oceania", (40, 140, 150))]
    lx = M
    for name, col in legend:
        draw.ellipse((lx, 970, lx + 8, 978), fill=col)
        draw.text((lx + 11, 968), name, font=font(SANS, 9), fill=(64, 62, 56))
        lx += 11 + draw.textlength(name, font=font(SANS, 9)) + 12

    draw.text((486, 778), "ALSO ON TUESDAY 17 NOVEMBER",
              font=font(SANS_B, 12), fill=RED)
    cols = [ALSO_ON[:17], ALSO_ON[17:]]
    for ci, items in enumerate(cols):
        cx = 486 + ci * 262
        for i, text in enumerate(items):
            n = 14 + ci * 17 + i
            yy = 800 + i * 11
            draw.text((cx, yy), str(n), font=font(SANS_B, 10), fill=RED)
            num_w = draw.textlength(str(n), font=font(SANS_B, 10))
            fitted = fit_one_line(draw, text, font(SANS, 10), 250 - num_w - 5)
            draw.text((cx + num_w + 4, yy), fitted, font=font(SANS, 10),
                      fill=INK)

    # footer
    draw.line((M, 992, W - M, 992), fill=RULE, width=1)
    foot_l = ("Every story here happened or was first reported on Tuesday "
              "17 November 2026. Contested claims are labelled as claims.")
    draw.text((M, 998), foot_l, font=font(SANS_IT, 9), fill=GREY)
    foot_r = "Sources: AP, Reuters, AFP, BBC, Al Jazeera, CNBC"
    draw.text((W - M - draw.textlength(foot_r, font=font(SANS, 9)), 998),
              foot_r, font=font(SANS, 9), fill=GREY)
    return img


def main():
    import hashlib
    import os
    img = build()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    img.save(out, optimize=True)
    data = open(out, "rb").read()
    print("entry.png bytes:", len(data))
    print("sha256:", hashlib.sha256(data).hexdigest())
    print("size:", img.size)


if __name__ == "__main__":
    main()
