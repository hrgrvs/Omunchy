"""Munchy fills the cell; Troggles are distinct sizes; chase eyes track."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from omunchy.constants import MUNCHY_SPRITE_SIZE, TROGGLE_SPRITE_SIZES
from omunchy.sprites import muncher_surface, troggle_surface


class SpriteScaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import pygame
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest("pygame is not installed") from exc
        pygame.display.init()
        cls.pygame = pygame

    @classmethod
    def tearDownClass(cls) -> None:
        cls.pygame.display.quit()

    def test_munchy_is_the_largest_and_fills_the_cell(self) -> None:
        sprite = muncher_surface(0, 1, False, False)
        self.assertEqual(sprite.get_width(), MUNCHY_SPRITE_SIZE)
        self.assertEqual(sprite.get_height(), MUNCHY_SPRITE_SIZE)
        self.assertGreaterEqual(MUNCHY_SPRITE_SIZE, 76)

    def test_troggle_sizes_are_distinct_and_smaller_than_munchy(self) -> None:
        sizes = {}
        for kind, expected in TROGGLE_SPRITE_SIZES.items():
            sprite = troggle_surface(kind, 0, 1)
            sizes[kind] = sprite.get_width()
            self.assertEqual(sprite.get_width(), expected, msg=kind)
            self.assertLess(expected, MUNCHY_SPRITE_SIZE, msg=kind)
        self.assertEqual(len(set(sizes.values())), len(sizes))
        self.assertLess(sizes["wander"], sizes["chase"])
        self.assertLess(sizes["chase"], sizes["fire"])
        self.assertLess(sizes["exploder"], sizes["hunter"])
        self.assertLess(sizes["wander"], sizes["exploder"])


class ChaseEyeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import pygame
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest("pygame is not installed") from exc
        pygame.display.init()
        cls.pygame = pygame

    @classmethod
    def tearDownClass(cls) -> None:
        cls.pygame.display.quit()

    def test_pupils_shift_when_look_target_changes(self) -> None:
        left = troggle_surface("chase", 0, 1, look_x=-1, look_y=0)
        right = troggle_surface("chase", 0, 1, look_x=1, look_y=0)
        up = troggle_surface("chase", 0, 1, look_x=0, look_y=-1)
        self.assertNotEqual(left.get_buffer().raw, right.get_buffer().raw)
        self.assertNotEqual(left.get_buffer().raw, up.get_buffer().raw)
        # Eyes are big: plenty of white sclera.
        white = 0
        for x in range(left.get_width()):
            for y in range(left.get_height()):
                rgb = left.get_at((x, y))[:3]
                if rgb[0] > 230 and rgb[1] > 230 and rgb[2] > 220:
                    white += 1
        self.assertGreater(white, 40)


if __name__ == "__main__":
    unittest.main()
