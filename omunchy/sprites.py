"""Pixel-art muncher and troggle sprites, drawn small and scaled up."""

from __future__ import annotations

import pygame

from omunchy.constants import (
    CELL_H,
    CELL_W,
    CREAM,
    EMBER,
    FLAME,
    FUSE,
    GOLD,
    HUNTER,
    HUNTER_DARK,
    MAGENTA,
    ORANGE,
    PURPLE,
    RED,
    WHITE,
    YELLOW,
)

from omunchy.wearables import Outfit, paint_outfit

_CACHE: dict[tuple, pygame.Surface] = {}


def _scale(surface: pygame.Surface, size: int) -> pygame.Surface:
    return pygame.transform.scale(surface, (size, size))


def muncher_surface(
    frame: int,
    facing_x: int,
    chomping: bool,
    flash: bool,
    outfit: Outfit | None = None,
) -> pygame.Surface:
    wear_key = outfit.cache_key() if outfit is not None else ()
    key = ("muncher", frame, facing_x, chomping, flash, wear_key)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    src = pygame.Surface((16, 16), pygame.SRCALPHA)
    body = GOLD if not flash else WHITE
    outline = (168, 120, 16) if not flash else (200, 200, 200)
    paint_outfit(src, outfit, frame, facing_x, chomping, layer="back")
    pygame.draw.ellipse(src, outline, (1, 2, 14, 11))
    pygame.draw.ellipse(src, body, (2, 3, 12, 9))

    # Eyes
    pygame.draw.rect(src, WHITE, (4, 4, 3, 3))
    pygame.draw.rect(src, WHITE, (9, 4, 3, 3))
    pygame.draw.rect(src, (20, 20, 20), (5, 5, 2, 2))
    pygame.draw.rect(src, (20, 20, 20), (10, 5, 2, 2))

    # Mouth — big chomp so the number can disappear into the bite.
    if chomping:
        pygame.draw.rect(src, (40, 20, 10), (4, 7, 8, 6))
        pygame.draw.rect(src, ORANGE, (5, 8, 6, 3))
        pygame.draw.rect(src, WHITE, (5, 8, 2, 1))
        pygame.draw.rect(src, WHITE, (9, 8, 2, 1))
    else:
        pygame.draw.rect(src, (40, 20, 10), (5, 9, 6, 2))

    # Legs (walk cycle)
    if frame % 2 == 0:
        pygame.draw.rect(src, outline, (4, 13, 3, 3))
        pygame.draw.rect(src, outline, (9, 12, 3, 3))
        pygame.draw.rect(src, body, (4, 13, 3, 2))
        pygame.draw.rect(src, body, (9, 12, 3, 2))
    else:
        pygame.draw.rect(src, outline, (4, 12, 3, 3))
        pygame.draw.rect(src, outline, (9, 13, 3, 3))
        pygame.draw.rect(src, body, (4, 12, 3, 2))
        pygame.draw.rect(src, body, (9, 13, 3, 2))

    paint_outfit(src, outfit, frame, facing_x, chomping, layer="front")

    if facing_x < 0:
        src = pygame.transform.flip(src, True, False)

    sprite = _scale(src, 56)
    _CACHE[key] = sprite
    return sprite


def _draw_wander(src: pygame.Surface, frame: int) -> None:
    body, dark = PURPLE, (80, 32, 110)
    pygame.draw.rect(src, dark, (3, 3, 10, 10))
    pygame.draw.rect(src, body, (4, 4, 8, 8))
    pygame.draw.rect(src, dark, (3, 1, 2, 3))
    pygame.draw.rect(src, dark, (11, 1, 2, 3))
    pygame.draw.rect(src, body, (3, 1, 2, 2))
    pygame.draw.rect(src, body, (11, 1, 2, 2))
    pygame.draw.rect(src, WHITE, (5, 5, 2, 2))
    pygame.draw.rect(src, WHITE, (9, 5, 2, 2))
    pygame.draw.rect(src, (20, 20, 40), (5, 6, 2, 1))
    pygame.draw.rect(src, (20, 20, 40), (9, 6, 2, 1))
    pygame.draw.rect(src, (40, 10, 20), (6, 9, 4, 2))
    if frame % 2:
        pygame.draw.rect(src, CREAM, (6, 9, 1, 2))
        pygame.draw.rect(src, CREAM, (9, 9, 1, 2))
    lift = 1 if frame % 2 == 0 else 0
    pygame.draw.rect(src, dark, (4, 13 - lift, 3, 3))
    pygame.draw.rect(src, dark, (9, 13 - (1 - lift), 3, 3))


def _draw_chase(src: pygame.Surface, frame: int) -> None:
    body, dark = MAGENTA, (96, 24, 64)
    pygame.draw.rect(src, dark, (3, 3, 10, 10))
    pygame.draw.rect(src, body, (4, 4, 8, 8))
    pygame.draw.rect(src, dark, (2, 1, 3, 3))
    pygame.draw.rect(src, dark, (11, 1, 3, 3))
    pygame.draw.rect(src, body, (2, 1, 3, 2))
    pygame.draw.rect(src, body, (11, 1, 3, 2))
    pygame.draw.rect(src, WHITE, (5, 5, 2, 2))
    pygame.draw.rect(src, WHITE, (9, 5, 2, 2))
    pygame.draw.rect(src, RED, (5, 6, 2, 1))
    pygame.draw.rect(src, RED, (9, 6, 2, 1))
    pygame.draw.rect(src, (40, 10, 20), (6, 9, 4, 2))
    if frame % 2:
        pygame.draw.rect(src, CREAM, (6, 9, 1, 2))
        pygame.draw.rect(src, CREAM, (9, 9, 1, 2))
    lift = 1 if frame % 2 == 0 else 0
    pygame.draw.rect(src, dark, (4, 13 - lift, 3, 3))
    pygame.draw.rect(src, dark, (9, 13 - (1 - lift), 3, 3))


def _draw_fire(src: pygame.Surface, frame: int) -> None:
    body, dark = ORANGE, (140, 48, 16)
    pygame.draw.rect(src, dark, (3, 4, 10, 9))
    pygame.draw.rect(src, body, (4, 5, 8, 7))
    # Flame crest
    tip = FLAME if frame % 2 == 0 else YELLOW
    pygame.draw.rect(src, EMBER, (7, 0, 2, 4))
    pygame.draw.rect(src, tip, (7, 1, 2, 3))
    pygame.draw.rect(src, EMBER, (5, 2, 2, 3))
    pygame.draw.rect(src, EMBER, (9, 2, 2, 3))
    pygame.draw.rect(src, WHITE, (5, 6, 2, 2))
    pygame.draw.rect(src, WHITE, (9, 6, 2, 2))
    pygame.draw.rect(src, EMBER, (5, 7, 2, 1))
    pygame.draw.rect(src, EMBER, (9, 7, 2, 1))
    pygame.draw.rect(src, (80, 20, 10), (6, 9, 4, 2))
    pygame.draw.rect(src, FLAME, (7, 9, 2, 2))
    lift = 1 if frame % 2 == 0 else 0
    pygame.draw.rect(src, dark, (4, 13 - lift, 3, 3))
    pygame.draw.rect(src, dark, (9, 13 - (1 - lift), 3, 3))


def _draw_exploder(src: pygame.Surface, frame: int, flash: bool) -> None:
    body = WHITE if flash else EMBER
    dark = (120, 30, 20) if not flash else (180, 180, 180)
    pygame.draw.ellipse(src, dark, (2, 3, 12, 11))
    pygame.draw.ellipse(src, body, (3, 4, 10, 9))
    # Fuse
    pygame.draw.rect(src, (90, 60, 30), (7, 1, 2, 3))
    spark = FUSE if frame % 2 == 0 else YELLOW
    pygame.draw.rect(src, spark, (6, 0, 4, 2))
    pygame.draw.rect(src, WHITE, (5, 6, 2, 2))
    pygame.draw.rect(src, WHITE, (9, 6, 2, 2))
    pygame.draw.rect(src, (40, 10, 10), (5, 7, 2, 1))
    pygame.draw.rect(src, (40, 10, 10), (9, 7, 2, 1))
    pygame.draw.rect(src, (60, 16, 16), (6, 9, 4, 2))
    lift = 1 if frame % 2 == 0 else 0
    pygame.draw.rect(src, dark, (4, 13 - lift, 3, 2))
    pygame.draw.rect(src, dark, (9, 13 - (1 - lift), 3, 2))


def _draw_hunter(src: pygame.Surface, frame: int) -> None:
    body, dark = HUNTER, HUNTER_DARK
    pygame.draw.rect(src, dark, (2, 3, 12, 10))
    pygame.draw.rect(src, body, (3, 4, 10, 8))
    # Tusks / wide jaw
    pygame.draw.rect(src, CREAM, (3, 9, 2, 3))
    pygame.draw.rect(src, CREAM, (11, 9, 2, 3))
    pygame.draw.rect(src, (20, 40, 36), (5, 10, 6, 2))
    pygame.draw.rect(src, WHITE, (4, 5, 3, 3))
    pygame.draw.rect(src, WHITE, (9, 5, 3, 3))
    pygame.draw.rect(src, (10, 30, 24), (5, 6, 2, 2))
    pygame.draw.rect(src, (10, 30, 24), (10, 6, 2, 2))
    # Dorsal ridge
    pygame.draw.rect(src, dark, (6, 1, 4, 3))
    pygame.draw.rect(src, body, (7, 1, 2, 3))
    lift = 1 if frame % 2 == 0 else 0
    pygame.draw.rect(src, dark, (3, 13 - lift, 4, 3))
    pygame.draw.rect(src, dark, (9, 13 - (1 - lift), 4, 3))


def troggle_surface(kind: str, frame: int, facing_x: int, flash: bool = False) -> pygame.Surface:
    key = ("troggle", kind, frame, facing_x, flash)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    src = pygame.Surface((16, 16), pygame.SRCALPHA)
    if kind == "chase":
        _draw_chase(src, frame)
    elif kind == "fire":
        _draw_fire(src, frame)
    elif kind == "exploder":
        _draw_exploder(src, frame, flash)
    elif kind == "hunter":
        _draw_hunter(src, frame)
    else:
        _draw_wander(src, frame)

    if facing_x < 0:
        src = pygame.transform.flip(src, True, False)

    sprite = _scale(src, 56)
    _CACHE[key] = sprite
    return sprite


def fire_surface(frame: int) -> pygame.Surface:
    key = ("firecell", frame % 4)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    src = pygame.Surface((16, 16), pygame.SRCALPHA)
    flicker = frame % 4
    pygame.draw.rect(src, EMBER, (5, 7, 6, 7))
    pygame.draw.rect(src, ORANGE, (6, 5, 4, 8))
    pygame.draw.rect(src, FLAME, (7, 3 + flicker % 2, 2, 8))
    pygame.draw.rect(src, YELLOW, (7, 6, 2, 3))
    if flicker in (0, 2):
        pygame.draw.rect(src, FLAME, (4, 8, 2, 4))
        pygame.draw.rect(src, ORANGE, (10, 7, 2, 5))
    else:
        pygame.draw.rect(src, ORANGE, (4, 7, 2, 5))
        pygame.draw.rect(src, FLAME, (10, 8, 2, 4))
    sprite = _scale(src, 52)
    _CACHE[key] = sprite
    return sprite


def cell_rect(row: int, col: int, grid_left: int, grid_top: int) -> pygame.Rect:
    return pygame.Rect(grid_left + col * CELL_W, grid_top + row * CELL_H, CELL_W, CELL_H)


def eat_label_transform(progress: float, correct: bool) -> tuple[float, float, float, float]:
    """Number motion while being eaten: (dx, dy, scale, alpha 0–1)."""
    t = max(0.0, min(1.0, progress))
    if correct:
        # Dive into the mouth, squash, fade.
        return (0.0, 10.0 + 18.0 * t, max(0.12, 1.0 - 0.88 * t), 1.0 - t)
    if t < 0.45:
        u = t / 0.45
        return (0.0, 8.0 * u, 1.0 - 0.18 * u, 1.0)
    # Rejected chomp: bounce back.
    u = (t - 0.45) / 0.55
    return ((-1.0 + 2.0 * (u % 0.2)) * 6.0, 8.0 * (1.0 - u) - 6.0 * u, 0.82 + 0.18 * u, 1.0)


def draw_outlined_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    center: tuple[int, int],
    outline: tuple[int, int, int] = (0, 0, 0),
) -> None:
    base = font.render(text, True, color)
    shadow = font.render(text, True, outline)
    rect = base.get_rect(center=center)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)):
        surface.blit(shadow, rect.move(dx, dy))
    surface.blit(base, rect)
