"""Update splash: Munchy run loop, status bar, and dummy-driver pygame."""

from __future__ import annotations

from io import StringIO
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from test_update import FakeGit  # noqa: E402

from omunchy.constants import GREEN, ORANGE, WINDOW_H, WINDOW_W  # noqa: E402
from omunchy.update import (  # noqa: E402
    REEXEC_ENV,
    SKIP_ENV,
    GitResult,
    maybe_update_and_reexec,
    reset_for_tests,
)
from omunchy.update_splash import (  # noqa: E402
    SPLASH_MUNCHY_SIZE,
    draw_update_splash,
    munchy_chomping,
    munchy_frame,
    munchy_hop,
    munchy_run_x,
    run_update_splash,
    should_show_splash,
    status_bar_color,
    status_bar_fill,
    status_bar_label,
)


class SplashMathTests(unittest.TestCase):
    def test_munchy_runs_right_then_wraps(self) -> None:
        xs = [munchy_run_x(t * 0.4, WINDOW_W, SPLASH_MUNCHY_SIZE) for t in range(20)]
        self.assertTrue(any(xs[i] > xs[i - 1] for i in range(1, len(xs))))
        self.assertTrue(any(xs[i] + SPLASH_MUNCHY_SIZE < xs[i - 1] for i in range(1, len(xs))))
        self.assertTrue(all(-SPLASH_MUNCHY_SIZE - 80 < x < WINDOW_W + 80 for x in xs))
        self.assertLess(munchy_run_x(0.0, WINDOW_W, SPLASH_MUNCHY_SIZE), 0)

    def test_hop_and_run_cycle(self) -> None:
        self.assertEqual(munchy_hop(0.0), 0)
        self.assertGreater(munchy_hop(0.12), 0)
        self.assertEqual(munchy_hop(0.0), munchy_hop(1.0 / 2.4))
        self.assertNotEqual(munchy_frame(0.0), munchy_frame(0.2))
        self.assertTrue(any(munchy_chomping(t * 0.1) for t in range(20)))
        self.assertTrue(any(not munchy_chomping(t * 0.1) for t in range(20)))

    def test_status_bar_phases(self) -> None:
        self.assertIn("Checking", status_bar_label("checking"))
        self.assertIn("Updating", status_bar_label("updating"))
        self.assertIn("Ready", status_bar_label("done"))
        self.assertIn("Couldn't update", status_bar_label("failed"))
        self.assertIn("Offline", status_bar_label("offline"))
        self.assertLess(status_bar_fill("checking", 0.0), status_bar_fill("updating", 0.0))
        self.assertLess(status_bar_fill("updating", 0.0), status_bar_fill("done", 0.0))
        self.assertEqual(status_bar_fill("done", 0.0), 1.0)
        self.assertEqual(status_bar_color("done"), GREEN)
        self.assertEqual(status_bar_color("failed"), ORANGE)
        checking_a = status_bar_fill("checking", 0.0)
        checking_b = status_bar_fill("checking", 0.4)
        self.assertNotEqual(checking_a, checking_b)

    def test_should_show_splash_respects_skip_and_reexec(self) -> None:
        saved = {key: os.environ.get(key) for key in (SKIP_ENV, REEXEC_ENV)}
        try:
            os.environ.pop(SKIP_ENV, None)
            os.environ.pop(REEXEC_ENV, None)
            self.assertTrue(should_show_splash(Path(".")))
            os.environ[SKIP_ENV] = "1"
            self.assertFalse(should_show_splash(Path(".")))
            os.environ.pop(SKIP_ENV, None)
            os.environ[REEXEC_ENV] = "1"
            self.assertFalse(should_show_splash(Path(".")))
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


class SplashPygameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import pygame
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest("pygame is not installed") from exc
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        pygame.display.init()
        pygame.font.init()
        cls.pygame = pygame

    @classmethod
    def tearDownClass(cls) -> None:
        cls.pygame.display.quit()
        cls.pygame.font.quit()

    def setUp(self) -> None:
        reset_for_tests()
        self._env_save = {key: os.environ.get(key) for key in (SKIP_ENV, REEXEC_ENV)}
        os.environ.pop(SKIP_ENV, None)
        os.environ.pop(REEXEC_ENV, None)
        self.root = Path(tempfile.mkdtemp())
        if not self.pygame.display.get_init():
            self.pygame.display.init()
        if not self.pygame.font.get_init():
            self.pygame.font.init()

    def tearDown(self) -> None:
        reset_for_tests()
        for key, value in self._env_save.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _surface(self):
        return self.pygame.Surface((WINDOW_W, WINDOW_H))

    def test_draw_each_phase_fills_16_by_9(self) -> None:
        for phase in ("checking", "updating", "done", "failed", "offline"):
            surf = self._surface()
            draw_update_splash(surf, 0.8, phase)
            self.assertEqual(surf.get_size(), (WINDOW_W, WINDOW_H))
            # Status bar lives in the lower third; it must not be empty.
            sample = surf.get_at((WINDOW_W // 2, 580))
            self.assertNotEqual(sample[:3], (0, 0, 0))

    def test_munchy_moves_across_drawn_frames(self) -> None:
        first = self._surface()
        second = self._surface()
        draw_update_splash(first, 0.15, "checking")
        draw_update_splash(second, 1.35, "checking")
        self.assertNotEqual(first.get_buffer().raw, second.get_buffer().raw)

    def test_run_splash_up_to_date_dummy_driver(self) -> None:
        with patch("sys.stdout", StringIO()):
            outcome = run_update_splash(
                root=self.root,
                git_runner=FakeGit(),
                min_seconds=0.0,
                fullscreen=False,
            )
        self.assertEqual(outcome.status, "up_to_date")
        self.assertFalse(outcome.should_reexec)
        self.assertFalse(self.pygame.display.get_init())

    def test_run_splash_offline_and_updated(self) -> None:
        with patch("sys.stdout", StringIO()):
            failed = run_update_splash(
                root=self.root,
                git_runner=FakeGit(fetch_result=GitResult(1, stderr="offline")),
                min_seconds=0.0,
                fullscreen=False,
            )
            updated = run_update_splash(
                root=self.root,
                git_runner=FakeGit(head="old", remote="new"),
                min_seconds=0.0,
                fullscreen=False,
            )
        self.assertEqual(failed.status, "failed")
        self.assertEqual(updated.status, "updated")
        self.assertTrue(updated.should_reexec)

    def test_maybe_update_splash_then_game_can_init(self) -> None:
        with patch("sys.stdout", StringIO()):
            outcome = maybe_update_and_reexec(
                root=self.root,
                git_runner=FakeGit(),
                splash=True,
                min_splash=0.0,
                _reexec=lambda: None,
            )
        self.assertEqual(outcome.status, "up_to_date")
        self.pygame.mixer.pre_init(22050, -16, 1, 512)
        self.pygame.init()
        from omunchy.app import Game

        game = Game()
        self.assertEqual(game.screen.get_size(), (WINDOW_W, WINDOW_H))
        game._draw()
        game.audio.shutdown()
        self.pygame.display.quit()
        self.pygame.quit()
        # Restore display for later tests in this class.
        self.pygame.display.init()
        self.pygame.font.init()

    def test_display_init_failure_falls_back_to_console(self) -> None:
        with (
            patch("pygame.display.init", side_effect=RuntimeError("no video")),
            patch("sys.stdout", StringIO()),
        ):
            outcome = run_update_splash(
                root=self.root,
                git_runner=FakeGit(),
                min_seconds=0.0,
                fullscreen=False,
            )
        self.assertEqual(outcome.status, "up_to_date")


if __name__ == "__main__":
    unittest.main()
