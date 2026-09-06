"""Kid-friendly pygame splash while the launch auto-update runs.

16:9 / fullscreen-friendly. A status bar tracks checking → updating →
done / failed / offline, and Munchy hops across the screen. The git work
runs on a background thread so the animation never freezes.

If the check finishes quickly the splash still shows for a short beat.
After a successful update the process re-execs with ``OMUNCHY_UPDATED=1``
and this splash is skipped so kids are not stuck on a second loading card.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
import threading
import time
from typing import Callable

from omunchy.constants import (
    BG,
    BG_DEEP,
    CELL_BORDER,
    CREAM,
    CYAN,
    GOLD,
    GREEN,
    HUD_BG,
    ORANGE,
    TITLE,
    WHITE,
    WINDOW_H,
    WINDOW_W,
    YELLOW,
)
from omunchy.update import (
    DEFAULT_TIMEOUT,
    REEXEC_ENV,
    SKIP_ENV,
    GitRunner,
    ProgressFn,
    UpdateOutcome,
    _env_truthy,
    check_for_updates,
    discover_repo_root,
    splash_phase_for,
)

MIN_SPLASH_SECONDS = 1.35
SPLASH_MUNCHY_SIZE = 96
RUN_SPEED = 320.0
HOP_HZ = 2.4
HOP_PX = 22
RUN_MARGIN = 48
BAR_W = 720
BAR_H = 28
GROUND_Y = 500

PHASE_LABELS = {
    "checking": "Checking for updates…",
    "updating": "Updating…",
    "done": "Ready to play!",
    "failed": "Couldn't update — playing this version.",
    "offline": "Offline — playing this version.",
}

PHASE_FILL = {
    "checking": 0.38,
    "updating": 0.72,
    "done": 1.0,
    "failed": 0.48,
    "offline": 0.48,
}

PHASE_COLORS = {
    "checking": GOLD,
    "updating": YELLOW,
    "done": GREEN,
    "failed": ORANGE,
    "offline": CYAN,
}


def should_show_splash(root: Path | None = None) -> bool:
    """False after skip-env, a self-restart, or a non-git install."""
    if _env_truthy(os.environ.get(SKIP_ENV)):
        return False
    if _env_truthy(os.environ.get(REEXEC_ENV)):
        return False
    if root is not None:
        return True
    return discover_repo_root() is not None


def status_bar_label(phase: str) -> str:
    return PHASE_LABELS.get(phase, PHASE_LABELS["checking"])


def status_bar_color(phase: str) -> tuple[int, int, int]:
    return PHASE_COLORS.get(phase, GOLD)


def status_bar_fill(phase: str, now: float = 0.0) -> float:
    """0–1 fill. Checking pulses so the bar still feels alive."""
    base = PHASE_FILL.get(phase, 0.3)
    if phase == "checking":
        pulse = 0.08 * (0.5 + 0.5 * math.sin(now * 4.0))
        return max(0.0, min(1.0, base + pulse))
    return max(0.0, min(1.0, base))


def munchy_run_x(now: float, screen_w: int, sprite_w: int) -> int:
    """Loop Munchy from just off the left edge to just off the right."""
    travel = screen_w + sprite_w + RUN_MARGIN * 2
    return int(-sprite_w - RUN_MARGIN + (now * RUN_SPEED) % travel)


def munchy_hop(now: float) -> int:
    return int(abs(math.sin(now * HOP_HZ * math.pi * 2.0)) * HOP_PX)


def munchy_frame(now: float) -> int:
    return int(now * 8)


def munchy_chomping(now: float) -> bool:
    return int(now * 3) % 5 == 0


@dataclass
class SplashState:
    phase: str = "checking"
    message: str = ""

    def set_phase(self, phase: str, message: str = "") -> None:
        self.phase = phase
        self.message = message

    def label(self) -> str:
        return self.message or status_bar_label(self.phase)


def _font(size: int, bold: bool = False):
    import pygame

    names = ("DejaVu Sans Mono", "Liberation Mono", "FreeMono", "monospace")
    for name in names:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


def _open_splash_screen(pygame_mod, fullscreen: bool = True):
    """Same 16:9 logical frame as the game; prefer fullscreen + SCALED."""
    logical = (WINDOW_W, WINDOW_H)
    attempts: list[int] = []
    if fullscreen:
        attempts.extend((pygame_mod.FULLSCREEN | pygame_mod.SCALED, pygame_mod.FULLSCREEN))
    attempts.extend((pygame_mod.SCALED | pygame_mod.RESIZABLE, pygame_mod.RESIZABLE, 0))
    last_error = None
    for flags in attempts:
        try:
            return pygame_mod.display.set_mode(logical, flags)
        except pygame_mod.error as exc:
            last_error = exc
    if last_error is not None:
        return pygame_mod.display.set_mode(logical)
    return pygame_mod.display.set_mode(logical)


def _shutdown_splash_display() -> None:
    """Drop video so the game can ``pygame.init()`` / mixer.pre_init cleanly."""
    try:
        from omunchy import sprites

        sprites._CACHE.clear()
    except Exception:
        pass
    try:
        import pygame

        if pygame.display.get_init():
            pygame.display.quit()
        if pygame.font.get_init():
            pygame.font.quit()
    except Exception:
        pass


def draw_update_splash(surface, now: float, phase: str, message: str = "") -> None:
    """Paint one splash frame onto any 16:9 surface (window or test buffer)."""
    import pygame

    from omunchy.sprites import draw_outlined_text, muncher_surface
    from omunchy.title_art import draw_title_word

    surface.fill(BG)
    cx = WINDOW_W // 2
    logo_bottom = draw_title_word(surface, now + 1.6, cx, 56)
    draw_outlined_text(surface, "Getting ready…", _font(28, True), CREAM, (cx, logo_bottom + 28))

    ground = pygame.Rect(0, GROUND_Y, WINDOW_W, 18)
    pygame.draw.rect(surface, (14, 56, 36), ground)
    pygame.draw.rect(surface, (28, 92, 56), (0, GROUND_Y, WINDOW_W, 4))
    # Little tufts so the track reads as grass, not a UI rule.
    for x in range(24, WINDOW_W, 46):
        pygame.draw.rect(surface, (48, 140, 72), (x, GROUND_Y - 6, 4, 8))
        pygame.draw.rect(surface, (36, 110, 58), (x + 8, GROUND_Y - 4, 3, 6))

    sprite = muncher_surface(munchy_frame(now), 1, munchy_chomping(now), False)
    if sprite.get_width() != SPLASH_MUNCHY_SIZE:
        sprite = pygame.transform.scale(sprite, (SPLASH_MUNCHY_SIZE, SPLASH_MUNCHY_SIZE))
    hop = munchy_hop(now)
    x = munchy_run_x(now, WINDOW_W, sprite.get_width())
    dest = sprite.get_rect()
    dest.midbottom = (x + dest.width // 2, GROUND_Y + 2 - hop)
    surface.blit(sprite, dest)

    bar_left = (WINDOW_W - BAR_W) // 2
    bar_top = 568
    track = pygame.Rect(bar_left, bar_top, BAR_W, BAR_H)
    pygame.draw.rect(surface, HUD_BG, track.inflate(8, 18), border_radius=10)
    pygame.draw.rect(surface, BG_DEEP, track, border_radius=8)
    pygame.draw.rect(surface, CELL_BORDER, track, 2, border_radius=8)
    fill_w = max(0, int((BAR_W - 6) * status_bar_fill(phase, now)))
    if fill_w > 0:
        fill = pygame.Rect(bar_left + 3, bar_top + 3, fill_w, BAR_H - 6)
        pygame.draw.rect(surface, status_bar_color(phase), fill, border_radius=6)
    label = message or status_bar_label(phase)
    draw_outlined_text(surface, label, _font(22, True), WHITE, (cx, bar_top - 28))
    draw_outlined_text(surface, TITLE, _font(16), CREAM, (cx, WINDOW_H - 28))


def _pump_quit_or_skip(pygame_mod, update_done: bool) -> bool:
    """Keep the window alive. After the check finishes, a tap skips the hold."""
    skip = False
    for event in pygame_mod.event.get():
        if event.type == pygame_mod.QUIT:
            skip = update_done
        elif event.type == pygame_mod.KEYDOWN and event.key in (
            pygame_mod.K_ESCAPE,
            pygame_mod.K_RETURN,
            pygame_mod.K_SPACE,
        ):
            skip = update_done
    return skip


def run_update_splash(
    root: Path | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    git_runner: GitRunner | None = None,
    *,
    on_progress: ProgressFn | None = None,
    min_seconds: float | None = None,
    fullscreen: bool = True,
    _draw: Callable | None = None,
    _clock: Callable[[], float] | None = None,
) -> UpdateOutcome:
    """Show the splash, run ``check_for_updates`` off-thread, return the outcome.

    Does not re-exec; ``maybe_update_and_reexec`` handles that. If pygame cannot
    open a display, falls back to a console-only check so launch still works.
    """
    hold = MIN_SPLASH_SECONDS if min_seconds is None else max(0.0, min_seconds)
    state = SplashState()
    lock = threading.Lock()

    def progress(phase: str, message: str = "") -> None:
        with lock:
            state.set_phase(phase, message)
        if on_progress is not None:
            on_progress(phase, message)

    outcome_box: list[UpdateOutcome] = []
    error_box: list[BaseException] = []

    def work() -> None:
        try:
            outcome_box.append(
                check_for_updates(
                    root=root,
                    timeout=timeout,
                    git_runner=git_runner,
                    on_progress=progress,
                )
            )
        except BaseException as exc:  # noqa: BLE001 — splash must not kill launch
            error_box.append(exc)

    try:
        import pygame
    except ImportError:
        return check_for_updates(root=root, timeout=timeout, git_runner=git_runner, on_progress=on_progress)

    opened = False
    try:
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_caption(TITLE)
        screen = _open_splash_screen(pygame, fullscreen=fullscreen)
        opened = True
    except Exception:
        _shutdown_splash_display()
        return check_for_updates(root=root, timeout=timeout, git_runner=git_runner, on_progress=on_progress)

    worker = threading.Thread(target=work, name="omunchy-update", daemon=True)
    worker.start()
    clock = pygame.time.Clock()
    now_fn = _clock or time.monotonic
    started = now_fn()
    anim = 0.0
    paint = _draw or draw_update_splash
    try:
        while True:
            dt = clock.tick(60) / 1000.0
            anim += dt
            elapsed = now_fn() - started
            worker_done = not worker.is_alive()
            skip_hold = _pump_quit_or_skip(pygame, worker_done)
            with lock:
                phase, label = state.phase, state.label()
            if worker_done and outcome_box:
                final = splash_phase_for(outcome_box[0])
                if phase != final and outcome_box[0].status != "skipped":
                    phase = final
                    label = status_bar_label(final)
                elif outcome_box[0].status == "skipped" and phase == "checking":
                    phase = "done"
                    label = status_bar_label("done")
            paint(screen, anim, phase, label)
            pygame.display.flip()
            if worker_done and (elapsed >= hold or skip_hold):
                break
    finally:
        worker.join(timeout=0.2)
        if opened:
            _shutdown_splash_display()

    if error_box:
        return UpdateOutcome("failed", str(error_box[0]))
    if outcome_box:
        return outcome_box[0]
    return check_for_updates(root=root, timeout=timeout, git_runner=git_runner, on_progress=on_progress)
