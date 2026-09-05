"""Animated blocky pixel logo for the Omunchy title screen (no ASCII doodles)."""

from __future__ import annotations

from dataclasses import dataclass
import math

from omunchy.constants import (
    CYAN,
    GOLD,
    GREEN,
    ORANGE,
    PINK,
    WHITE,
    WINDOW_W,
    YELLOW,
)

TITLE_WORD = "OMUNCHY"
TAGLINE = "A math arcade for grades 2–5"
BLURB_A = "Munch every number that matches the rule."
BLURB_B = "Wrong munches and Troggles cost a life."
START_HINT = "Press ENTER or SPACE"
CONTROLS_HINT = "←→ menu    Enter play    T Troggles    Esc / Q quit    F11    M mute"
LICENSE_LINE = "MIT License  ·  Copyright Damon Hargraves"

# 7×7 block glyphs — chunky arcade letters that stay readable on 16:9.
_GLYPHS: dict[str, tuple[str, ...]] = {
    "O": (
        ".XXXXX.",
        "XX...XX",
        "XX...XX",
        "XX...XX",
        "XX...XX",
        "XX...XX",
        ".XXXXX.",
    ),
    "M": (
        "XX...XX",
        "XXX.XXX",
        "XXXXXXX",
        "XX.X.XX",
        "XX...XX",
        "XX...XX",
        "XX...XX",
    ),
    "U": (
        "XX...XX",
        "XX...XX",
        "XX...XX",
        "XX...XX",
        "XX...XX",
        "XX...XX",
        ".XXXXX.",
    ),
    "N": (
        "XX...XX",
        "XXX..XX",
        "XXXX.XX",
        "XX.XXXX",
        "XX..XXX",
        "XX...XX",
        "XX...XX",
    ),
    "C": (
        ".XXXXX.",
        "XX...XX",
        "XX.....",
        "XX.....",
        "XX.....",
        "XX...XX",
        ".XXXXX.",
    ),
    "H": (
        "XX...XX",
        "XX...XX",
        "XX...XX",
        "XXXXXXX",
        "XX...XX",
        "XX...XX",
        "XX...XX",
    ),
    "Y": (
        "XX...XX",
        "XX...XX",
        ".XX.XX.",
        "..XXX..",
        "...X...",
        "...X...",
        "...X...",
    ),
}

GLYPH_W = 7
GLYPH_H = 7
PIXEL = 16
LETTER_GAP = 12
POP_STAGGER = 0.11
WAVE_PX = 14.0

_CYCLE = (GOLD, YELLOW, ORANGE, PINK, CYAN, GREEN, WHITE)


@dataclass(frozen=True)
class LetterPose:
    ch: str
    x: int
    y: int
    scale: float
    color: tuple[int, int, int]
    glow: tuple[int, int, int]
    visible: bool


def glyph(ch: str) -> tuple[str, ...]:
    return _GLYPHS[ch]


def logo_width() -> int:
    n = len(TITLE_WORD)
    return n * GLYPH_W * PIXEL + (n - 1) * LETTER_GAP


def logo_height() -> int:
    return GLYPH_H * PIXEL


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def letter_color(index: int, now: float) -> tuple[int, int, int]:
    """Kid-friendly gold/rainbow cycle, phase-shifted per letter."""
    phase = now * 0.55 + index * 0.37
    pos = phase % len(_CYCLE)
    i = int(pos) % len(_CYCLE)
    nxt = (i + 1) % len(_CYCLE)
    return _mix(_CYCLE[i], _CYCLE[nxt], pos - int(pos))


def letter_poses(now: float, center_x: int = WINDOW_W // 2, top_y: int = 72) -> tuple[LetterPose, ...]:
    """Pop-in, wave, pulse, and color-cycle each letter of OMUNCHY."""
    total_w = logo_width()
    origin_x = center_x - total_w // 2
    pulse = 1.0 + 0.06 * math.sin(now * 2.4)
    poses: list[LetterPose] = []
    for i, ch in enumerate(TITLE_WORD):
        appear = i * POP_STAGGER
        age = now - appear
        visible = age >= 0
        if age < 0:
            scale = 0.0
        elif age < 0.22:
            # Overshoot pop.
            t = age / 0.22
            scale = (1.18 if t < 0.65 else 1.0 + 0.18 * (1.0 - t) / 0.35) * pulse
        else:
            scale = pulse
        wave = math.sin(now * 2.8 + i * 0.7) * WAVE_PX
        x = origin_x + i * (GLYPH_W * PIXEL + LETTER_GAP)
        y = int(top_y + wave)
        color = letter_color(i, now)
        glow = _mix(color, (20, 40, 24), 0.45)
        poses.append(LetterPose(ch, x, y, scale, color, glow, visible))
    return tuple(poses)


def draw_title_word(surface, now: float, center_x: int = WINDOW_W // 2, top_y: int = 72) -> int:
    """Blit the animated pixel logo. Returns the y just below the word."""
    import pygame

    poses = letter_poses(now, center_x, top_y)
    cell = PIXEL
    for pose in poses:
        if not pose.visible or pose.scale <= 0.05:
            continue
        rows = glyph(pose.ch)
        letter_w = GLYPH_W * cell
        letter_h = GLYPH_H * cell
        scale = pose.scale
        draw_w = max(1, int(letter_w * scale))
        draw_h = max(1, int(letter_h * scale))
        ox = pose.x - (draw_w - letter_w) // 2
        oy = pose.y - (draw_h - letter_h) // 2
        px = draw_w / GLYPH_W
        py = draw_h / GLYPH_H
        # Soft glow block behind each lit pixel.
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit != "X":
                    continue
                gx = int(ox + c * px)
                gy = int(oy + r * py)
                rw = max(2, int(px) + 1)
                rh = max(2, int(py) + 1)
                pygame.draw.rect(surface, pose.glow, (gx - 1, gy + 2, rw + 2, rh + 2), border_radius=2)
                pygame.draw.rect(surface, (0, 0, 0), (gx + 1, gy + 1, rw, rh), border_radius=2)
                pygame.draw.rect(surface, pose.color, (gx, gy, rw, rh), border_radius=2)
    # Sparkle on a couple of blocks so it feels alive without clutter.
    sparkle_t = (now * 3.2) % 1.0
    if sparkle_t < 0.35:
        spark_i = int(now * 1.7) % len(TITLE_WORD)
        pose = poses[spark_i]
        if pose.visible:
            pygame.draw.rect(
                surface,
                WHITE,
                (pose.x + PIXEL * 3, pose.y + PIXEL, 5, 5),
                border_radius=1,
            )
    return top_y + logo_height() + int(WAVE_PX) + 8
