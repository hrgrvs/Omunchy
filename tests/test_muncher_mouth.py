"""Open-mouth peek: the cell number stays readable under the muncher."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from omunchy.constants import CELL_DIGIT, GOLD, WINDOW_H, WINDOW_W
from omunchy.sprites import PEEK_MOUTH, muncher_surface
from omunchy.wearables import BY_ID, Outfit


def _near(rgb: tuple[int, int, int], target: tuple[int, int, int], slack: int = 12) -> bool:
    return all(abs(a - b) <= slack for a, b in zip(rgb, target))


def _scaled_mouth_center() -> tuple[int, int]:
    """Pixel in the 56×56 sprite that sits in the peek hole."""
    x, y, w, h = PEEK_MOUTH
    # 16×16 → 56×56 is a 3.5× nearest-neighbor scale.
    sx = int((x + w / 2) * 3.5)
    sy = int((y + h / 2) * 3.5)
    return sx, sy


class MuncherMouthSpriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        try:
            import pygame
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest("pygame is not installed") from exc
        pygame.display.init()
        cls.pygame = pygame

    @classmethod
    def tearDownClass(cls) -> None:
        cls.pygame.display.quit()

    def test_peeking_mouth_is_see_through(self) -> None:
        sprite = muncher_surface(0, 1, False, False, peeking=True)
        mx, my = _scaled_mouth_center()
        self.assertEqual(sprite.get_at((mx, my))[3], 0)
        # A ring of the hole should be empty, not a single lucky pixel.
        clear = 0
        for dx in range(-4, 5):
            for dy in range(-3, 4):
                if sprite.get_at((mx + dx, my + dy))[3] == 0:
                    clear += 1
        self.assertGreaterEqual(clear, 20)

    def test_closed_mouth_covers_the_bite(self) -> None:
        sprite = muncher_surface(0, 1, False, False, peeking=False)
        mx, my = _scaled_mouth_center()
        pixel = sprite.get_at((mx, my))
        self.assertGreater(pixel[3], 200)
        # Idle body/mouth is gold or the dark closed lip — never a hole.
        self.assertTrue(
            _near(pixel[:3], GOLD, 40) or pixel[2] < 40,
            msg=pixel,
        )

    def test_chomp_mouth_stays_opaque_for_the_eat_animation(self) -> None:
        sprite = muncher_surface(0, 1, True, False, peeking=True)
        mx, my = _scaled_mouth_center()
        pixel = sprite.get_at((mx, my))
        self.assertGreater(pixel[3], 200)
        # Filled bite: dark jaw or orange tongue, not the gold body.
        self.assertLess(pixel[1], 180, msg=pixel)

    def test_wearables_still_draw_around_an_open_mouth(self) -> None:
        outfit = Outfit()
        outfit.wear(BY_ID["hat-red-cap"])
        outfit.wear(BY_ID["cape-ruby"])
        outfit.wear(BY_ID["glasses-round"])
        outfit.wear(BY_ID["mustache-bushy"])
        outfit.wear(BY_ID["cane-wood"])
        outfit.wear(BY_ID["shoes-sneakers"])
        sprite = muncher_surface(0, 1, False, False, outfit, peeking=True)
        mx, my = _scaled_mouth_center()
        self.assertEqual(sprite.get_at((mx, my))[3], 0)
        pixels = [
            sprite.get_at((x, y))[:3]
            for x in range(sprite.get_width())
            for y in range(sprite.get_height())
            if sprite.get_at((x, y))[3] > 0
        ]
        # Red cap + ruby cape + red sneakers share this primary.
        self.assertIn((220, 56, 56), pixels)
        # Wood cane
        self.assertIn((140, 84, 40), pixels)
        # Glasses frames
        self.assertIn((28, 28, 32), pixels)


class MuncherMouthPlayfieldTests(unittest.TestCase):
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
        from omunchy.app import Game, PLAY_ST

        cls.Game = Game
        cls.PLAY_ST = PLAY_ST
        cls.pygame = pygame

    @classmethod
    def tearDownClass(cls) -> None:
        cls.pygame.display.quit()
        cls.pygame.quit()

    def _play_game(self, mode: str = "multiples"):
        from omunchy.sprites import cell_rect

        game = self.Game()
        game.start_run(mode)
        game.state = self.PLAY_ST
        game.player.hop_timer = 0
        game.player.chomp_timer = 0
        game.eat_fx = None
        game.anim = 0.0
        game.flash_wrong = 0.0
        return game, cell_rect

    def test_digit_is_readable_while_standing_on_an_unmunched_cell(self) -> None:
        from omunchy.constants import grid_geometry

        game, cell_rect = self._play_game("multiples")
        self.assertIsNotNone(game.board)
        cell = game.board.cell(game.player.row, game.player.col)
        self.assertFalse(cell.munched)
        self.assertTrue(cell.label)

        game._draw()
        self.assertEqual(game.screen.get_size(), (WINDOW_W, WINDOW_H))
        left, top, _w, _h = grid_geometry(game.board.rows, game.board.cols)
        rect = cell_rect(game.player.row, game.player.col, left, top)
        found = 0
        goldish = 0
        for x in range(rect.centerx - 16, rect.centerx + 17):
            for y in range(rect.centery - 12, rect.centery + 13):
                rgb = game.screen.get_at((x, y))[:3]
                if rgb == CELL_DIGIT:
                    found += 1
                if _near(rgb, GOLD, 18):
                    goldish += 1
        self.assertGreater(found, 8, msg=(cell.label, found, goldish))
        # The number, not the gold body, should own the cell center.
        self.assertGreater(found, goldish, msg=(cell.label, found, goldish))

    def test_equals_expression_stays_readable_under_the_muncher(self) -> None:
        from omunchy.constants import grid_geometry
        from omunchy.sprites import cell_rect

        game, _ = self._play_game("equals")
        # Prefer a wide label if the spawn cell is a bare number.
        rows, cols = game.board.rows, game.board.cols
        wide = None
        for r in range(rows):
            for c in range(cols):
                cell = game.board.cell(r, c)
                if not cell.munched and len(cell.label) >= 3:
                    wide = cell
                    break
            if wide is not None:
                break
        if wide is None:
            self.skipTest("equals board had no expression labels")
        game.player.row, game.player.col = wide.row, wide.col
        game._draw()
        left, top, _w, _h = grid_geometry(rows, cols)
        rect = cell_rect(wide.row, wide.col, left, top)
        found = 0
        for x in range(rect.left + 8, rect.right - 8):
            for y in range(rect.centery - 10, rect.centery + 11):
                if game.screen.get_at((x, y))[:3] == CELL_DIGIT:
                    found += 1
        self.assertGreater(found, 20, msg=(wide.label, found))

    def test_empty_cell_uses_a_closed_mouth(self) -> None:
        game, cell_rect = self._play_game("multiples")
        cell = game.board.cell(game.player.row, game.player.col)
        cell.munched = True
        game._draw()
        from omunchy.constants import grid_geometry

        left, top, _w, _h = grid_geometry(game.board.rows, game.board.cols)
        rect = cell_rect(game.player.row, game.player.col, left, top)
        # Sprite is shifted down 8px from the cell center.
        mx = rect.centerx
        my = rect.centery + 8
        # Sample the mouth region of the 56×56 sprite (center-ish, a bit low).
        mouth = game.screen.get_at((mx, my + 6))
        self.assertGreater(mouth[3] if len(mouth) > 3 else 255, 200)
        # No leftover high-contrast digit on a munched plate.
        digit_hits = 0
        for x in range(rect.centerx - 10, rect.centerx + 11):
            for y in range(rect.centery - 8, rect.centery + 9):
                if game.screen.get_at((x, y))[:3] == CELL_DIGIT:
                    digit_hits += 1
        self.assertEqual(digit_hits, 0)


if __name__ == "__main__":
    unittest.main()
