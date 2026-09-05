"""Display, timing, and gameplay constants."""

from __future__ import annotations

# 16:9 logical frame — fills typical laptop screens; pygame.SCALED letterboxes.
WINDOW_W = 1280
WINDOW_H = 720
FPS = 60
TITLE = "Omunchy"

# Full-size board (late levels). Early levels use a smaller grid that grows here.
MAX_ROWS = 6
MAX_COLS = 8
ROWS = MAX_ROWS
COLS = MAX_COLS
CELL_W = 108
CELL_H = 84
GRID_W = MAX_COLS * CELL_W
GRID_H = MAX_ROWS * CELL_H
HUD_H = 64
RULE_H = 44
GRID_TOP = HUD_H + RULE_H
GRID_LEFT = (WINDOW_W - GRID_W) // 2
HINT_H = 48
BOTTOM_H = HINT_H

START_LIVES = 3
MOVE_DELAY = 0.15
MUNCH_LOCK = 0.32
HIT_IFRAMES = 1.6
TROGGLE_FREEZE = 0.9

# Kid-fair Troggle pace (grades 2–5). Higher interval = slower / less aggressive.
# Nudged a little slower again vs the previous curve; kinds keep their spread.
TROGGLE_INTERVAL_START = 1.48
TROGGLE_INTERVAL_STEP = 0.030
TROGGLE_INTERVAL_FLOOR = 0.76
TROGGLE_KIND_INTERVAL_MIN = 0.70

# Fire-breath: longer wind-up so kids can step off the front square.
FIRE_WINDUP = 0.66
# How long a burning cell stays lit. Linger is independent of the Troggle pose.
FIRE_DURATION = 1.20
# Short breath pose / lock after a cell ignites.
FIRE_BREATH = 0.42
FIRE_COOLDOWN = 3.05
# Oldest flame goes out when a third cell would ignite.
MAX_ACTIVE_FIRES = 2

# Telegraph before a Troggle walks onto the board (mid-level refill).
SPAWN_TELEGRAPH = 0.80

# Player-facing hero name. Package / window title stay Omunchy.
HERO_NAME = "Munchy"

# Exploder: 4-dir (cardinal) adjacency only — diagonal is safe for kids.
EXPLODE_WINDUP = 0.90

# Munch / eat animation (number squash into the bite).
EAT_CORRECT = 0.34
EAT_WRONG = 0.40

# Retro arcade palette
BLACK = (0, 0, 0)
BG = (6, 22, 16)
BG_DEEP = (3, 12, 9)
HUD_BG = (10, 36, 26)
RULE_BG = (14, 52, 36)
# Number cells: near-black plates so digits jump out (grades 2–5, 16:9).
# Avoid mid-green + cream, which reads muddy at fullscreen.
CELL_BG = (6, 16, 14)
CELL_BG_ALT = (16, 32, 26)
CELL_EMPTY = (3, 8, 7)
CELL_EMPTY_BORDER = (16, 40, 30)
CELL_BORDER = (48, 108, 78)
CELL_HL = (96, 255, 148)
CELL_DIGIT = (255, 255, 245)
CREAM = (240, 236, 196)
WHITE = (250, 250, 240)
# Get-ready overlay: heavy black fade so board content cannot compete with text.
INTRO_DIM_ALPHA = 228
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
FLAME = (255, 168, 48)
EMBER = (220, 72, 28)
HUNTER = (36, 150, 132)
HUNTER_DARK = (12, 72, 64)
FUSE = (255, 220, 80)

MODES = ("multiples", "factors", "primes", "equals", "pairings")
MODE_LABELS = {
    "multiples": "Multiples",
    "factors": "Factors",
    "primes": "Primes",
    "equals": "Equals",
    "pairings": "Pairings",
}
MODE_BLURBS = {
    "multiples": "Munch multiples of a number (2 through 20, in order).",
    "factors": "Munch the factors of a number up to 36.",
    "primes": "Munch prime numbers (small primes through 29).",
    "equals": "Munch expressions that equal the target.",
    "pairings": "Grab one number, then eat it with a partner that makes 10, then 100, then 1000.",
}


# Pixel sizes (16×16 art scaled up). Munchy fills the cell; Troggles vary.
MUNCHY_SPRITE_SIZE = 80
TROGGLE_SPRITE_SIZES = {
    "wander": 40,
    "chase": 52,
    "fire": 62,
    "exploder": 48,
    "hunter": 70,
}


def grid_geometry(rows: int, cols: int) -> tuple[int, int, int, int]:
    """Centered (left, top, width, height) for the current board size."""
    grid_w = cols * CELL_W
    grid_h = rows * CELL_H
    grid_left = (WINDOW_W - grid_w) // 2
    available = WINDOW_H - HUD_H - RULE_H - HINT_H
    grid_top = HUD_H + RULE_H + max(0, (available - grid_h) // 2)
    return grid_left, grid_top, grid_w, grid_h
