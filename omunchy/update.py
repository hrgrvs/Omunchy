"""Startup git self-update. Runs before the game loop.

A git clone with network can fast-forward from origin (prefers ``main``).
Anything else — zip install, offline, timeout, diverged local commits —
continues with the current code so kids can still play.

The launch path can show a pygame splash (status bar + Munchy running)
while this runs. Tests and re-exec after a successful pull skip the splash.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Callable, Sequence

SKIP_ENV = "OMUNCHY_SKIP_UPDATE"
REEXEC_ENV = "OMUNCHY_UPDATED"
DEFAULT_TIMEOUT = 12
PREFERRED_BRANCH = "main"
FALLBACK_BRANCHES = (PREFERRED_BRANCH, "master")

_ran = False


@dataclass(frozen=True)
class GitResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    missing: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out and not self.missing


@dataclass(frozen=True)
class UpdateOutcome:
    status: str
    message: str
    updated: bool = False
    should_reexec: bool = False


GitRunner = Callable[[Sequence[str], Path, float], GitResult]
ProgressFn = Callable[[str, str], None]


def _env_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() not in ("", "0", "false", "no", "off")


def _say(message: str) -> None:
    print(message, flush=True)


def _note(on_progress: ProgressFn | None, phase: str, message: str = "") -> None:
    if on_progress is not None:
        on_progress(phase, message)


def splash_phase_for(outcome: UpdateOutcome) -> str:
    """Map an update outcome to a splash status-bar phase."""
    if outcome.status in ("up_to_date", "updated"):
        return "done"
    if outcome.status == "failed":
        return "offline"
    if outcome.status == "diverged":
        return "failed"
    return "done"


def reset_for_tests() -> None:
    """Allow tests to call maybe_update_and_reexec more than once."""
    global _ran
    _ran = False


def discover_repo_root(start: Path | None = None) -> Path | None:
    """Return the game checkout root if this install lives in a git clone.

    Only the package parent is considered (``<clone>/omunchy/update.py`` →
    ``<clone>``). Walking further up would pick an unrelated parent repo.
    """
    package_dir = Path(__file__).resolve().parent if start is None else start
    root = package_dir.parent
    if (root / ".git").exists():
        return root
    return None


def run_git(args: Sequence[str], cwd: Path, timeout: float = DEFAULT_TIMEOUT) -> GitResult:
    """Run ``git`` with a timeout and no credential / SSH prompts."""
    git = shutil.which("git")
    if not git:
        return GitResult(127, missing=True, stderr="git not found")
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_MERGE_AUTOEDIT"] = "no"
    env["GCM_INTERACTIVE"] = "Never"
    env.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes -o ConnectTimeout=10")
    cmd = [
        git,
        "-c",
        "http.lowSpeedLimit=1000",
        "-c",
        f"http.lowSpeedTime={max(1, int(timeout) - 2)}",
        *args,
    ]
    try:
        completed = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return GitResult(-1, timed_out=True, stderr="timed out")
    except OSError as exc:
        return GitResult(127, missing=True, stderr=str(exc))
    return GitResult(completed.returncode, completed.stdout or "", completed.stderr or "")


def _ref_exists(runner: GitRunner, root: Path, ref: str, timeout: float) -> bool:
    return runner(["rev-parse", "--verify", "--quiet", ref], root, timeout).ok


def _pick_target(
    runner: GitRunner,
    root: Path,
    current_branch: str,
    timeout: float,
) -> str | None:
    """Prefer origin/main when we are on main; otherwise same-name origin branch."""
    if current_branch == PREFERRED_BRANCH and _ref_exists(runner, root, "origin/main", timeout):
        return "origin/main"
    if current_branch in FALLBACK_BRANCHES:
        remote = f"origin/{current_branch}"
        if _ref_exists(runner, root, remote, timeout):
            return remote
    if not current_branch and _ref_exists(runner, root, "origin/main", timeout):
        return "origin/main"
    return None


def check_for_updates(
    root: Path | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    git_runner: GitRunner | None = None,
    *,
    on_progress: ProgressFn | None = None,
) -> UpdateOutcome:
    """Fetch/ff-only pull when this is a clone. Never raises for git/network errors."""
    if _env_truthy(os.environ.get(SKIP_ENV)):
        return UpdateOutcome("skipped", "update check skipped")
    if _env_truthy(os.environ.get(REEXEC_ENV)):
        return UpdateOutcome("skipped", "already updated this launch")

    runner = git_runner or run_git
    if root is None:
        root = discover_repo_root()
    if root is None:
        return UpdateOutcome("skipped", "not a git checkout")

    probe = runner(["rev-parse", "--is-inside-work-tree"], root, timeout)
    if probe.missing:
        return UpdateOutcome("skipped", "git not found")
    if probe.timed_out:
        _say("Omunchy — update check failed (offline). Starting current version.")
        _note(on_progress, "offline")
        return UpdateOutcome("failed", "timed out")
    if not probe.ok or probe.stdout.strip() != "true":
        return UpdateOutcome("skipped", "not a git checkout")

    remote = runner(["remote", "get-url", "origin"], root, timeout)
    if not remote.ok:
        return UpdateOutcome("skipped", "no origin remote")

    branch = runner(["symbolic-ref", "--short", "HEAD"], root, timeout)
    current_branch = branch.stdout.strip() if branch.ok else ""
    if current_branch and current_branch not in FALLBACK_BRANCHES:
        _say(f"Omunchy — on branch {current_branch} (not main); starting current version.")
        return UpdateOutcome("skipped", f"not on main ({current_branch})")

    before = runner(["rev-parse", "HEAD"], root, timeout)
    if not before.ok:
        _say("Omunchy — update check failed (offline). Starting current version.")
        _note(on_progress, "offline")
        return UpdateOutcome("failed", "could not read HEAD")
    before_sha = before.stdout.strip()

    _say("Omunchy — checking for updates…")
    _note(on_progress, "checking")
    fetched = runner(["fetch", "--quiet", "origin"], root, timeout)
    if fetched.timed_out or not fetched.ok:
        _say("Omunchy — update check failed (offline). Starting current version.")
        _note(on_progress, "offline")
        return UpdateOutcome("failed", "timed out" if fetched.timed_out else "fetch failed")

    target = _pick_target(runner, root, current_branch, timeout)
    if target is None:
        _say("Omunchy — no origin/main. Starting current version.")
        return UpdateOutcome("skipped", "no origin/main")

    remote_sha = runner(["rev-parse", target], root, timeout)
    if not remote_sha.ok:
        _say("Omunchy — update check failed (offline). Starting current version.")
        _note(on_progress, "offline")
        return UpdateOutcome("failed", f"missing {target}")
    if remote_sha.stdout.strip() == before_sha:
        _say("Omunchy — up to date.")
        _note(on_progress, "done")
        return UpdateOutcome("up_to_date", "already up to date")

    can_ff = runner(["merge-base", "--is-ancestor", "HEAD", target], root, timeout)
    if not can_ff.ok:
        remote_is_ancestor = runner(["merge-base", "--is-ancestor", target, "HEAD"], root, timeout)
        if remote_is_ancestor.ok:
            _say("Omunchy — up to date.")
            _note(on_progress, "done")
            return UpdateOutcome("up_to_date", "local is ahead")
        _say("Omunchy — local copy differs from origin; starting current version.")
        _note(on_progress, "failed")
        return UpdateOutcome("diverged", "diverged; not fast-forwarding")

    _say("Omunchy — updating…")
    _note(on_progress, "updating")
    merged = runner(["merge", "--ff-only", target], root, timeout)
    if not merged.ok:
        _say("Omunchy — local copy differs from origin; starting current version.")
        _note(on_progress, "failed")
        return UpdateOutcome("diverged", "ff-only merge failed")

    after = runner(["rev-parse", "HEAD"], root, timeout)
    after_sha = after.stdout.strip() if after.ok else before_sha
    if after_sha != before_sha:
        _say("Omunchy — updated. Restarting…")
        _note(on_progress, "done")
        return UpdateOutcome("updated", "updated", updated=True, should_reexec=True)

    _say("Omunchy — up to date.")
    _note(on_progress, "done")
    return UpdateOutcome("up_to_date", "already up to date")


def reexec_self(argv: Sequence[str] | None = None) -> None:
    """Replace this process with the same interpreter and args (Linux / macOS)."""
    os.environ[REEXEC_ENV] = "1"
    args = [sys.executable, *(argv if argv is not None else sys.argv)]
    os.execv(sys.executable, args)


def maybe_update_and_reexec(
    root: Path | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    git_runner: GitRunner | None = None,
    *,
    _reexec: Callable[[], None] | None = None,
    splash: bool = False,
    min_splash: float | None = None,
    on_progress: ProgressFn | None = None,
) -> UpdateOutcome:
    """Entry point for ``__main__`` / ``main()``. Re-execs after a successful pull.

    ``splash=True`` shows the kid-friendly status bar + Munchy run while the
    check runs. Skipped when ``OMUNCHY_SKIP_UPDATE`` is set, after a self-restart
    (``OMUNCHY_UPDATED``), or when this is not a git clone. Tests keep the
    default (no splash).
    """
    global _ran
    if _ran:
        return UpdateOutcome("skipped", "already ran")
    if splash:
        from omunchy.update_splash import run_update_splash, should_show_splash

        if should_show_splash(root):
            outcome = run_update_splash(
                root=root,
                timeout=timeout,
                git_runner=git_runner,
                on_progress=on_progress,
                min_seconds=min_splash,
            )
            _ran = True
            if outcome.should_reexec:
                (_reexec or reexec_self)()
            return outcome
    outcome = check_for_updates(
        root=root,
        timeout=timeout,
        git_runner=git_runner,
        on_progress=on_progress,
    )
    _ran = True
    if outcome.should_reexec:
        (_reexec or reexec_self)()
    return outcome
