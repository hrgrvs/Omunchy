"""Wander bounce, lingering fire, and spawn-warning cues on a live Game."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from omunchy.entities import FireField, IncomingTroggle, Troggle
from omunchy.constants import HERO_NAME


class PlayHazardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
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
        game = self.Game()
        game.start_run("multiples")
        game.state = self.PLAY_ST
        game.player.iframe_timer = 0
        game.freeze = 0
        game.player.chomp_timer = 0
        return game

    def test_hero_name_is_munchy(self) -> None:
        self.assertEqual(HERO_NAME, "Munchy")

    def test_level_start_queues_per_type_spawn_cues(self) -> None:
        game = self._play()
        kinds = [kind for _wait, kind in game._spawn_cues]
        self.assertIn("wander", kinds)
        game._tick_spawn_cues(1.0)
        self.assertEqual(game._spawn_cues, [])

    def test_wander_bumps_without_losing_a_life(self) -> None:
        game = self._play()
        game.player.row, game.player.col = 2, 2
        game.player.prev_row, game.player.prev_col = 2, 1
        wander = Troggle(row=2, col=2, kind="wander", heading=(1, 0), interval=8.0)
        wander.move_timer = 8.0
        game.troggles = [wander]
        lives = game.lives
        game._update(0.016)
        self.assertEqual(game.lives, lives)
        self.assertEqual(game.player.pos, (2, 1))

    def test_lingering_fire_costs_a_life_after_the_breath(self) -> None:
        game = self._play()
        game.player.row, game.player.col = 1, 2
        game.player.prev_row, game.player.prev_col = 1, 1
        game.troggles = [Troggle(row=3, col=3, kind="wander")]
        game.fires = FireField()
        game.fires.ignite(1, 2, game.board.rows, game.board.cols, duration=1.2)
        lives = game.lives
        game._update(0.016)
        self.assertEqual(game.lives, lives - 1)
        self.assertGreater(game.player.iframe_timer, 0)

    def test_incoming_troggle_materializes_after_the_warning(self) -> None:
        game = self._play()
        game.troggles = []
        game.incoming = [
            IncomingTroggle(
                kind="chase",
                row=0,
                col=0,
                heading=(1, 0),
                interval=1.2,
                warn=0.01,
            )
        ]
        game._tick_incoming(0.05)
        self.assertEqual(game.incoming, [])
        self.assertEqual(len(game.troggles), 1)
        self.assertEqual(game.troggles[0].kind, "chase")
        self.assertEqual(game.troggles[0].pos, (0, 0))


if __name__ == "__main__":
    unittest.main()
