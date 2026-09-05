"""Milestone celebration every N cleared levels."""

from __future__ import annotations

CELEBRATE_EVERY = 3
CELEBRATE_SECONDS = 2.8

BANNERS = ("Nice!", "Level up!", "Great job!", "Way to go!")


def is_celebration_level(level: int, every: int = CELEBRATE_EVERY) -> bool:
    return level > 0 and level % every == 0


def banner_for_level(level: int) -> str:
    index = max(0, level // CELEBRATE_EVERY - 1)
    return BANNERS[index % len(BANNERS)]