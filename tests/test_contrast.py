"""Grid digit contrast and get-ready veil (grades 2–5, 16:9 fullscreen)."""

from __future__ import annotations

import os
import unittest

from omunchy.constants import (
    CELL_BG,
    CELL_BG_ALT,
    CELL_BORDER,
    CELL_DIGIT,
    CELL_EMPTY,
    CELL_EMPTY_BORDER,
    CELL_HL,
    CELL_W,
    CREAM,
    INTRO_DIM_ALPHA,
    WINDOW_H,
    WINDOW_W,
)


def _channel(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (v / 255.0 for v in rgb)
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    light, dark = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


class CellContrastTests(unittest.TestCase):
    def test_digits_are_near_white_not_muddy_cream(self) -> None:
        self.assertGreaterEqual(min(CELL_DIGIT), 240)
        self.assertGreaterEqual(sum(CELL_DIGIT), sum(CREAM))
        # Cooler / brighter than cream so it does not blend into green fills.
        self.assertGreater(CELL_DIGIT[2], CREAM[2])

    def test_number_cells_have_strong_luminance_contrast(self) -> None:
        for fill in (CELL_BG, CELL_BG_ALT):
            ratio = contrast_ratio(CELL_DIGIT, fill)
            self.assertGreaterEqual(ratio, 12.0, msg=(CELL_DIGIT, fill, ratio))
            self.assertLess(relative_luminance(fill), 0.03)

    def test_empty_and_highlight_still_read_clearly(self) -> None:
        self.assertLess(relative_luminance(CELL_EMPTY), relative_luminance(CELL_BG))
        self.assertLess(relative_luminance(CELL_EMPTY_BORDER), relative_luminance(CELL_BORDER))
        self.assertGreater(relative_luminance(CELL_HL), relative_luminance(CELL_BORDER))
        self.assertGreaterEqual(contrast_ratio(CELL_HL, CELL_BG), 7.0)


class IntroVeilTests(unittest.TestCase):
    def test_intro_dim_is_a_heavy_black_fade(self) -> None:
        self.assertGreaterEqual(INTRO_DIM_ALPHA, 210)
        self.assertLessEqual(INTRO_DIM_ALPHA, 240)


class IntroDrawTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        try:
            import pygame
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest("pygame is not installed") from exc
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        from omunchy.app import Game, INTRO_ST, PLAY_ST

        cls.Game = Game
        cls.INTRO_ST = INTRO_ST
        cls.PLAY_ST = PLAY_ST
        cls.pygame = pygame

    @classmethod
    def tearDownClass(cls) -> None:
        cls.pygame.display.quit()
        cls.pygame.quit()

    def test_get_ready_veil_darkens_the_board(self) -> None:
        from omunchy.constants import grid_geometry

        game = self.Game()
        game.start_run("multiples")
        self.assertEqual(game.screen.get_size(), (WINDOW_W, WINDOW_H))
        rows, cols = game.board.rows, game.board.cols
        left, top, _w, _h = grid_geometry(rows, cols)
        # Inset of the top-right cell — fill, not HUD / overlay copy.
        sample = (left + (cols - 1) * CELL_W + 10, top + 10)

        game.state = self.PLAY_ST
        game._draw()
        play = game.screen.get_at(sample)
        game.state = self.INTRO_ST
        game._draw()
        intro = game.screen.get_at(sample)
        self.assertLess(sum(intro[:3]), sum(play[:3]) * 0.45)
        self.assertLess(sum(intro[:3]), 40)


if __name__ == "__main__":
    unittest.main()
