import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


class PygameSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import pygame
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest("pygame is not installed") from exc
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        from omunch.app import Game

        cls.Game = Game
        cls.pygame = pygame

    def test_boot_and_draw_key_screens(self) -> None:
        from omunch.app import (
            CELEBRATE_ST,
            CLEAR_ST,
            INTRO_ST,
            MODE_ST,
            OVER_ST,
            PLAY_ST,
        )

        game = self.Game()
        self.assertTrue(game.audio.muted is False)
        # Mixer may be dummy, but shipped cues should still load.
        self.assertIn("correct", game.audio._sounds)
        self.assertIn("celebrate", game.audio._sounds)

        game.start_run("multiples")
        self.assertEqual(game.state, INTRO_ST)
        self.assertIsNotNone(game.board)
        self.assertGreater(game.board.remaining_correct(), 0)

        game.state = PLAY_ST
        game._draw()
        game.state = MODE_ST
        game._draw()
        game.state = CLEAR_ST
        game._draw()
        game.level = 3
        game._start_celebrate()
        self.assertEqual(game.state, CELEBRATE_ST)
        self.assertGreater(len(game.confetti), 0)
        game._draw()
        game._finish_celebrate()
        self.assertEqual(game.level, 4)
        game.state = OVER_ST
        game._draw()
        game.audio.shutdown()
        self.pygame.quit()


if __name__ == "__main__":
    unittest.main()