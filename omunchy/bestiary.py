"""Kid-friendly Troggle field guide (title / pause page)."""

from __future__ import annotations

# kind, short name, one-line behavior — keep each line readable on 16:9.
TROGGLE_GUIDE: tuple[tuple[str, str, str], ...] = (
    ("wander", "Wander", "Walks at random; bumps Munchy back (safe)."),
    ("chase", "Chase", "Follows Munchy; big eyes track him."),
    ("fire", "Fire-breath", "Burns the front square; Munchy loses a life on it."),
    ("exploder", "Exploder", "Pops on side-adjacent squares after a warning."),
    ("hunter", "Hunter", "Eats other Troggles; still hurts Munchy on contact."),
)

TITLE_MENU = ("Play", "Troggles")
PAUSE_MENU = ("Resume", "Troggles", "Title")
