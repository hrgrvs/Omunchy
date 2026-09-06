"""Startup self-update: stubs for up-to-date, re-exec, offline, and skip."""

from __future__ import annotations

from io import StringIO
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from omunchy.update import (
    DEFAULT_TIMEOUT,
    REEXEC_ENV,
    SKIP_ENV,
    GitResult,
    UpdateOutcome,
    check_for_updates,
    discover_repo_root,
    maybe_update_and_reexec,
    reexec_self,
    reset_for_tests,
    run_git,
    splash_phase_for,
)


class FakeGit:
    """Scripted git: healthy up-to-date clone on main unless overridden."""

    def __init__(
        self,
        *,
        inside: bool = True,
        origin: str | None = "https://github.com/hrgrvs/Omunchy.git",
        branch: str = "main",
        head: str = "aaa",
        remote: str | None = "aaa",
        fetch_result: GitResult | None = None,
        merge_result: GitResult | None = None,
        fetch_timeout: bool = False,
        diverged: bool = False,
        ahead: bool = False,
        git_missing: bool = False,
    ) -> None:
        self.inside = inside
        self.origin = origin
        self.branch = branch
        self.head = head
        self.remote = remote
        self.fetch_result = fetch_result or GitResult(0)
        self.merge_result = merge_result or GitResult(0)
        self.fetch_timeout = fetch_timeout
        self.diverged = diverged
        self.ahead = ahead
        self.git_missing = git_missing
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, args, cwd, timeout) -> GitResult:  # noqa: ANN001
        self.calls.append(tuple(args))
        if self.git_missing:
            return GitResult(127, missing=True)
        cmd = args[0]
        if cmd == "rev-parse":
            if "--is-inside-work-tree" in args:
                return GitResult(0, stdout="true\n") if self.inside else GitResult(128)
            if "--verify" in args:
                ref = args[-1]
                if ref == "origin/main" and self.remote is not None:
                    return GitResult(0)
                if ref == "origin/master" and self.branch == "master" and self.remote is not None:
                    return GitResult(0)
                return GitResult(1)
            if args[-1] == "HEAD":
                return GitResult(0, stdout=self.head + "\n")
            if args[-1] in ("origin/main", "origin/master") and self.remote is not None:
                return GitResult(0, stdout=self.remote + "\n")
            return GitResult(128)
        if cmd == "remote":
            return GitResult(0, stdout=self.origin + "\n") if self.origin else GitResult(2)
        if cmd == "symbolic-ref":
            return GitResult(0, stdout=self.branch + "\n") if self.branch else GitResult(128)
        if cmd == "fetch":
            if self.fetch_timeout:
                return GitResult(-1, timed_out=True)
            return self.fetch_result
        if cmd == "merge-base":
            if self.diverged:
                return GitResult(1)
            if self.ahead:
                return GitResult(0 if args[-1] == "HEAD" else 1)
            if args[-1] != "HEAD":
                return GitResult(0)
            return GitResult(0 if self.head == self.remote else 1)
        if cmd == "merge":
            if self.merge_result.ok and self.remote is not None:
                self.head = self.remote
            return self.merge_result
        return GitResult(1, stderr=f"unexpected {args}")

    def ran(self, subcommand: str) -> bool:
        return any(call and call[0] == subcommand for call in self.calls)


class UpdateTestCase(unittest.TestCase):
    def setUp(self) -> None:
        reset_for_tests()
        self._env_save = {
            key: os.environ.get(key) for key in (SKIP_ENV, REEXEC_ENV)
        }
        os.environ.pop(SKIP_ENV, None)
        os.environ.pop(REEXEC_ENV, None)
        self.root = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        reset_for_tests()
        for key, value in self._env_save.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _check(self, git: FakeGit, **kwargs) -> UpdateOutcome:
        buf = StringIO()
        with patch("sys.stdout", buf):
            outcome = check_for_updates(root=self.root, git_runner=git, **kwargs)
        self.output = buf.getvalue()
        return outcome


class SkipAndDiscoverTests(UpdateTestCase):
    def test_skip_env_does_not_run_git(self) -> None:
        os.environ[SKIP_ENV] = "1"

        def boom(*_args, **_kwargs):
            raise AssertionError("git should not run when OMUNCHY_SKIP_UPDATE=1")

        outcome = check_for_updates(root=self.root, git_runner=boom)
        self.assertEqual(outcome.status, "skipped")
        self.assertFalse(outcome.should_reexec)

    def test_skip_env_zero_still_checks(self) -> None:
        os.environ[SKIP_ENV] = "0"
        git = FakeGit()
        outcome = self._check(git)
        self.assertEqual(outcome.status, "up_to_date")
        self.assertTrue(git.ran("fetch"))

    def test_reexec_env_skips_second_launch(self) -> None:
        os.environ[REEXEC_ENV] = "1"

        def boom(*_args, **_kwargs):
            raise AssertionError("git should not run after a self-restart")

        outcome = check_for_updates(root=self.root, git_runner=boom)
        self.assertEqual(outcome.status, "skipped")

    def test_not_a_git_repo_is_silent_skip(self) -> None:
        outcome = self._check(FakeGit(inside=False))
        self.assertEqual(outcome.status, "skipped")
        self.assertFalse(outcome.should_reexec)
        self.assertEqual(self.output, "")

    def test_discover_repo_root_only_package_parent(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            clone = Path(raw) / "Omunchy"
            package = clone / "omunchy"
            package.mkdir(parents=True)
            self.assertIsNone(discover_repo_root(package))
            (clone / ".git").mkdir()
            self.assertEqual(discover_repo_root(package), clone)
            unrelated = clone / "nested" / "omunchy"
            unrelated.mkdir(parents=True)
            self.assertIsNone(discover_repo_root(unrelated))

    def test_git_missing_skips(self) -> None:
        outcome = self._check(FakeGit(git_missing=True))
        self.assertEqual(outcome.status, "skipped")
        self.assertFalse(outcome.should_reexec)

    def test_feature_branch_warns_and_does_not_fetch(self) -> None:
        git = FakeGit(branch="cursor/auto-update")
        outcome = self._check(git)
        self.assertEqual(outcome.status, "skipped")
        self.assertIn("not main", self.output)
        self.assertFalse(git.ran("fetch"))
        self.assertFalse(git.ran("merge"))


class UpdateCheckTests(UpdateTestCase):
    def test_up_to_date_no_reexec(self) -> None:
        git = FakeGit(head="aaa", remote="aaa")
        reexecs: list[int] = []
        outcome = maybe_update_and_reexec(
            root=self.root,
            git_runner=git,
            _reexec=lambda: reexecs.append(1),
        )
        self.assertEqual(outcome.status, "up_to_date")
        self.assertFalse(outcome.updated)
        self.assertFalse(outcome.should_reexec)
        self.assertEqual(reexecs, [])
        self.assertTrue(git.ran("fetch"))
        self.assertFalse(git.ran("merge"))
        self.assertTrue(any(call == ("fetch", "--quiet", "origin") for call in git.calls))

    def test_updated_reexecs_same_args(self) -> None:
        git = FakeGit(head="aaa", remote="bbb")
        execv = []

        def fake_reexec() -> None:
            execv.append(list(os.environ.get(REEXEC_ENV, "")))
            reexec_self(argv=["-m", "omunchy"])

        with (
            patch("omunchy.update.os.execv") as mocked_execv,
            patch("omunchy.update.sys.executable", "/usr/bin/python3"),
            patch("sys.stdout", StringIO()),
        ):
            mocked_execv.side_effect = SystemExit(0)
            with self.assertRaises(SystemExit):
                maybe_update_and_reexec(
                    root=self.root,
                    git_runner=git,
                    _reexec=fake_reexec,
                )
            mocked_execv.assert_called_once_with(
                "/usr/bin/python3",
                ["/usr/bin/python3", "-m", "omunchy"],
            )
        self.assertTrue(git.ran("fetch"))
        self.assertTrue(git.ran("merge"))
        self.assertIn(("--ff-only",), [call[1:2] for call in git.calls if call[0] == "merge"])
        merge_call = next(call for call in git.calls if call[0] == "merge")
        self.assertEqual(merge_call, ("merge", "--ff-only", "origin/main"))
        self.assertEqual(os.environ.get(REEXEC_ENV), "1")

    def test_updated_outcome_without_execv(self) -> None:
        git = FakeGit(head="old", remote="new")
        called = []
        with patch("sys.stdout", StringIO()) as buf:
            outcome = maybe_update_and_reexec(
                root=self.root,
                git_runner=git,
                _reexec=lambda: called.append("reexec"),
            )
            text = buf.getvalue()
        self.assertEqual(outcome.status, "updated")
        self.assertTrue(outcome.updated)
        self.assertTrue(outcome.should_reexec)
        self.assertEqual(called, ["reexec"])
        self.assertIn("updating", text.lower())
        self.assertIn("restarting", text.lower())

    def test_offline_fetch_failure_continues(self) -> None:
        git = FakeGit(fetch_result=GitResult(1, stderr="Could not resolve host"))
        reexecs: list[int] = []
        with patch("sys.stdout", StringIO()) as buf:
            outcome = maybe_update_and_reexec(
                root=self.root,
                git_runner=git,
                _reexec=lambda: reexecs.append(1),
            )
            text = buf.getvalue()
        self.assertEqual(outcome.status, "failed")
        self.assertFalse(outcome.should_reexec)
        self.assertEqual(reexecs, [])
        self.assertFalse(git.ran("merge"))
        self.assertIn("offline", text.lower())

    def test_offline_timeout_continues(self) -> None:
        git = FakeGit(fetch_timeout=True)
        outcome = self._check(git)
        self.assertEqual(outcome.status, "failed")
        self.assertIn("offline", self.output.lower())
        self.assertFalse(git.ran("merge"))
        self.assertFalse(outcome.should_reexec)

    def test_diverged_warns_and_continues(self) -> None:
        git = FakeGit(head="local", remote="origin", diverged=True)
        outcome = self._check(git)
        self.assertEqual(outcome.status, "diverged")
        self.assertFalse(outcome.should_reexec)
        self.assertFalse(git.ran("merge"))
        self.assertIn("differs", self.output.lower())

    def test_local_ahead_is_up_to_date(self) -> None:
        git = FakeGit(head="newer", remote="older", ahead=True)
        outcome = self._check(git)
        self.assertEqual(outcome.status, "up_to_date")
        self.assertFalse(git.ran("merge"))

    def test_dirty_ff_failure_continues(self) -> None:
        git = FakeGit(head="aaa", remote="bbb", merge_result=GitResult(1, stderr="uncommitted"))
        outcome = self._check(git)
        self.assertEqual(outcome.status, "diverged")
        self.assertTrue(git.ran("merge"))
        self.assertFalse(outcome.should_reexec)

    def test_maybe_update_runs_once(self) -> None:
        git = FakeGit()
        first = maybe_update_and_reexec(root=self.root, git_runner=git, _reexec=lambda: None)
        second = maybe_update_and_reexec(root=self.root, git_runner=git, _reexec=lambda: None)
        self.assertEqual(first.status, "up_to_date")
        self.assertEqual(second.status, "skipped")
        self.assertEqual(sum(1 for call in git.calls if call[0] == "fetch"), 1)

    def test_main_calls_update_before_pygame_init(self) -> None:
        import inspect

        from omunchy.app import main
        from omunchy import __main__ as package_main

        source = inspect.getsource(main)
        self.assertIn("maybe_update_and_reexec", source)
        self.assertLess(source.index("maybe_update_and_reexec"), source.index("pygame.init"))
        main_text = Path(package_main.__file__).read_text()
        self.assertIn("maybe_update_and_reexec", main_text)
        self.assertLess(
            main_text.index("maybe_update_and_reexec"),
            main_text.index("from omunchy.app import main"),
        )
        self.assertIn("splash=True", source)
        self.assertIn("splash=True", main_text)

    def test_progress_checking_then_done(self) -> None:
        phases: list[str] = []
        outcome = self._check(FakeGit(), on_progress=lambda phase, _msg: phases.append(phase))
        self.assertEqual(outcome.status, "up_to_date")
        self.assertEqual(phases, ["checking", "done"])
        self.assertEqual(splash_phase_for(outcome), "done")

    def test_progress_checking_updating_done(self) -> None:
        phases: list[str] = []
        outcome = self._check(
            FakeGit(head="aaa", remote="bbb"),
            on_progress=lambda phase, _msg: phases.append(phase),
        )
        self.assertEqual(outcome.status, "updated")
        self.assertEqual(phases, ["checking", "updating", "done"])
        self.assertEqual(splash_phase_for(outcome), "done")

    def test_progress_offline_on_fetch_failure(self) -> None:
        phases: list[str] = []
        outcome = self._check(
            FakeGit(fetch_result=GitResult(1, stderr="Could not resolve host")),
            on_progress=lambda phase, _msg: phases.append(phase),
        )
        self.assertEqual(outcome.status, "failed")
        self.assertEqual(phases, ["checking", "offline"])
        self.assertEqual(splash_phase_for(outcome), "offline")

    def test_progress_failed_when_diverged(self) -> None:
        phases: list[str] = []
        outcome = self._check(
            FakeGit(head="local", remote="origin", diverged=True),
            on_progress=lambda phase, _msg: phases.append(phase),
        )
        self.assertEqual(outcome.status, "diverged")
        self.assertEqual(phases, ["checking", "failed"])
        self.assertEqual(splash_phase_for(outcome), "failed")

    def test_splash_flag_skipped_when_skip_env(self) -> None:
        os.environ[SKIP_ENV] = "1"
        opened: list[str] = []

        def boom(*_args, **_kwargs):
            raise AssertionError("git should not run when OMUNCHY_SKIP_UPDATE=1")

        with patch("omunchy.update_splash.run_update_splash", side_effect=lambda **_k: opened.append("splash")):
            outcome = maybe_update_and_reexec(root=self.root, git_runner=boom, splash=True)
        self.assertEqual(outcome.status, "skipped")
        self.assertEqual(opened, [])

    def test_splash_flag_skipped_after_reexec_env(self) -> None:
        os.environ[REEXEC_ENV] = "1"
        opened: list[str] = []
        with patch("omunchy.update_splash.run_update_splash", side_effect=lambda **_k: opened.append("splash")):
            outcome = maybe_update_and_reexec(
                root=self.root,
                git_runner=lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("no git")),
                splash=True,
            )
        self.assertEqual(outcome.status, "skipped")
        self.assertEqual(opened, [])

    def test_splash_true_delegates_to_splash(self) -> None:
        fake = UpdateOutcome("up_to_date", "already up to date")
        git = FakeGit()
        with patch("omunchy.update_splash.run_update_splash", return_value=fake) as run:
            outcome = maybe_update_and_reexec(
                root=self.root,
                git_runner=git,
                splash=True,
                _reexec=lambda: None,
            )
        run.assert_called_once()
        self.assertEqual(outcome.status, "up_to_date")
        self.assertFalse(git.ran("fetch"))


class RunGitTests(unittest.TestCase):
    def test_timeout_becomes_failed_result(self) -> None:
        with patch("omunchy.update.shutil.which", return_value="/usr/bin/git"):
            with patch("omunchy.update.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 12)):
                result = run_git(["fetch", "origin"], Path("."), timeout=12)
        self.assertTrue(result.timed_out)
        self.assertFalse(result.ok)

    def test_missing_git_binary(self) -> None:
        with patch("omunchy.update.shutil.which", return_value=None):
            result = run_git(["status"], Path("."))
        self.assertTrue(result.missing)
        self.assertFalse(result.ok)

    def test_passes_timeout_and_no_prompt_env(self) -> None:
        completed = subprocess.CompletedProcess(["git"], 0, stdout="ok", stderr="")
        with patch("omunchy.update.shutil.which", return_value="/usr/bin/git"):
            with patch("omunchy.update.subprocess.run", return_value=completed) as run:
                run_git(["fetch", "--quiet", "origin"], Path("/tmp/repo"), timeout=DEFAULT_TIMEOUT)
        kwargs = run.call_args.kwargs
        self.assertEqual(kwargs["timeout"], DEFAULT_TIMEOUT)
        self.assertEqual(kwargs["env"]["GIT_TERMINAL_PROMPT"], "0")
        self.assertIn("BatchMode=yes", kwargs["env"]["GIT_SSH_COMMAND"])
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[0], "/usr/bin/git")
        self.assertIn("http.lowSpeedLimit=1000", cmd)


if __name__ == "__main__":
    unittest.main()
