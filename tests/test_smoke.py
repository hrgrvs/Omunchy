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
        from omunchy.app import Game

        cls.Game = Game
        cls.pygame = pygame

    def test_boot_and_draw_key_screens(self) -> None:
        from omunchy.app import (
            BESTIARY_ST,
            CELEBRATE_ST,
            CLEAR_ST,
            INTRO_ST,
            MODE_ST,
            OVER_ST,
            PAUSE_ST,
            PLAY_ST,
            TITLE_ST,
            WARDROBE_ST,
        )

        game = self.Game()
        self.assertEqual(game.screen.get_size(), (1280, 720))
        from omunchy.constants import TITLE

        self.assertEqual(TITLE, "Omunchy")
        game._draw()
        game.anim = 1.8
        game._draw()
        game._keydown(self.pygame.K_t)
        self.assertEqual(game.state, BESTIARY_ST)
        game._draw()
        game._keydown(self.pygame.K_ESCAPE)
        self.assertEqual(game.state, TITLE_ST)
        game._keydown(self.pygame.K_F11)
        self.assertIsNotNone(game.screen)
        game._keydown(self.pygame.K_ESCAPE)
        self.assertFalse(game.running)
        game.running = True
        self.assertTrue(game.audio.muted is False)
        # Mixer may be dummy, but shipped cues should still load.
        self.assertIn("correct", game.audio._sounds)
        self.assertIn("celebrate", game.audio._sounds)

        for mode in ("multiples", "factors", "primes", "equals", "pairings"):
            game.start_run(mode)
            self.assertEqual(game.state, INTRO_ST, msg=mode)
            self.assertIsNotNone(game.board)
            self.assertGreater(game.board.remaining_correct(), 0, msg=mode)
            self.assertEqual((game.board.rows, game.board.cols), (4, 5), msg=mode)
            self.assertTrue(game.board.in_bounds(game.player.row, game.player.col))
        # Pairings grab does not start an eat animation — use a munch mode for the rest.
        game.start_run("multiples")
        self.assertEqual(len(game.troggles), 1)
        self.assertEqual(game.troggles[0].kind, "wander")

        game.state = INTRO_ST
        game._keydown(self.pygame.K_ESCAPE)
        self.assertEqual(game.state, PAUSE_ST)
        game._keydown(self.pygame.K_ESCAPE)
        self.assertEqual(game.state, PLAY_ST)
        game._keydown(self.pygame.K_ESCAPE)
        self.assertEqual(game.state, PAUSE_ST)
        game.pause_index = 1
        game._keydown(self.pygame.K_RETURN)
        self.assertEqual(game.state, BESTIARY_ST)
        game._draw()
        game._keydown(self.pygame.K_ESCAPE)
        self.assertEqual(game.state, PAUSE_ST)
        game._keydown(self.pygame.K_ESCAPE)
        self.assertEqual(game.state, PLAY_ST)
        game._munch()
        self.assertIsNotNone(game.eat_fx)
        game._draw()
        game._update(1.0)
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
        self.assertEqual(game.state, WARDROBE_ST)
        self.assertGreaterEqual(len(game.wear_choices), 3)
        game._draw()
        game._apply_wear_choice()
        self.assertEqual(game.state, INTRO_ST)
        self.assertIsNotNone(game.board)
        self.assertEqual((game.board.rows, game.board.cols), (5, 6))
        self.assertEqual(len(game.outfit.slots), 1)

        game.level = 3
        game.state = CLEAR_ST
        game._advance_from_clear()
        self.assertEqual(game.state, CELEBRATE_ST)
        self.assertEqual(game.level, 4)
        game._begin_level()
        self.assertEqual(game.state, INTRO_ST)
        self.assertEqual((game.board.rows, game.board.cols), (5, 6))
        game.level = 10
        game._begin_level()
        self.assertEqual((game.board.rows, game.board.cols), (6, 8))
        kinds = {t.kind for t in game.troggles}
        self.assertGreaterEqual(len(kinds), 4)
        game.state = OVER_ST
        game._draw()
        game.audio.shutdown()
        self.pygame.quit()


if __name__ == "__main__":
    unittest.main()