"""Pixel-art muncher and troggle sprites, drawn small and scaled up."""

from __future__ import annotations

import pygame

from omunch.constants import (
    CELL_H,
    CELL_W,
    CREAM,
    GOLD,
    MAGENTA,
    ORANGE,
    PURPLE,
    RED,
    WHITE,
    YELLOW,
)

_CACHE: dict[tuple, pygame.Surface] = {}


def _scale(surface: pygame.Surface, size: int) -> pygame.Surface:
    return pygame.transform.scale(surface, (size, size))


def muncher_surface(frame: int, facing_x: int, chomping: bool, flash: bool) -> pygame.Surface:
    key = ("muncher", frame, facing_x, chomping, flash)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    src = pygame.Surface((16, 16), pygame.SRCALPHA)
    body = GOLD if not flash else WHITE
    outline = (168, 120, 16) if not flash else (200, 200, 200)
    pygame.draw.ellipse(src, outline, (1, 2, 14, 11))
    pygame.draw.ellipse(src, body, (2, 3, 12, 9))

    # Eyes
    pygame.draw.rect(src, WHITE, (4, 4, 3, 3))
    pygame.draw.rect(src, WHITE, (9, 4, 3, 3))
    pygame.draw.rect(src, (20, 20, 20), (5, 5, 2, 2))
    pygame.draw.rect(src, (20, 20, 20), (10, 5, 2, 2))

    # Mouth — opens on chomp, faces movement
    if chomping:
        pygame.draw.rect(src, (40, 20, 10), (5, 8, 6, 4))
        pygame.draw.rect(src, ORANGE, (6, 9, 4, 2))
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

    if facing_x < 0:
        src = pygame.transform.flip(src, True, False)

    sprite = _scale(src, 56)
    _CACHE[key] = sprite
    return sprite


def troggle_surface(kind: str, frame: int, facing_x: int) -> pygame.Surface:
    key = ("troggle", kind, frame, facing_x)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    src = pygame.Surface((16, 16), pygame.SRCALPHA)
    body = MAGENTA if kind == "chase" else PURPLE
    dark = (96, 24, 64) if kind == "chase" else (80, 32, 110)
    pygame.draw.rect(src, dark, (3, 3, 10, 10))
    pygame.draw.rect(src, body, (4, 4, 8, 8))
    # Horns / antennae
    pygame.draw.rect(src, dark, (3, 1, 2, 3))
    pygame.draw.rect(src, dark, (11, 1, 2, 3))
    pygame.draw.rect(src, body, (3, 1, 2, 2))
    pygame.draw.rect(src, body, (11, 1, 2, 2))
    # Eyes
    pygame.draw.rect(src, WHITE, (5, 5, 2, 2))
    pygame.draw.rect(src, WHITE, (9, 5, 2, 2))
    pygame.draw.rect(src, RED if kind == "chase" else (20, 20, 40), (5, 6, 2, 1))
    pygame.draw.rect(src, RED if kind == "chase" else (20, 20, 40), (9, 6, 2, 1))
    # Snaggle mouth
    pygame.draw.rect(src, (40, 10, 20), (6, 9, 4, 2))
    if frame % 2:
        pygame.draw.rect(src, CREAM, (6, 9, 1, 2))
        pygame.draw.rect(src, CREAM, (9, 9, 1, 2))
    # Feet
    lift = 1 if frame % 2 == 0 else 0
    pygame.draw.rect(src, dark, (4, 13 - lift, 3, 3))
    pygame.draw.rect(src, dark, (9, 13 - (1 - lift), 3, 3))

    if facing_x < 0:
        src = pygame.transform.flip(src, True, False)

    sprite = _scale(src, 56)
    _CACHE[key] = sprite
    return sprite


def cell_rect(row: int, col: int, grid_left: int, grid_top: int) -> pygame.Rect:
    return pygame.Rect(grid_left + col * CELL_W, grid_top + row * CELL_H, CELL_W, CELL_H)


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