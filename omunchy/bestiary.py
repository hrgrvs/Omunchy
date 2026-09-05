"""Kid-friendly Troggle field guide (title / pause page)."""

from __future__ import annotations

# kind, short name, one-line behavior — keep each line readable on 16:9.
TROGGLE_GUIDE: tuple[tuple[str, str, str], ...] = (
    ("wander", "Wander", "Walks around at random."),
    ("chase", "Chase", "Follows you."),
    ("fire", "Fire-breath", "Lights the square in front."),
    ("exploder", "Exploder", "Pops on side-adjacent squares after a warning."),
    ("hunter", "Hunter", "Eats other Troggles; still hurts you on contact."),
)

TITLE_MENU = ("Play", "Troggles")
PAUSE_MENU = ("Resume", "Troggles", "Title")
