"""Muncher and Troggle movement / collision."""

from __future__ import annotations

from dataclasses import dataclass
import random

from omunch.constants import COLS, ROWS


@dataclass
class Actor:
    row: int
    col: int
    move_timer: float = 0.0

    @property
    def pos(self) -> tuple[int, int]:
        return self.row, self.col


class Muncher(Actor):
    facing: tuple[int, int] = (1, 0)
    chomp_timer: float = 0.0
    iframe_timer: float = 0.0
    hop_timer: float = 0.0

    def can_move(self) -> bool:
        return self.chomp_timer <= 0

    def invulnerable(self) -> bool:
        return self.iframe_timer > 0

    def tick(self, dt: float) -> None:
        self.chomp_timer = max(0.0, self.chomp_timer - dt)
        self.iframe_timer = max(0.0, self.iframe_timer - dt)
        self.hop_timer = max(0.0, self.hop_timer - dt)

    def try_step(self, dr: int, dc: int) -> bool:
        if not self.can_move():
            return False
        nr, nc = self.row + dr, self.col + dc
        if not (0 <= nr < ROWS and 0 <= nc < COLS):
            return False
        if dr or dc:
            self.facing = (dc, dr)
        self.row, self.col = nr, nc
        self.hop_timer = 0.12
        return True


class Troggle(Actor):
    kind: str = "wander"  # wander | chase
    interval: float = 0.75
    heading: tuple[int, int] = (1, 0)

    def tick_and_maybe_move(self, dt: float, prey: tuple[int, int], rng: random.Random) -> None:
        self.move_timer -= dt
        if self.move_timer > 0:
            return
        self.move_timer = self.interval
        if self.kind == "chase":
            self._chase_step(prey, rng)
        else:
            self._wander_step(rng)

    def _apply(self, dr: int, dc: int) -> bool:
        nr, nc = self.row + dr, self.col + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS:
            self.row, self.col = nr, nc
            if dr or dc:
                self.heading = (dc, dr)
            return True
        return False

    def _wander_step(self, rng: random.Random) -> None:
        dc, dr = self.heading
        if rng.random() < 0.22 or not self._apply(dr, dc):
            dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
            rng.shuffle(dirs)
            for ndc, ndr in dirs:
                if self._apply(ndr, ndc):
                    return

    def _chase_step(self, prey: tuple[int, int], rng: random.Random) -> None:
        pr, pc = prey
        options: list[tuple[int, int]] = []
        if pr < self.row:
            options.append((-1, 0))
        elif pr > self.row:
            options.append((1, 0))
        if pc < self.col:
            options.append((0, -1))
        elif pc > self.col:
            options.append((0, 1))
        # Fairness: sometimes wander so kids can escape.
        if not options or rng.random() < 0.22:
            self._wander_step(rng)
            return
        rng.shuffle(options)
        for dr, dc in options:
            if self._apply(dr, dc):
                return
        self._wander_step(rng)


def spawn_troggles(level: int, player: tuple[int, int], rng: random.Random) -> list[Troggle]:
    """1 wanderer early; a chaser joins later. Never on/next to the player."""
    pr, pc = player
    corners = [(0, 0), (0, COLS - 1), (ROWS - 1, 0), (ROWS - 1, COLS - 1)]
    far = [p for p in corners if abs(p[0] - pr) + abs(p[1] - pc) >= 4]
    rng.shuffle(far)
    if not far:
        far = [(0, COLS - 1)]

    count = 1
    if level >= 2:
        count = 2
    if level >= 5:
        count = 3
    count = min(count, len(far) + 2)

    spots = list(far)
    extras = [(0, COLS // 2), (ROWS - 1, COLS // 2), (ROWS // 2, 0), (ROWS // 2, COLS - 1)]
    for extra in extras:
        if extra not in spots and abs(extra[0] - pr) + abs(extra[1] - pc) >= 4:
            spots.append(extra)

    troggles: list[Troggle] = []
    interval = max(0.42, 0.82 - (level - 1) * 0.04)
    for i in range(min(count, len(spots))):
        row, col = spots[i]
        kind = "chase" if (i == 1 and level >= 3) or (i == 2) else "wander"
        t = Troggle(row=row, col=col, kind=kind, interval=interval if kind == "wander" else interval + 0.12)
        t.heading = [(1, 0), (-1, 0), (0, 1), (0, -1)][i % 4]
        t.move_timer = 0.55 + i * 0.2
        troggles.append(t)
    return troggles


def safe_player_spawn(occupied: set[tuple[int, int]], rng: random.Random) -> tuple[int, int]:
    """Prefer a central-ish empty cell."""
    preferred = [
        (ROWS // 2, COLS // 2),
        (ROWS // 2, COLS // 2 - 1),
        (ROWS // 2 + 1, COLS // 2),
        (ROWS // 2 - 1, COLS // 2),
        (ROWS - 2, 2),
        (2, 2),
    ]
    for pos in preferred:
        if pos not in occupied:
            return pos
    candidates = [(r, c) for r in range(ROWS) for c in range(COLS) if (r, c) not in occupied]
    return candidates[rng.randrange(len(candidates))] if candidates else (0, 0)