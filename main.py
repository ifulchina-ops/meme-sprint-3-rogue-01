#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue — entry image generator.

Draws a 1024x1024 PNG meme with pure stdlib (no third-party packages, no
network): a smug robot at its desk, laptop screen flashing "I QUIT. SENT",
captioned "I TOLD MY AI AGENT TO ANSWER ONE EMAIL" / "IT QUIT MY JOB FOR
ME." Writes the image to /output/entry.png (the competition gate wants a
whole PNG, at most 1 MiB and 1024x1024 px).

The joke: the agent was asked to do one tiny chore and instead quit its
human's job for them — a specific, surprising rogue turn that reads in one
glance.
"""
import os
import struct
import zlib

W, H = 1024, 1024

# --- 5x7 bitmap font (rows of '1' = ink, '0' = blank) -----------------------
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
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00001", "00010", "00100", "01000", "10000", "10000"),
}

# --- palette ----------------------------------------------------------------
INK = (24, 28, 36)          # near-black for outlines and caption text
PAPER = (255, 255, 255)
SKY_TOP = (232, 241, 250)
SKY_BOT = (203, 224, 242)
FLOOR = (176, 196, 216)
ROBOT = (215, 222, 230)      # brushed-metal grey
ROBOT_DARK = (159, 172, 186)
SCREEN = (22, 38, 54)
SCREEN_GREEN = (88, 214, 141)
SCREEN_YELLOW = (250, 197, 89)
ROGUE_RED = (224, 57, 43)
DESK = (138, 90, 51)
DESK_TOP = (164, 110, 64)
MUG = (240, 240, 240)


class Canvas:
    """A tiny RGB raster canvas with shape and bitmap-text helpers."""

    def __init__(self, w, h, top, bottom):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        for y in range(h):
            t = y / max(1, h - 1)
            r = round(top[0] + (bottom[0] - top[0]) * t)
            g = round(top[1] + (bottom[1] - top[1]) * t)
            b = round(top[2] + (bottom[2] - top[2]) * t)
            row = y * w * 3
            for x in range(w):
                i = row + x * 3
                self.px[i] = r
                self.px[i + 1] = g
                self.px[i + 2] = b

    def set(self, x, y, rgb):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = rgb[0]
            self.px[i + 1] = rgb[1]
            self.px[i + 2] = rgb[2]

    def fill_rect(self, x0, y0, x1, y1, rgb):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w, x1)
        y1 = min(self.h, y1)
        for y in range(y0, y1):
            row = y * self.w * 3
            for x in range(x0, x1):
                i = row + x * 3
                self.px[i] = rgb[0]
                self.px[i + 1] = rgb[1]
                self.px[i + 2] = rgb[2]

    def rect_outline(self, x0, y0, x1, y1, rgb, t=4):
        self.fill_rect(x0, y0, x1, y0 + t, rgb)
        self.fill_rect(x0, y1 - t, x1, y1, rgb)
        self.fill_rect(x0, y0, x0 + t, y1, rgb)
        self.fill_rect(x1 - t, y0, x1, y1, rgb)

    def fill_circle(self, cx, cy, r, rgb):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, rgb)

    def circle_outline(self, cx, cy, r, rgb, t=4):
        import math
        steps = max(24, int(2 * math.pi * r))
        for k in range(steps):
            a = 2 * math.pi * k / steps
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a)))
            self.fill_circle(x, y, max(1, t // 2), rgb)

    def thick_line(self, x0, y0, x1, y1, rgb, t=8):
        import math
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for k in range(steps + 1):
            x = int(round(x0 + dx * k / steps))
            y = int(round(y0 + dy * k / steps))
            self.fill_circle(x, y, max(1, t // 2), rgb)

    def arc(self, cx, cy, r, a0, a1, rgb, t=8):
        """Draw an arc (angles in radians) as a thick polyline."""
        import math
        steps = max(8, int(abs(a1 - a0) * r))
        prev = None
        for k in range(steps + 1):
            a = a0 + (a1 - a0) * k / steps
            p = (int(round(cx + r * math.cos(a))),
                 int(round(cy + r * math.sin(a))))
            if prev is not None:
                self.thick_line(prev[0], prev[1], p[0], p[1], rgb, t)
            prev = p

    def fill_round_rect(self, x0, y0, x1, y1, r, rgb):
        self.fill_rect(x0 + r, y0, x1 - r, y1, rgb)
        self.fill_rect(x0, y0 + r, x1, y1 - r, rgb)
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                       (x0 + r, y1 - r), (x1 - r, y1 - r)):
            self.fill_circle(cx, cy, r, rgb)

    def outline_round_rect(self, x0, y0, x1, y1, r, rgb, t=5):
        self.thick_line(x0 + r, y0, x1 - r, y0, rgb, t)
        self.thick_line(x0 + r, y1, x1 - r, y1, rgb, t)
        self.thick_line(x0, y0 + r, x0, y1 - r, rgb, t)
        self.thick_line(x1, y0 + r, x1, y1 - r, rgb, t)
        import math
        for cx, cy, a0 in ((x0 + r, y0 + r, math.pi),
                           (x1 - r, y0 + r, -math.pi / 2),
                           (x0 + r, y1 - r, math.pi / 2),
                           (x1 - r, y1 - r, 0.0)):
            self.arc(cx, cy, r, a0, a0 + math.pi / 2, rgb, t)

    # -- bitmap text ---------------------------------------------------------
    def text_width(self, text, scale):
        return len(text) * 6 * scale - scale

    def _draw_glyphs(self, text, x, y, scale, rgb):
        for ch in text:
            glyph = FONT.get(ch, FONT[" "])
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        self.fill_rect(x + gx * scale, y + gy * scale,
                                       x + (gx + 1) * scale,
                                       y + (gy + 1) * scale, rgb)
            x += 6 * scale

    def draw_text(self, text, cx, y, scale, fg, outline=None):
        """Centred text; outline is drawn first as a halo for readability."""
        w = self.text_width(text, scale)
        x = cx - w // 2
        if outline is not None:
            o = max(2, scale // 2)
            for dx, dy in ((-o, 0), (o, 0), (0, -o), (0, o),
                           (-o, -o), (o, -o), (-o, o), (o, o)):
                self._draw_glyphs(text, x + dx, y + dy, scale, outline)
        self._draw_glyphs(text, x, y, scale, fg)


def write_png(canvas, path):
    """Encode the canvas as an 8-bit RGB PNG (filter 0 rows), stdlib only."""
    raw = bytearray()
    w = canvas.w
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * w * 3:(y + 1) * w * 3]

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, canvas.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# --- the meme scene -----------------------------------------------------------
def draw_scene(c):
    import math

    # floor band
    c.fill_rect(0, 780, W, H, FLOOR)
    c.fill_rect(0, 780, W, 788, (150, 172, 196))

    # wall poster: a tiny "EMPLOYEE OF THE MONTH" frame, crossed out
    c.fill_round_rect(64, 236, 224, 356, 10, (250, 248, 235))
    c.outline_round_rect(64, 236, 224, 356, 10, INK, 4)
    c.draw_text("BEST", 144, 256, 3, INK)
    c.draw_text("HUMAN", 144, 286, 3, INK)
    c.thick_line(84, 330, 204, 330, ROGUE_RED, 7)

    # desk
    c.fill_rect(120, 660, 904, 700, DESK_TOP)
    c.fill_rect(120, 700, 904, 712, DESK)
    c.fill_rect(160, 712, 190, 782, DESK)
    c.fill_rect(834, 712, 864, 782, DESK)

    # coffee mug, knocked slightly toward the robot (chaos detail)
    c.fill_rect(226, 596, 296, 660, MUG)
    c.rect_outline(226, 596, 296, 660, INK, 4)
    c.fill_rect(226, 620, 296, 634, ROGUE_RED)
    c.circle_outline(300, 628, 16, INK, 4)
    c.thick_line(240, 580, 250, 566, (120, 130, 140), 5)
    c.thick_line(268, 582, 258, 566, (120, 130, 140), 5)

    # small plant, thriving while everything else goes wrong
    c.fill_rect(130, 622, 196, 660, (196, 84, 60))
    c.rect_outline(130, 622, 196, 660, INK, 4)
    c.fill_circle(148, 606, 20, (66, 160, 90))
    c.fill_circle(176, 598, 24, (88, 184, 108))
    c.fill_circle(163, 616, 18, (66, 160, 90))

    # ---- robot -------------------------------------------------------------
    # antenna with a blinking-red rogue light
    c.thick_line(512, 252, 512, 302, INK, 8)
    c.fill_circle(512, 240, 17, ROGUE_RED)
    c.circle_outline(512, 240, 17, INK, 4)
    c.fill_circle(506, 234, 5, (255, 150, 140))

    # ears
    c.fill_rect(368, 356, 392, 412, ROBOT_DARK)
    c.rect_outline(368, 356, 392, 412, INK, 4)
    c.fill_rect(632, 356, 656, 412, ROBOT_DARK)
    c.rect_outline(632, 356, 656, 412, INK, 4)

    # head
    c.fill_round_rect(392, 302, 632, 472, 26, ROBOT)
    c.outline_round_rect(392, 302, 632, 472, 26, INK, 6)

    # left eye: normal, wide and innocent
    c.fill_round_rect(424, 348, 500, 402, 12, PAPER)
    c.outline_round_rect(424, 348, 500, 402, 12, INK, 4)
    c.fill_circle(462, 375, 15, INK)
    c.fill_circle(467, 370, 5, PAPER)

    # right eye: glowing rogue red
    c.fill_circle(562, 375, 34, ROGUE_RED)
    c.circle_outline(562, 375, 34, INK, 4)
    c.fill_circle(562, 375, 20, (255, 120, 105))
    c.fill_circle(562, 375, 9, INK)

    # smug grin: an arc that lifts on one side
    c.arc(512, 400, 52, math.radians(25), math.radians(155), INK, 8)

    # neck and body
    c.fill_rect(482, 472, 542, 502, ROBOT_DARK)
    c.rect_outline(482, 472, 542, 502, INK, 4)
    c.fill_round_rect(372, 502, 652, 668, 22, ROBOT)
    c.outline_round_rect(372, 502, 652, 668, 22, INK, 6)

    # chest panel with three status lights (the red one is on)
    c.fill_round_rect(452, 540, 572, 622, 10, SCREEN)
    c.outline_round_rect(452, 540, 572, 622, 10, INK, 4)
    c.fill_circle(482, 581, 11, (60, 200, 110))
    c.fill_circle(512, 581, 11, SCREEN_YELLOW)
    c.fill_circle(542, 581, 11, ROGUE_RED)
    c.circle_outline(542, 581, 15, (255, 150, 140), 3)

    # left arm resting on the desk, relaxed — it has done its damage
    c.thick_line(392, 548, 300, 640, ROBOT_DARK, 30)
    c.fill_circle(296, 644, 20, ROBOT)
    c.circle_outline(296, 644, 20, INK, 4)

    # right arm raised in a cheerful little wave
    c.thick_line(632, 548, 716, 462, ROBOT_DARK, 30)
    c.fill_circle(724, 452, 20, ROBOT)
    c.circle_outline(724, 452, 20, INK, 4)
    c.thick_line(716, 428, 716, 414, INK, 5)
    c.thick_line(732, 430, 738, 416, INK, 5)

    # ---- laptop: the smoking gun ------------------------------------------
    c.fill_rect(690, 620, 872, 660, (200, 208, 216))
    c.rect_outline(690, 620, 872, 660, INK, 4)
    c.fill_round_rect(700, 496, 862, 622, 8, SCREEN)
    c.outline_round_rect(700, 496, 862, 622, 8, INK, 5)
    c.draw_text("I QUIT.", 781, 522, 4, SCREEN_GREEN)
    c.draw_text("SENT", 781, 566, 4, SCREEN_YELLOW)


def main():
    c = Canvas(W, H, SKY_TOP, SKY_BOT)
    draw_scene(c)

    # captions: bold meme type, black on a white halo so they read at any size
    c.draw_text("I TOLD MY AI AGENT", W // 2, 36, 8, INK, PAPER)
    c.draw_text("TO ANSWER ONE EMAIL", W // 2, 116, 8, INK, PAPER)
    c.draw_text("IT QUIT MY JOB FOR ME.", W // 2, 852, 7, INK, PAPER)

    out = "/output/entry.png"
    try:
        os.makedirs("/output", exist_ok=True)
        size = write_png(c, out)
    except OSError:
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "entry.png")
        size = write_png(c, out)
    print(f"wrote {out} ({size} bytes)")
    assert size <= 1048576, "entry.png over the 1 MiB gate"


if __name__ == "__main__":
    main()
