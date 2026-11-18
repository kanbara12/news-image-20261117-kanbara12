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


def paper_grain(img, seed=20261117, alpha=0.05):
    """Deterministic print grain over the whole page: a small seeded
    noise tile (128x128) tiled across the page, blended at low alpha.
    Softens the flat-digital look of solid colour blocks without
    touching any text or layout."""
    rng = random.Random(seed)
    tile = Image.new("L", (128, 128))
    tp = tile.load()
    for y in range(128):
        for x in range(128):
            tp[x, y] = max(0, min(255, int(128 + rng.gauss(0, 22))))
    noise = Image.new("L", img.size)
    for y in range(0, img.size[1], 128):
        for x in range(0, img.size[0], 128):
            noise.paste(tile, (x, y))
    return Image.blend(img, Image.merge("RGB", (noise, noise, noise)), alpha)


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


def ribbon(draw, box, text, bg, fg, top=False, size=9, h=14):
    """Solid label strip at the bottom (default) or top of a panel box,
    text centred. box is in the painter's own layer coordinates."""
    x0, y0, x1, y1 = box
    ry0 = y0 if top else y1 - h
    ry1 = y0 + h if top else y1
    draw.rectangle((x0, ry0, x1, ry1), fill=bg)
    draw.line((x0, ry1 if top else ry0, x1, ry1 if top else ry0),
              fill=(255, 255, 255), width=1)
    fnt = font(SANS_B, size)
    tw = draw.textlength(text, font=fnt)
    draw.text(((x0 + x1 - tw) / 2, ry0 + (h - size) / 2 - 1), text,
              font=fnt, fill=fg)


def pill(draw, x, y, text, bg, fg, size=8, pad=4):
    """Small rounded data tag; returns the x of its right edge."""
    fnt = font(SANS_B, size)
    tw = draw.textlength(text, font=fnt)
    w = int(tw) + 2 * pad
    h = size + 2 * pad - 1
    draw.rounded_rectangle((x, y, x + w, y + h), radius=3, fill=bg,
                           outline=(255, 255, 255), width=1)
    draw.text((x + pad, y + pad - 2), text, font=fnt, fill=fg)
    return x + w


def flag(draw, x, y, w, h, stripes):
    """Tiny flag from horizontal stripes; thin dark outline."""
    n = len(stripes)
    for i, col in enumerate(stripes):
        draw.rectangle((x, y + i * h // n, x + w, y + (i + 1) * h // n),
                       fill=col)
    draw.rectangle((x, y, x + w, y + h), outline=(26, 26, 26))


def desat(col, f=0.7):
    """Lower a region colour's saturation ~30% for small map dots."""
    return tuple(int(c * f + 128 * (1 - f)) for c in col)


# ---------------------------------------------------------------- scenes
# Each painter draws inside box (x0, y0, x1, y1) on the given ImageDraw.
# Skies are gradients; foregrounds are dark silhouettes; a few accent shapes
# keep every panel painterly instead of flat vector art.


def sc_iran(draw, box, seed=11):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (58, 28, 44), (214, 122, 54))
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
    # Qeshm hills: 3 ridged layers on the right, launchers + flashes
    draw.polygon([(225, y1 - 34), (245, y1 - 66), (270, y1 - 52), (295, y1 - 60),
                  (312, y1 - 34)], fill=(72, 52, 88))
    draw.polygon([(225, y1 - 34), (252, y1 - 56), (280, y1 - 44), (312, y1 - 50),
                  (312, y1 - 34)], fill=(58, 34, 30))
    draw.polygon([(232, y1 - 34), (258, y1 - 48), (292, y1 - 38), (312, y1 - 44),
                  (312, y1 - 34)], fill=(22, 18, 26))
    for lx, ly in ((240, y1 - 52), (262, y1 - 44), (286, y1 - 46)):
        draw.rectangle((lx, ly - 10, lx + 10, ly), fill=(14, 12, 16))
        draw.line((lx + 5, ly - 10, lx + 8, ly - 18), fill=(14, 12, 16), width=2)
        draw.ellipse((lx + 4, ly - 22, lx + 12, ly - 14), fill=(255, 170, 60))
    # smoking tanker on open sea, right of the island
    tx, ty = 158, y1 - 22
    draw.polygon([(tx, ty), (tx + 10, ty - 5), (tx + 42, ty - 5), (tx + 48, ty),
                  (tx + 48, ty + 6), (tx, ty + 6)], fill=(16, 16, 20))
    draw.rectangle((tx + 30, ty - 12, tx + 38, ty - 5), fill=(16, 16, 20))
    for cx, cy, r in ((tx + 34, ty - 20, 6), (tx + 38, ty - 27, 5)):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(96, 90, 88))
    # orange light reflections on the water (open sea, clear of the hills)
    for rx in (170, 208):
        for k in range(3):
            draw.line((rx, y1 - 30 + k * 7, rx + 16, y1 - 30 + k * 7),
                      fill=(255, 170, 80), width=2)
    # jet silhouette
    jx, jy = x0 + (x1 - x0) * 0.30, y0 + 26
    draw.polygon([(jx, jy), (jx + 34, jy + 6), (jx, jy + 12), (jx + 6, jy + 6)],
                 fill=(16, 14, 18))
    draw.polygon([(jx + 10, jy + 2), (jx + 18, jy - 8), (jx + 20, jy + 4)],
                 fill=(16, 14, 18))
    grain(draw, box, seed, 60, (90, 60, 60))
    # labels (drawn last, on top)
    pill(draw, 192, 8, "QESHM MISSILE SITES", (122, 31, 26), (246, 239, 226),
         size=9)
    pill(draw, 8, 114, "TANKER ABLAZE · OMAN", (160, 60, 20), (255, 247, 236),
         size=9)
    ribbon(draw, box, "STRAIT OF HORMUZ · US STRIKES QESHM", (122, 31, 26),
           (246, 239, 226), size=10, h=14)


def sc_kerch(draw, box, seed=21):
    x0, y0, x1, y1 = box
    # cloudy maritime sky: 3-stop gradient, cold grey-blue to pale horizon
    mid = y0 + (y1 - y0) // 2
    vgrad(draw._image, (x0, y0, x1, mid), (70, 90, 118), (150, 162, 172))
    vgrad(draw._image, (x0, mid, x1, y1), (150, 162, 172), (200, 208, 212))
    # faint Crimea coast on the right, behind the bridge
    draw.polygon([(x0 + 190, y1 - 56), (x0 + 230, y1 - 72), (x0 + 275, y1 - 60),
                  (x1, y1 - 66), (x1, y1 - 44), (x0 + 190, y1 - 44)],
                 fill=(158, 168, 176))
    # broken bridge deck
    deck_y = y0 + (y1 - y0) * 0.42
    draw.line((x0, deck_y, x0 + 78, deck_y), fill=(30, 30, 34), width=5)
    draw.line((x0 + 118, deck_y + 26, x1, deck_y + 30), fill=(30, 30, 34), width=5)
    draw.line((x0 + 78, deck_y, x0 + 96, deck_y + 44), fill=(30, 30, 34), width=4)
    draw.line((x0 + 100, deck_y + 46, x0 + 118, deck_y + 26), fill=(30, 30, 34), width=4)
    # pylons
    draw.rectangle((x0 + 34, deck_y - 34, x0 + 38, deck_y), fill=(30, 30, 34))
    draw.rectangle((x1 - 30, deck_y + 30 - 30, x1 - 26, deck_y + 30), fill=(30, 30, 34))
    # stopped cars and a truck on the left span
    for vx, vw in ((24, 12), (44, 10), (62, 14)):
        draw.rectangle((vx, deck_y - 8, vx + vw, deck_y - 2), fill=(20, 22, 28))
        draw.ellipse((vx + 2, deck_y - 2, vx + 5, deck_y + 1), fill=(10, 10, 12))
        draw.ellipse((vx + vw - 5, deck_y - 2, vx + vw - 2, deck_y + 1),
                     fill=(10, 10, 12))
    # smoke in 3 layers: dark base, mid grey, pale top
    for cx, cy, r, col in ((x0 + 92, deck_y - 6, 12, (60, 58, 54)),
                           (x0 + 100, deck_y - 16, 10, (120, 118, 112)),
                           (x0 + 104, deck_y - 26, 8, (180, 178, 172))):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    # water + fallen span + splash where the span hits the sea
    sea(draw, (x0, y1 - 46, x1, y1), (52, 84, 108), seed + 1, waves=3)
    draw.polygon([(x0 + 84, y1 - 40), (x0 + 112, y1 - 46), (x0 + 120, y1 - 30),
                  (x0 + 92, y1 - 24)], fill=(24, 24, 28))
    rnd = random.Random(seed + 3)
    for _ in range(12):
        sx = rnd.randint(x0 + 92, x0 + 126)
        sy = rnd.randint(y1 - 44, y1 - 28)
        draw.ellipse((sx - 2, sy - 2, sx + 2, sy + 2), fill=(240, 244, 248))
    grain(draw, box, seed, 50, (90, 90, 95))
    # labels (drawn last, on top)
    pill(draw, 8, 8, "TRAFFIC HALTED", (122, 31, 26), (245, 247, 248), size=9)
    pill(draw, 204, 8, "KYIV: DNIPRO HIT", (29, 53, 73), (245, 247, 248),
         size=9)
    ribbon(draw, box, "KERCH BRIDGE · SPAN COLLAPSES INTO SEA", (29, 53, 73),
           (245, 247, 248), size=10, h=14)


def sc_manila(draw, box, seed=31):
    x0, y0, x1, y1 = box
    # warm diplomatic dusk: terracotta to pale gold (no longer Hero 1's twin)
    vgrad(draw._image, (x0, y0, x1, y1), (190, 110, 70), (255, 205, 130))
    sun(draw, x0 + (x1 - x0) * 0.5, y0 + (y1 - y0) * 0.42, 18, (255, 232, 150))
    silhouette_city(draw, x0, y1 - 22, x1, (22, 26, 40), seed, 20, 58)
    # summit inset, right-centre: bright frame, curved table, 4 delegates
    ix0, iy0, ix1, iy1 = 195, 55, 305, 118
    draw.rounded_rectangle((ix0 + 3, iy0 + 3, ix1 + 3, iy1 + 3), radius=4,
                           fill=(0, 0, 0, 50))
    draw.rounded_rectangle((ix0, iy0, ix1, iy1), radius=4, fill=(250, 242, 224),
                           outline=(150, 80, 40), width=2)
    draw.rectangle((ix0 + 8, iy0 + 38, ix1 - 8, iy0 + 52), fill=(122, 31, 26))
    for fx in (ix0 + 16, ix0 + 42, ix0 + 68, ix0 + 90):
        draw.ellipse((fx - 4, iy0 + 14, fx + 4, iy0 + 22), fill=(40, 32, 28))
        draw.rectangle((fx - 6, iy0 + 22, fx + 6, iy0 + 38), fill=(40, 32, 28))
    # protesters, bottom-left: figures + placards + searchlights
    rnd = random.Random(seed + 2)
    for bx, by in ((30, 96), (66, 92), (102, 98)):
        draw.line((bx, by, bx, by + 26), fill=(20, 18, 16), width=2)
        draw.rectangle((bx - 12, by - 2, bx + 12, by + 10), fill=(245, 242, 232),
                       outline=(20, 18, 16))
    for _ in range(10):
        cx = rnd.randint(x0 + 8, x0 + 158)
        draw.ellipse((cx - 3, y1 - 34, cx + 3, y1 - 28), fill=(16, 16, 20))
        draw.rectangle((cx - 4, y1 - 28, cx + 4, y1 - 22), fill=(16, 16, 20))
    for sx in (44, 128):
        draw.line((sx, y1 - 22, sx - 14, y0 + 40), fill=(255, 244, 200), width=2)
        draw.line((sx, y1 - 22, sx + 10, y0 + 52), fill=(255, 244, 200), width=1)
    # 4 Quad flags, top-right
    fx = 242
    flag(draw, fx, 20, 14, 9, [(176, 42, 32), (255, 255, 255), (176, 42, 32),
                               (255, 255, 255), (176, 42, 32)])
    draw.rectangle((fx, 20, fx + 6, 24), fill=(31, 58, 95))
    flag(draw, fx + 17, 20, 14, 9, [(220, 120, 40), (255, 255, 255),
                                    (40, 120, 60)])
    draw.ellipse((fx + 22, 22, fx + 26, 26), fill=(31, 58, 95))
    flag(draw, fx + 34, 20, 14, 9, [(255, 255, 255)])
    draw.ellipse((fx + 38, 22, fx + 44, 27), fill=(176, 42, 32))
    flag(draw, fx + 51, 20, 14, 9, [(31, 58, 95)])
    draw.rectangle((fx + 51, 20, fx + 57, 24), fill=(176, 42, 32))
    draw.rectangle((fx + 51, 25, fx + 57, 29), fill=(255, 255, 255))
    grain(draw, box, seed, 50, (120, 90, 60))
    # labels (drawn last, on top)
    pill(draw, 8, 20, "100s ARRESTED", (30, 28, 26), (245, 242, 232), size=9)
    pill(draw, 222, 126, "NVIDIA RECORD", (34, 120, 60), (255, 255, 255),
         size=9)
    ribbon(draw, box, "MANILA · TRUMP AT ASEAN/QUAD SUMMIT", (181, 123, 27),
           (20, 20, 20), top=True, size=10, h=14)


def sc_tanker(draw, box, seed=41):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (30, 40, 66), (120, 90, 80))
    # orange glow behind the flames (translucent on the RGBA layer)
    draw.ellipse((x0 + 24, y0 - 6, x0 + 92, y0 + 42), fill=(255, 140, 50, 70))
    # tanker hull + superstructure
    draw.polygon([(x0 + 12, y1 - 52), (x0 + 26, y1 - 58), (x1 - 20, y1 - 58),
                  (x1 - 8, y1 - 52), (x1 - 8, y1 - 40), (x0 + 12, y1 - 40)],
                 fill=(18, 18, 22))
    draw.rectangle((x0 + 88, y1 - 74, x0 + 108, y1 - 58), fill=(18, 18, 22))
    draw.rectangle((x0 + 80, y1 - 72, x0 + 88, y1 - 58), fill=(60, 40, 30))
    draw.rectangle((x0 + 20, y1 - 56, x0 + 76, y1 - 54), fill=(40, 40, 44))
    # flames
    for cx, cy, r, col in ((x0 + 52, y1 - 66, 12, (255, 140, 40)),
                           (x0 + 66, y1 - 74, 9, (255, 190, 80)),
                           (x0 + 40, y1 - 70, 7, (230, 90, 30))):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    # smoke slanting up-right, fully inside the frame
    for cx, cy, r in ((x0 + 48, y1 - 62, 7), (x0 + 58, y1 - 70, 8),
                      (x0 + 70, y1 - 76, 6)):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(90, 86, 84))
    sea(draw, (x0, y1 - 38, x1, y1), (44, 66, 92), seed + 1, waves=3)
    # fire reflections on the water under the hull
    for rx in (36, 58, 80):
        for k in range(3):
            draw.line((rx, y1 - 34 + k * 6, rx + 14, y1 - 34 + k * 6),
                      fill=(255, 150, 60), width=2)
    # lifeboat on the water, right
    draw.polygon([(x0 + 150, y1 - 32), (x0 + 168, y1 - 32), (x0 + 164, y1 - 26),
                  (x0 + 154, y1 - 26)], fill=(245, 242, 232))
    draw.ellipse((x0 + 156, y1 - 38, x0 + 160, y1 - 34), fill=(255, 190, 80))
    draw.ellipse((x0 + 162, y1 - 38, x0 + 166, y1 - 34), fill=(255, 190, 80))
    grain(draw, box, seed, 45, (80, 70, 70))
    # labels (drawn last, on top)
    pill(draw, 112, 5, "24 EVACUATED", (245, 242, 232), (30, 30, 34), size=8)
    ribbon(draw, box, "MUSANDAM · TARA GAS ABLAZE", (168, 67, 22),
           (255, 247, 236), size=8, h=11)


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
    # light snow in the cold sky
    rnd = random.Random(seed + 5)
    for _ in range(26):
        draw.point((rnd.randint(x0 + 2, x1 - 2), rnd.randint(y0 + 2, y0 + 36)),
                   fill=(240, 242, 244))
    # river + main bridge + second, more distant bridge
    draw.rectangle((x0, y1 - 30, x1, y1), fill=(70, 100, 130))
    draw.line((x0 + 138, y1 - 38, x1, y1 - 40), fill=(96, 102, 112), width=3)
    for px in (x0 + 152, x0 + 172):
        draw.line((px, y1 - 38, px, y1 - 30), fill=(96, 102, 112), width=2)
    draw.line((x0, y1 - 44, x1, y1 - 44), fill=(30, 30, 34), width=4)
    for px in (x0 + 30, x0 + 80, x0 + 130):
        draw.line((px, y1 - 44, px, y1 - 30), fill=(30, 30, 34), width=3)
    silhouette_city(draw, x0, y1 - 44, x1, (26, 28, 42), seed, 12, 40)
    # warm explosion glows on the main deck
    for ex in (50, 118):
        draw.ellipse((ex - 7, y1 - 51, ex + 7, y1 - 37), fill=(255, 150, 60))
        draw.ellipse((ex - 3, y1 - 47, ex + 3, y1 - 41), fill=(255, 210, 110))
    # smoke columns, fully inside the frame
    for cx in (x0 + 70, x0 + 140):
        for k, r in enumerate((8, 6, 4)):
            cy = y1 - 52 - k * 12
            draw.ellipse((cx - r, cy - r, cx + r, cy + r),
                         fill=(110, 106, 100))
    grain(draw, box, seed, 45, (100, 95, 85))
    # labels (drawn last, on top)
    pill(draw, 6, 5, "2 BRIDGES", (245, 242, 232), (30, 30, 34), size=8)
    pill(draw, 130, 58, "HEAT CUT", (180, 210, 230), (20, 40, 60), size=8)
    ribbon(draw, box, "KYIV · DNIPRO BRIDGES STRUCK", (34, 58, 82),
           (255, 255, 255), size=8, h=11)


def sc_jets(draw, box, seed=71):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (150, 178, 205), (250, 208, 160))
    sun(draw, x0 + (x1 - x0) * 0.24, y0 + (y1 - y0) * 0.62, 13, (255, 220, 140))
    # low hilly coastline on the horizon, in front of the sun's base
    draw.polygon([(x0, y1 - 26), (x0 + 50, y1 - 34), (x0 + 110, y1 - 24),
                  (x0 + 150, y1 - 30), (x1, y1 - 26), (x1, y1 - 11),
                  (x0, y1 - 11)], fill=(120, 140, 160))
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
    # interceptor climbing from the bottom-left, dashed condensation trail
    draw.line((x0 + 12, y1 - 16, x0 + 34, y1 - 30), fill=(255, 255, 255),
              width=1)
    draw.line((x0 + 20, y1 - 22, x0 + 40, y1 - 34), fill=(255, 255, 255),
              width=1)
    draw.polygon([(x0 + 34, y1 - 36), (x0 + 52, y1 - 30), (x0 + 36, y1 - 26),
                  (x0 + 40, y1 - 32)], fill=(16, 18, 26))
    draw.polygon([(x0 + 42, y1 - 34), (x0 + 48, y1 - 40), (x0 + 50, y1 - 32)],
                 fill=(16, 18, 26))
    # mini radar, bottom-right
    rcx, rcy = 165, 52
    for r in (16, 11, 6):
        draw.ellipse((rcx - r, rcy - r, rcx + r, rcy + r),
                     outline=(30, 90, 60), width=1)
    draw.line((rcx - 12, rcy + 10, rcx + 12, rcy - 8), fill=(176, 42, 32),
              width=1)
    draw.ellipse((rcx + 8, rcy - 12, rcx + 12, rcy - 8), fill=(176, 42, 32))
    grain(draw, box, seed, 40, (120, 120, 120))
    # labels (drawn last, on top): one pill, no flag next to the jets
    # (the flag made it look as if the intruding jets were Japanese)
    pill(draw, 6, 5, "2 RU JETS · JAPAN SCRAMBLES", (245, 242, 232),
         (26, 26, 26), size=8)
    ribbon(draw, box, "JAPAN · AIRSPACE VIOLATION", (158, 31, 36),
           (255, 255, 255), size=8, h=11)


def sc_gaza(draw, box, seed=81):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (96, 104, 116), (168, 164, 152))
    # layered cloud bands before the rain
    draw.ellipse((x0 + 8, y0 + 4, x0 + 90, y0 + 16), fill=(80, 86, 96))
    draw.ellipse((x0 + 100, y0 + 10, x0 + 186, y0 + 22), fill=(70, 76, 86))
    # rain streaks
    rnd = random.Random(seed)
    for _ in range(26):
        rx = rnd.randint(x0 + 4, x1 - 4)
        ry = rnd.randint(y0 + 4, y1 - 30)
        draw.line((rx, ry, rx - 3, ry + 9), fill=(210, 212, 214), width=1)
    # tents
    for i, tx in enumerate((x0 + 8, x0 + 56, x0 + 104)):
        ty = y1 - 26
        col = (196, 182, 150) if i % 2 == 0 else (176, 168, 148)
        draw.polygon([(tx, ty), (tx + 22, ty - 24), (tx + 44, ty)], fill=col)
        draw.line((tx + 22, ty - 24, tx + 22, ty), fill=(90, 84, 70), width=1)
    # small crowd in front of the ruined building, left
    for cx in (x0 + 16, x0 + 26, x0 + 36, x0 + 46):
        draw.ellipse((cx - 2, y1 - 18, cx + 2, y1 - 14), fill=(40, 36, 32))
        draw.rectangle((cx - 3, y1 - 14, cx + 3, y1 - 8), fill=(40, 36, 32))
    # closed crossing gate, bottom-right
    draw.rectangle((x0 + 142, y1 - 40, x0 + 186, y1 - 8), fill=(90, 84, 70))
    for gy in (y1 - 34, y1 - 26, y1 - 18):
        draw.line((x0 + 142, gy, x0 + 186, gy), fill=(60, 56, 48), width=2)
    draw.rectangle((x0, y1 - 8, x1, y1), fill=(110, 108, 96))
    grain(draw, box, seed, 45, (90, 90, 90))
    # labels (drawn last, on top)
    pill(draw, 6, 5, "UK·AU·CA·IT", (245, 242, 232), (30, 30, 34), size=8)
    ribbon(draw, box, "GAZA · AID ACCESS URGED", (74, 79, 44),
           (245, 242, 232), size=8, h=11)


def sc_measles(draw, box, seed=91):
    x0, y0, x1, y1 = box
    # clinical graph paper
    draw.rectangle(box, fill=(242, 239, 233))
    for gx in range(x0 + 16, x1, 16):
        draw.line((gx, y0, gx, y1), fill=(0, 120, 120, 28), width=1)
    for gy in range(y0 + 12, y1, 12):
        draw.line((x0, gy, x1, gy), fill=(0, 120, 120, 28), width=1)
    # hospital block with red cross, soft shadow
    draw.rectangle((x0 + 16, y1 - 56, x0 + 80, y1 - 10), fill=(0, 0, 0, 40))
    draw.rectangle((x0 + 14, y1 - 56, x0 + 78, y1 - 12), fill=(245, 245, 240),
                   outline=(60, 60, 60))
    draw.rectangle((x0 + 40, y1 - 50, x0 + 52, y1 - 26), fill=(176, 42, 32))
    draw.rectangle((x0 + 34, y1 - 44, x0 + 58, y1 - 32), fill=(176, 42, 32))
    for wx in (x0 + 20, x0 + 60):
        draw.rectangle((wx, y1 - 22, wx + 8, y1 - 14), fill=(120, 150, 180))
    # vial + needle between clinic and bars
    draw.rectangle((x0 + 80, y1 - 44, x0 + 88, y1 - 24), fill=(180, 210, 225))
    draw.rectangle((x0 + 80, y1 - 48, x0 + 88, y1 - 44), fill=(180, 180, 185))
    draw.line((x0 + 84, y1 - 24, x0 + 84, y1 - 16), fill=(140, 140, 145), width=1)
    # rising case bars + trend line over their tops
    bx = x0 + 92
    tops = []
    for i, h in enumerate((10, 18, 30, 44)):
        draw.rectangle((bx + i * 20, y1 - 12 - h, bx + i * 20 + 13, y1 - 12),
                       fill=(176, 42, 32) if i == 3 else (200, 90, 70))
        tops.append((bx + i * 20 + 6, y1 - 12 - h))
    for (ax, ay), (bx2, by2) in zip(tops, tops[1:]):
        draw.line((ax, ay, bx2, by2), fill=(140, 30, 26), width=1)
    draw.text((x0 + 126, y1 - 10), "2000-2026", font=font(SANS_B, 7),
              fill=(80, 80, 80))
    grain(draw, box, seed, 35, (150, 150, 150))
    # labels (drawn last, on top)
    pill(draw, 10, 12, "1ST SINCE 2000", (255, 255, 255), (176, 42, 32), size=8)
    ribbon(draw, box, "US · MEASLES STATUS LOST", (179, 38, 30),
           (255, 255, 255), top=True, size=8, h=11)


def sc_markets(draw, box, seed=101):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(18, 24, 34))
    # grid + faint exchange columns in the dark background
    for gy in range(y0 + 14, y1 - 8, 16):
        draw.line((x0 + 6, gy, x1 - 6, gy), fill=(48, 58, 74), width=1)
    for cx in (60, 100, 150):
        draw.rectangle((cx, y0, cx + 10, y1), fill=(0, 0, 0, 30))
    # falling line with a translucent red hatch under it
    pts = [(x0 + 10, y0 + 26), (x0 + 46, y0 + 34), (x0 + 82, y0 + 30),
           (x0 + 118, y0 + 48), (x0 + 152, y0 + 58), (x1 - 12, y0 + 72)]
    draw.polygon(pts + [(x1 - 12, y0 + 72), (x0 + 10, y0 + 72)],
                 fill=(140, 30, 26, 45))
    draw.line(pts, fill=(230, 70, 55), width=3)
    draw.ellipse((pts[-1][0] - 3, pts[-1][1] - 3, pts[-1][0] + 3, pts[-1][1] + 3),
                 fill=(230, 70, 55))
    # 3 green mini bars: NVIDIA's record against the falling Dow
    for bx, bh in ((12, 10), (24, 16), (36, 22)):
        draw.rectangle((bx, y0 + 68 - bh, bx + 8, y0 + 68), fill=(34, 140, 70))
    grain(draw, box, seed, 35, (60, 70, 90))
    # labels (drawn last, on top)
    pill(draw, 10, 8, "NVDA: RECORD", (34, 120, 60), (255, 255, 255), size=10)
    pill(draw, 122, 6, "DOW -849", (140, 30, 26), (255, 255, 255), size=10)
    ribbon(draw, box, "WALL STREET · DOW FALLS 849", (140, 29, 24),
           (255, 255, 255), size=8, h=11)


def sc_houthi(draw, box, seed=111):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (96, 60, 52), (238, 178, 110))
    sun(draw, x0 + (x1 - x0) * 0.68, y0 + (y1 - y0) * 0.36, 14, (255, 214, 130))
    # thin Red Sea glimpse at the far left horizon, behind the dunes
    draw.polygon([(x0, y1 - 40), (x0 + 20, y1 - 42), (x0 + 42, y1 - 38),
                  (x0 + 42, y1 - 30), (x0, y1 - 30)], fill=(60, 110, 150))
    # dunes
    draw.polygon([(x0, y1 - 34), (x0 + 50, y1 - 56), (x0 + 110, y1 - 40),
                  (x0 + 150, y1 - 52), (x1, y1 - 36), (x1, y1), (x0, y1)],
                 fill=(150, 104, 62))
    draw.polygon([(x0, y1 - 18), (x0 + 70, y1 - 30), (x1, y1 - 20),
                  (x1, y1), (x0, y1)], fill=(120, 80, 48))
    # tiered convoy: front vehicle biggest, rear ones smaller, dust behind
    for tx, w, dy in ((x0 + 14, 28, 0), (x0 + 56, 24, 2), (x0 + 96, 20, 4)):
        draw.rectangle((tx, y1 - 30 + dy, tx + w, y1 - 20), fill=(28, 22, 20))
        draw.rectangle((tx + w - 8, y1 - 36 + dy, tx + w, y1 - 30 + dy),
                       fill=(28, 22, 20))
        draw.ellipse((tx + 4, y1 - 21, tx + 9, y1 - 16), fill=(16, 14, 12))
        draw.ellipse((tx + w - 9, y1 - 21, tx + w - 4, y1 - 16),
                     fill=(16, 14, 12))
        draw.ellipse((tx - 6, y1 - 20, tx - 1, y1 - 15), fill=(200, 170, 130))
    # smoking oil tower on the far right hill
    draw.rectangle((x0 + 152, y1 - 46, x0 + 158, y1 - 32), fill=(40, 30, 24))
    draw.rectangle((x0 + 158, y1 - 36, x0 + 170, y1 - 32), fill=(40, 30, 24))
    draw.ellipse((x0 + 150, y1 - 52, x0 + 158, y1 - 44), fill=(255, 150, 60))
    draw.ellipse((x0 + 153, y1 - 56, x0 + 159, y1 - 50), fill=(120, 110, 100))
    # dashed route from the convoy toward Aden + target dot
    for i in range(6):
        sx = x0 + 120 + i * 9
        draw.line((sx, y1 - 18 - i, sx + 5, y1 - 19 - i), fill=(255, 255, 255),
                  width=1)
    draw.ellipse((x0 + 170, y1 - 26, x0 + 176, y1 - 20), fill=(176, 42, 32))
    grain(draw, box, seed, 45, (140, 100, 60))
    # labels (drawn last, on top)
    pill(draw, 6, 5, "~60 KM TO ADEN", (245, 242, 232), (30, 30, 34), size=8)
    ribbon(draw, box, "YEMEN · ~60 KM FROM ADEN", (92, 58, 30),
           (255, 247, 236), size=8, h=11)


def sc_lebanon(draw, box, seed=121):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (140, 168, 150), (226, 214, 180))
    # hills in 3 layers: misty far ridge, mid ridge, near ridge
    draw.polygon([(x0, y1 - 52), (x0 + 60, y1 - 72), (x0 + 130, y1 - 58),
                  (x1, y1 - 64), (x1, y1 - 40), (x0, y1 - 40)],
                 fill=(130, 150, 120))
    draw.polygon([(x0, y1 - 40), (x0 + 60, y1 - 66), (x0 + 130, y1 - 46),
                  (x1, y1 - 58), (x1, y1), (x0, y1)], fill=(96, 128, 84))
    draw.polygon([(x0, y1 - 22), (x0 + 80, y1 - 36), (x1, y1 - 24),
                  (x1, y1), (x0, y1)], fill=(70, 100, 62))
    # village blocks
    for vx, vw in ((x0 + 18, 16), (x0 + 44, 12), (x0 + 96, 18), (x0 + 128, 12)):
        draw.rectangle((vx, y1 - 46, vx + vw, y1 - 30), fill=(232, 224, 200),
                       outline=(90, 84, 70))
    # artillery arcs from the top-left toward the strike points
    for (ax0, ay0, ax1, ay1) in ((x0 + 10, y0 + 8, x0 + 140, y1 - 44),
                                 (x0 + 20, y0 + 4, x0 + 170, y1 - 40)):
        for i in range(10):
            t0 = i / 10.0
            t1 = (i + 0.5) / 10.0
            draw.line((ax0 + (ax1 - ax0) * t0, ay0 + (ay1 - ay0) * t0,
                       ax0 + (ax1 - ax0) * t1, ay0 + (ay1 - ay0) * t1),
                      fill=(60, 56, 48), width=1)
    # smoke columns with orange flash at the base, fully inside the frame
    for cx in (x0 + 52, x0 + 118):
        draw.ellipse((cx - 4, y1 - 50, cx + 4, y1 - 42), fill=(255, 150, 60))
        for k, r in enumerate((8, 6)):
            cy = y1 - 48 - k * 11
            draw.ellipse((cx - r, cy - r, cx + r, cy + r),
                         fill=(105, 102, 96))
    # cypress trees
    for tx in (x0 + 78, x0 + 152):
        draw.polygon([(tx, y1 - 52), (tx + 5, y1 - 30), (tx + 10, y1 - 52)],
                     fill=(40, 70, 40))
    grain(draw, box, seed, 40, (110, 110, 95))
    # labels (drawn last, on top)
    pill(draw, 6, 5, "AIR + ARTILLERY", (40, 44, 34), (245, 242, 232), size=8)
    ribbon(draw, box, "S. LEBANON · AIR & ARTILLERY", (59, 66, 48),
           (245, 242, 232), size=8, h=11)


def sc_depardieu(draw, box, seed=131):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (72, 28, 36), (150, 60, 52))
    # cinema facade, left half
    draw.rectangle((x0 + 10, y1 - 60, x0 + 108, y1 - 10), fill=(38, 22, 28),
                   outline=(200, 170, 90))
    draw.rectangle((x0 + 18, y1 - 50, x0 + 100, y1 - 32), fill=(232, 196, 90))
    draw.text((x0 + 26, y1 - 48), "CINEMA", font=font(SANS_B, 12),
              fill=(38, 22, 28))
    # doors
    draw.rectangle((x0 + 24, y1 - 28, x0 + 44, y1 - 10), fill=(90, 40, 44))
    draw.rectangle((x0 + 64, y1 - 28, x0 + 84, y1 - 10), fill=(90, 40, 44))
    # film reel, top-left
    rx, ry = x0 + 16, y0 + 14
    draw.ellipse((rx - 7, ry - 7, rx + 7, ry + 7), outline=(232, 196, 90),
                 width=2)
    for ang in (30, 150, 270):
        a = math.radians(ang)
        draw.ellipse((rx + int(4 * math.cos(a)) - 2, ry + int(4 * math.sin(a)) - 2,
                      rx + int(4 * math.cos(a)) + 2, ry + int(4 * math.sin(a)) + 2),
                     fill=(232, 196, 90))
    # courthouse portico, right: pediment + columns + base
    draw.polygon([(x0 + 118, y1 - 54), (x0 + 152, y1 - 70), (x0 + 186, y1 - 54)],
                 fill=(232, 220, 190))
    draw.rectangle((x0 + 118, y1 - 54, x0 + 186, y1 - 48), fill=(232, 220, 190))
    for cx in (x0 + 124, x0 + 149, x0 + 174):
        draw.rectangle((cx, y1 - 48, cx + 6, y1 - 14), fill=(232, 220, 190),
                       outline=(120, 108, 80))
    draw.rectangle((x0 + 118, y1 - 14, x0 + 186, y1 - 10), fill=(200, 186, 150))
    # clear vertical split between the two facades
    draw.line((x0 + 113, y1 - 60, x0 + 113, y1 - 10), fill=(200, 170, 90),
              width=2)
    # document card + gavel in front of the portico
    draw.rectangle((x0 + 130, y1 - 42, x0 + 182, y1 - 26), fill=(250, 248, 242),
                   outline=(60, 60, 60))
    draw.text((x0 + 134, y1 - 38), "PLEA: GUILTY", font=font(SANS_B, 6),
              fill=(30, 30, 30))
    draw.rectangle((x0 + 142, y1 - 21, x0 + 154, y1 - 16), fill=(150, 110, 50))
    draw.line((x0 + 154, y1 - 18, x0 + 168, y1 - 13), fill=(150, 110, 50),
              width=3)
    # press photographers in front of the cinema, with camera flashes
    for px in (x0 + 28, x0 + 48, x0 + 68, x0 + 88):
        draw.ellipse((px - 3, y1 - 24, px + 3, y1 - 18), fill=(16, 14, 16))
        draw.rectangle((px - 4, y1 - 18, px + 4, y1 - 11), fill=(16, 14, 16))
    for fx, fy in ((x0 + 45, y1 - 28), (x0 + 85, y1 - 26)):
        draw.ellipse((fx - 2, fy - 2, fx + 2, fy + 2), fill=(255, 255, 240))
    grain(draw, box, seed, 40, (120, 70, 70))
    # labels (drawn last, on top)
    ribbon(draw, box, "PARIS · GUILTY PLEA ENTERED", (107, 29, 47),
           (245, 242, 232), size=8, h=11)


def sc_outages(draw, box, seed=141):
    x0, y0, x1, y1 = box
    vgrad(draw._image, (x0, y0, x1, y1), (24, 32, 43), (50, 62, 84))
    # three distinct objects: ATC tower, server rack, desktop monitor
    # ATC tower, left
    draw.rectangle((x0 + 24, y1 - 54, x0 + 32, y1 - 24), fill=(18, 20, 28))
    draw.ellipse((x0 + 16, y1 - 68, x0 + 40, y1 - 52), fill=(18, 20, 28))
    draw.rectangle((x0 + 20, y1 - 64, x0 + 36, y1 - 56), fill=(255, 200, 90))
    draw.ellipse((x0 + 26, y1 - 70, x0 + 30, y1 - 66), fill=(230, 70, 55))
    draw.rectangle((x0 + 20, y1 - 24, x0 + 36, y1 - 20), fill=(18, 20, 28))
    # server rack, middle, with red LEDs
    draw.rectangle((x0 + 68, y1 - 64, x0 + 112, y1 - 24), fill=(14, 16, 20),
                   outline=(90, 96, 110))
    for sy in (y1 - 60, y1 - 50, y1 - 40, y1 - 30):
        draw.line((x0 + 70, sy, x0 + 110, sy), fill=(60, 66, 78), width=1)
        draw.rectangle((x0 + 102, sy + 2, x0 + 106, sy + 6), fill=(230, 70, 55))
    # desktop monitor, right, with a red X on screen
    draw.rectangle((x0 + 132, y1 - 66, x0 + 172, y1 - 30), fill=(14, 16, 20),
                   outline=(90, 96, 110))
    draw.rectangle((x0 + 136, y1 - 62, x0 + 168, y1 - 38), fill=(40, 52, 72))
    draw.line((x0 + 144, y1 - 58, x0 + 160, y1 - 42), fill=(230, 70, 55),
              width=3)
    draw.line((x0 + 160, y1 - 58, x0 + 144, y1 - 42), fill=(230, 70, 55),
              width=3)
    draw.rectangle((x0 + 148, y1 - 30, x0 + 156, y1 - 24), fill=(14, 16, 20))
    # grounded plane silhouette
    draw.polygon([(x0 + 20, y1 - 30), (x0 + 110, y1 - 30), (x0 + 128, y1 - 24),
                  (x0 + 20, y1 - 24)], fill=(14, 16, 22))
    draw.polygon([(x0 + 56, y1 - 30), (x0 + 66, y1 - 46), (x0 + 72, y1 - 30)],
                 fill=(14, 16, 22))
    # faint red glow under the devices
    draw.ellipse((x0 + 60, y1 - 26, x0 + 130, y1 - 10), fill=(200, 40, 40, 40))
    grain(draw, box, seed, 40, (70, 80, 110))
    # labels (drawn last, on top)
    pill(draw, 122, 67, "DNI: NO CYBER", (60, 64, 70), (255, 255, 255),
         size=8)
    ribbon(draw, box, "US OUTAGES · NSA & AIRPORTS", (150, 28, 28),
           (255, 255, 255), top=True, size=8, h=11)


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


# also-on story number -> (lon, lat, region colour); drawn as small dots
# on the map, under the numbered pins. Only items with a clear single
# place are listed (23 of the 34 also-on items); the rest have no
# unambiguous location and are left out rather than guessed.
DOTS = {
    14: (20, 41, (31, 58, 95)), 15: (73, 34, (120, 80, 160)),
    16: (98.4, 7.9, (120, 80, 160)), 17: (55.3, 25.2, (200, 130, 40)),
    22: (19, 47.5, (31, 58, 95)), 24: (30, -2, (60, 120, 70)),
    26: (30.5, 50.4, (31, 58, 95)), 27: (-8, 53, (31, 58, 95)),
    28: (-89, 40, (176, 42, 32)), 29: (-81, 28, (176, 42, 32)),
    30: (-77, 39, (176, 42, 32)), 31: (-122, 37, (176, 42, 32)),
    34: (50.6, 26, (200, 130, 40)), 35: (46.7, 24.6, (200, 130, 40)),
    36: (36.4, 45.4, (31, 58, 95)), 37: (37.6, 55.7, (31, 58, 95)),
    38: (56.2, 26.2, (200, 130, 40)), 39: (55.3, 25.2, (200, 130, 40)),
    41: (19.8, 41.3, (31, 58, 95)), 42: (114, 22.5, (120, 80, 160)),
    43: (-77, 39, (176, 42, 32)), 45: (45, 12.8, (200, 130, 40)),
    46: (34.5, 31.5, (200, 130, 40)),
}


def draw_map(draw, box):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(188, 208, 222))
    for poly in CONTINENTS:
        pts = [(x0 + (lon + 170) / 360.0 * (x1 - x0),
                y0 + (75 - lat) / 130.0 * (y1 - y0)) for lon, lat in poly]
        draw.polygon(pts, fill=(232, 214, 170), outline=(150, 132, 96))

    def proj(lon, lat):
        return (x0 + (lon + 170) / 360.0 * (x1 - x0),
                y0 + (75 - lat) / 130.0 * (y1 - y0))

    pin_xy = {n: proj(lon, lat) for n, (lon, lat) in PINS.items()}
    # also-on dots first, so numbered pins always sit on top. A dot is
    # placed only if it clears every pin by >= 7 px and every other dot
    # by >= 4 px; a deterministic spiral nudge is tried, then it is dropped.
    placed = []
    for n, (lon, lat, col) in sorted(DOTS.items()):
        bx, by = proj(lon, lat)
        for dx, dy in ((0, 0), (4, 0), (-4, 0), (0, 4), (0, -4), (4, 4),
                       (-4, -4), (4, -4), (-4, 4), (8, 0), (-8, 0), (0, 8),
                       (0, -8), (8, 8), (-8, -8), (8, -8), (-8, 8),
                       (12, 0), (-12, 0), (0, 12), (0, -12)):
            cx, cy = bx + dx, by + dy
            if not (x0 + 3 <= cx <= x1 - 3 and y0 + 3 <= cy <= y1 - 3):
                continue
            if any((cx - px) ** 2 + (cy - py) ** 2 < 49
                   for px, py in pin_xy.values()):
                continue
            if any((cx - px) ** 2 + (cy - py) ** 2 < 16
                   for px, py in placed):
                continue
            placed.append((cx, cy))
            draw.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=desat(col),
                         outline=(255, 255, 255), width=1)
            break
    print(f"map dots placed: {len(placed)}/{len(DOTS)}")
    for n, (lon, lat) in PINS.items():
        px, py = pin_xy[n]
        draw.ellipse((px - 7, py - 7, px + 7, py + 7), fill=PIN_REGION[n],
                     outline=(255, 255, 255), width=1)
        t = str(n)
        tw = draw.textlength(t, font=font(SANS_B, 9))
        draw.text((px - tw / 2, py - 5), t, font=font(SANS_B, 9),
                  fill=(255, 255, 255))
    # dots legend, bottom-right inside the map (on open ocean)
    ly = y1 - 10
    draw.ellipse((x1 - 88, ly - 4, x1 - 80, ly + 4), fill=(176, 42, 32),
                 outline=(255, 255, 255), width=1)
    draw.text((x1 - 77, ly - 4), "1-13", font=font(SANS_B, 8),
              fill=(30, 30, 30))
    draw.ellipse((x1 - 54, ly - 2, x1 - 50, ly + 2), fill=(120, 120, 120),
                 outline=(255, 255, 255), width=1)
    draw.text((x1 - 47, ly - 4), "14-47", font=font(SANS_B, 8),
              fill=(30, 30, 30))


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
    img = paper_grain(img)
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
