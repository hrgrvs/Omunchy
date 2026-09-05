"""Arcade title-screen ASCII for Omunchy (16:9 laptop layout)."""

from __future__ import annotations

# Compact 5-line banner — wide enough to feel arcade, short enough for 1280×720.
TITLE_BANNER = (
    " ██████   ███    ███  ██    ██  ███    ██   ██████  ██   ██  ██    ██",
    "██    ██  ████  ████  ██    ██  ████   ██  ██       ██   ██   ██  ██ ",
    "██    ██  ██ ████ ██  ██    ██  ██ ██  ██  ██       ███████    ████  ",
    "██    ██  ██  ██  ██  ██    ██  ██  ██ ██  ██       ██   ██     ██   ",
    " ██████   ██      ██   ██████   ██   ████   ██████  ██   ██     ██   ",
)

TITLE_DOODLE = (
    "   .--.                    /\\_/\\   ",
    "  ( o o)    munch    vs   ( o.o )  ",
    "   \\__V/                   > ^ <   ",
    "   you                    Troggle  ",
)

TAGLINE = "A math arcade for grades 2–5"
BLURB_A = "Munch every number that matches the rule."
BLURB_B = "Wrong munches and Troggles cost a life."
START_HINT = "Press ENTER or SPACE"
CONTROLS_HINT = "Esc / Q quit    F11 window    M mute"
LICENSE_LINE = "MIT License  ·  Copyright Damon Hargraves"
