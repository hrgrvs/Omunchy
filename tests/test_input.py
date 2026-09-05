"""Tap-only movement: one KEYDOWN steps one cell; hold / repeat does not."""

from __future__ import annotations

import os
import unittest


class TapMoveTests(unittest.TestCase):
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

    def _play(self):
        self.pygame.event.clear()
        game = self.Game()
        game.start_run("multiples")
        game.state = self.PLAY_ST
        game.player.row, game.player.col = 1, 1
        game.player.chomp_timer = 0
        game.held.clear()
        return game

    def _key(self, game, key: int, down: bool = True) -> None:
        kind = self.pygame.KEYDOWN if down else self.pygame.KEYUP
        self.pygame.event.post(self.pygame.event.Event(kind, key=key))
        game._events()

    def test_held_move_is_gone(self) -> None:
        game = self._play()
        self.assertFalse(hasattr(game, "_held_move"))
        self.assertFalse(hasattr(game, "move_cool"))

    def test_one_keydown_moves_one_cell_for_each_scheme(self) -> None:
        schemes = (
            (self.pygame.K_RIGHT, self.pygame.K_LEFT, self.pygame.K_DOWN, self.pygame.K_UP),
            (self.pygame.K_d, self.pygame.K_a, self.pygame.K_s, self.pygame.K_w),
            (self.pygame.K_l, self.pygame.K_j, self.pygame.K_k, self.pygame.K_i),
        )
        for right, left, down, up in schemes:
            with self.subTest(right=right):
                game = self._play()
                start = game.player.pos
                game._try_move_key(right)
                self.assertEqual(game.player.pos, (start[0], start[1] + 1))
                game._try_move_key(down)
                self.assertEqual(game.player.pos, (start[0] + 1, start[1] + 1))
                game._try_move_key(left)
                self.assertEqual(game.player.pos, (start[0] + 1, start[1]))
                game._try_move_key(up)
                self.assertEqual(game.player.pos, start)

    def test_holding_a_direction_does_not_keep_moving(self) -> None:
        game = self._play()
        start = game.player.pos
        self._key(game, self.pygame.K_RIGHT)
        after_tap = game.player.pos
        self.assertEqual(after_tap, (start[0], start[1] + 1))
        self.assertIn(self.pygame.K_RIGHT, game.held)
        for _ in range(24):
            game._update(0.05)
        self.assertEqual(game.player.pos, after_tap)
        # OS / pygame key-repeat while still held must not step again.
        self._key(game, self.pygame.K_RIGHT)
        self.assertEqual(game.player.pos, after_tap)
        self._key(game, self.pygame.K_RIGHT, down=False)
        self._key(game, self.pygame.K_RIGHT)
        self.assertEqual(game.player.pos, (start[0], start[1] + 2))

    def test_wasd_and_ijkl_holds_also_do_not_repeat(self) -> None:
        for key in (self.pygame.K_d, self.pygame.K_l):
            with self.subTest(key=key):
                game = self._play()
                start = game.player.pos
                self._key(game, key)
                stepped = game.player.pos
                self.assertEqual(stepped, (start[0], start[1] + 1))
                for _ in range(12):
                    game._update(0.08)
                self.assertEqual(game.player.pos, stepped)


if __name__ == "__main__":
    unittest.main()
