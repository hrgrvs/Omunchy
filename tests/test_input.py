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
        from omunchy.app import (
            BESTIARY_ST,
            CELEBRATE_ST,
            CLEAR_ST,
            DIRECTION_KEYS,
            INTRO_ST,
            MODE_ST,
            OVER_ST,
            PAUSE_ST,
            PLAY_ST,
            TITLE_ST,
            WARDROBE_ST,
            Game,
        )

        cls.Game = Game
        cls.PLAY_ST = PLAY_ST
        cls.TITLE_ST = TITLE_ST
        cls.MODE_ST = MODE_ST
        cls.INTRO_ST = INTRO_ST
        cls.PAUSE_ST = PAUSE_ST
        cls.CLEAR_ST = CLEAR_ST
        cls.CELEBRATE_ST = CELEBRATE_ST
        cls.WARDROBE_ST = WARDROBE_ST
        cls.BESTIARY_ST = BESTIARY_ST
        cls.OVER_ST = OVER_ST
        cls.DIRECTION_KEYS = DIRECTION_KEYS
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
        game.running = True
        return game

    def _key(self, game, key: int, down: bool = True, repeat: int = 0) -> None:
        kind = self.pygame.KEYDOWN if down else self.pygame.KEYUP
        self.pygame.event.post(self.pygame.event.Event(kind, key=key, repeat=repeat))
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

    def test_consecutive_direction_changes_each_advance_one_step(self) -> None:
        """Changing direction must never require a second tap."""
        game = self._play()
        start = game.player.pos
        path = (
            (self.pygame.K_RIGHT, (start[0], start[1] + 1)),
            (self.pygame.K_DOWN, (start[0] + 1, start[1] + 1)),
            (self.pygame.K_LEFT, (start[0] + 1, start[1])),
            (self.pygame.K_UP, start),
            (self.pygame.K_d, (start[0], start[1] + 1)),
            (self.pygame.K_s, (start[0] + 1, start[1] + 1)),
            (self.pygame.K_l, (start[0] + 1, start[1] + 2)),
        )
        for key, expected in path:
            self._key(game, key)
            self.assertEqual(game.player.pos, expected, msg=key)
        # Previous direction keys may still be in held (no KEYUP). Going back
        # to an earlier direction must still step on this KEYDOWN.
        self.assertIn(self.pygame.K_RIGHT, game.held)
        self._key(game, self.pygame.K_RIGHT)
        self.assertEqual(game.player.pos, (start[0] + 1, start[1] + 3))

    def test_stale_held_direction_still_moves_on_keydown(self) -> None:
        """Missed KEYUP (macOS) must not force a second press."""
        game = self._play()
        game.held.add(self.pygame.K_RIGHT)
        start = game.player.pos
        self._key(game, self.pygame.K_RIGHT)
        self.assertEqual(game.player.pos, (start[0], start[1] + 1))

    def test_chomp_does_not_swallow_the_next_direction_tap(self) -> None:
        game = self._play()
        game.player.chomp_timer = 0.4
        start = game.player.pos
        self._key(game, self.pygame.K_RIGHT)
        self.assertEqual(game.player.pos, (start[0], start[1] + 1))

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
        self._key(game, self.pygame.K_RIGHT, repeat=1)
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
                self._key(game, key, repeat=1)
                self.assertEqual(game.player.pos, stepped)


    def test_escape_leaves_every_interactive_state(self) -> None:
        game = self._play()
        cases = (
            (self.TITLE_ST, lambda g: not g.running),
            (self.MODE_ST, lambda g: g.state == self.TITLE_ST),
            (self.INTRO_ST, lambda g: g.state == self.PAUSE_ST),
            (self.PLAY_ST, lambda g: g.state == self.PAUSE_ST),
            (self.PAUSE_ST, lambda g: g.state == self.PLAY_ST),
            (self.BESTIARY_ST, lambda g: g.state == self.TITLE_ST),
            (self.CLEAR_ST, lambda g: g.state != self.CLEAR_ST),
            (self.CELEBRATE_ST, lambda g: g.state == self.WARDROBE_ST),
            (self.WARDROBE_ST, lambda g: g.state == self.INTRO_ST),
            (self.OVER_ST, lambda g: g.state == self.TITLE_ST),
        )
        for state, ok in cases:
            with self.subTest(state=state):
                game.running = True
                game.held.clear()
                game.state = state
                if state == self.BESTIARY_ST:
                    game.bestiary_back = self.TITLE_ST
                if state == self.CELEBRATE_ST:
                    game.level = 4
                    game.wear_choices = []
                if state == self.WARDROBE_ST:
                    from omunchy.wearables import BY_ID

                    game.wear_choices = [BY_ID["cape-bat"]]
                    game.wear_index = 0
                if state == self.CLEAR_ST:
                    game.level = 1
                self._key(game, self.pygame.K_ESCAPE)
                self.assertTrue(ok(game), msg=f"state={state} now={game.state}")

    def test_escape_clears_stuck_held_keys(self) -> None:
        game = self._play()
        game.held.update(self.DIRECTION_KEYS)
        game.held.add(self.pygame.K_SPACE)
        self._key(game, self.pygame.K_ESCAPE)
        self.assertEqual(game.state, self.PAUSE_ST)
        self.assertNotIn(self.pygame.K_SPACE, game.held)
        self.assertFalse(self.DIRECTION_KEYS & game.held)

    def test_get_ready_and_wardrobe_stay_keyboard_dismissible(self) -> None:
        game = self._play()
        game.state = self.INTRO_ST
        game.held.add(self.pygame.K_SPACE)
        self._key(game, self.pygame.K_SPACE)
        self.assertEqual(game.state, self.PLAY_ST)

        game.state = self.CELEBRATE_ST
        game.held.add(self.pygame.K_RETURN)
        self._key(game, self.pygame.K_RETURN)
        self.assertEqual(game.state, self.WARDROBE_ST)
        self.assertGreaterEqual(len(game.wear_choices), 1)

        game.state = self.WARDROBE_ST
        self._key(game, self.pygame.K_ESCAPE)
        self.assertEqual(game.state, self.INTRO_ST)

    def test_eat_animation_does_not_block_escape(self) -> None:
        game = self._play()
        game._munch()
        self.assertIsNotNone(game.eat_fx)
        self._key(game, self.pygame.K_ESCAPE)
        self.assertEqual(game.state, self.PAUSE_ST)

    def test_focus_lost_clears_held(self) -> None:
        game = self._play()
        game.held.add(self.pygame.K_RIGHT)
        focus = getattr(self.pygame, "WINDOWFOCUSLOST", None) or getattr(
            self.pygame, "ACTIVEEVENT", None
        )
        if focus is None:
            self.skipTest("pygame has no focus event")
        self.pygame.event.post(self.pygame.event.Event(focus))
        game._events()
        self.assertEqual(game.held, set())


if __name__ == "__main__":
    unittest.main()
