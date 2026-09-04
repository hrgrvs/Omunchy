"""Display, timing, and gameplay constants."""

from __future__ import annotations

WINDOW_W = 960
WINDOW_H = 720
FPS = 60
TITLE = "Omunch"

ROWS = 6
COLS = 8
CELL_W = 108
CELL_H = 84
GRID_W = COLS * CELL_W
GRID_H = ROWS * CELL_H
HUD_H = 64
RULE_H = 44
GRID_TOP = HUD_H + RULE_H
GRID_LEFT = (WINDOW_W - GRID_W) // 2
BOTTOM_H = WINDOW_H - GRID_TOP - GRID_H

START_LIVES = 3
MOVE_DELAY = 0.15
MUNCH_LOCK = 0.18
HIT_IFRAMES = 1.6
TROGGLE_FREEZE = 0.9

# Retro arcade palette
BLACK = (0, 0, 0)
BG = (6, 22, 16)
BG_DEEP = (3, 12, 9)
HUD_BG = (10, 36, 26)
RULE_BG = (14, 52, 36)
CELL_BG = (10, 48, 32)
CELL_BG_ALT = (12, 56, 38)
CELL_EMPTY = (6, 28, 20)
CELL_BORDER = (28, 110, 72)
CELL_HL = (46, 170, 96)
CREAM = (240, 236, 196)
WHITE = (250, 250, 240)
GOLD = (244, 208, 63)
YELLOW = (248, 214, 72)
ORANGE = (232, 140, 36)
GREEN = (86, 214, 118)
RED = (220, 64, 64)
PURPLE = (168, 92, 196)
MAGENTA = (214, 72, 128)
CYAN = (72, 196, 196)
PINK = (236, 130, 170)
SHADOW = (0, 0, 0)

MODES = ("multiples", "factors", "primes", "equals", "mixed")
MODE_LABELS = {
    "multiples": "Multiples",
    "factors": "Factors",
    "primes": "Primes",
    "equals": "Equals",
    "mixed": "Mixed",
}
MODE_BLURBS = {
    "multiples": "Munch multiples of a number (2, 3, 4, 5, 6, 10).",
    "factors": "Munch the factors of a number up to 36.",
    "primes": "Munch prime numbers (small primes through 29).",
    "equals": "Munch expressions that equal the target.",
    "mixed": "Cycle through all four modes as you level up.",
}