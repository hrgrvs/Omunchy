"""Muncher and Troggle movement / collision.

Troggle types
-------------
wander     Random walk (existing).
chase      Seeks the player, with occasional wander so kids can escape (existing).
fire       Wanders, then breathes fire onto the single square directly in front
           (facing direction). Player on that cell while fire is active loses a life.
exploder   If the player stands on a *cardinal* neighbor (up/down/left/right —
           diagonal is safe), it telegraphs then explodes. 4-dir is the kid-fair
           choice: you can stand diagonally without popping it.
hunter     Hunts and eats other Troggles (removes them). Contact with the player
           still costs a life.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random

from omunchy.board import board_size_for_level
from omunchy.constants import (
    EXPLODE_WINDUP,
    FIRE_COOLDOWN,
    FIRE_DURATION,
    FIRE_WINDUP,
    MAX_COLS,
    MAX_ROWS,
    TROGGLE_INTERVAL_FLOOR,
    TROGGLE_INTERVAL_START,
    TROGGLE_INTERVAL_STEP,
    TROGGLE_KIND_INTERVAL_MIN,
)

TROGGLE_KINDS = ("wander", "chase", "fire", "exploder", "hunter")

# Extra delay vs the level's base step interval. Hunter is a bit quicker.
_KIND_INTERVAL_BIAS = {
    "wander": 0.0,
    "chase": 0.14,
    "fire": 0.10,
    "exploder": 0.18,
    "hunter": -0.06,
}


def is_cardinal_adjacent(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """True when a and b share a side (4-dir). Diagonal is not adjacent."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def front_cell(row: int, col: int, heading: tuple[int, int]) -> tuple[int, int]:
    """Cell directly in front. heading is (dc, dr), matching Troggle.heading."""
    dc, dr = heading
    return row + dr, col + dc


@dataclass
class Actor:
    row: int
    col: int
    move_timer: float = 0.0

    @property
    def pos(self) -> tuple[int, int]:
        return self.row, self.col


@dataclass
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

    def try_step(self, dr: int, dc: int, rows: int = MAX_ROWS, cols: int = MAX_COLS) -> bool:
        if not self.can_move():
            return False
        nr, nc = self.row + dr, self.col + dc
        if not (0 <= nr < rows and 0 <= nc < cols):
            return False
        if dr or dc:
            self.facing = (dc, dr)
        self.row, self.col = nr, nc
        self.hop_timer = 0.12
        return True


@dataclass
class Troggle(Actor):
    kind: str = "wander"
    interval: float = 1.15
    heading: tuple[int, int] = (1, 0)
    fire_cooldown: float = 2.2
    fire_windup: float = 0.0
    fire_active: float = 0.0
    explode_windup: float = 0.0
    exploded: bool = False
    just_boomed: bool = False
    _others: tuple["Troggle", ...] = field(default=(), repr=False, compare=False)

    def front_cell(self) -> tuple[int, int]:
        return front_cell(self.row, self.col, self.heading)

    @property
    def is_firing(self) -> bool:
        return self.kind == "fire" and self.fire_active > 0

    @property
    def is_winding_fire(self) -> bool:
        return self.kind == "fire" and self.fire_windup > 0

    @property
    def is_telegraphing(self) -> bool:
        return self.kind == "exploder" and self.explode_windup > 0

    def update(
        self,
        dt: float,
        prey: tuple[int, int],
        rng: random.Random,
        rows: int,
        cols: int,
        others: tuple["Troggle", ...] | list["Troggle"] = (),
    ) -> None:
        self._others = tuple(others)
        self.tick_specials(dt, prey, rows, cols)
        self.tick_and_maybe_move(dt, prey, rng, rows, cols)

    def tick_specials(self, dt: float, prey: tuple[int, int], rows: int, cols: int) -> None:
        self.just_boomed = False
        if self.kind == "fire":
            self._tick_fire(dt, rows, cols)
        elif self.kind == "exploder" and not self.exploded:
            self._tick_exploder(dt, prey)

    def _tick_fire(self, dt: float, rows: int, cols: int) -> None:
        if self.fire_active > 0:
            self.fire_active = max(0.0, self.fire_active - dt)
            return
        if self.fire_windup > 0:
            self.fire_windup = max(0.0, self.fire_windup - dt)
            if self.fire_windup <= 0:
                fr, fc = self.front_cell()
                if 0 <= fr < rows and 0 <= fc < cols:
                    self.fire_active = FIRE_DURATION
                self.fire_cooldown = FIRE_COOLDOWN
            return
        self.fire_cooldown = max(0.0, self.fire_cooldown - dt)
        if self.fire_cooldown <= 0:
            self.fire_windup = FIRE_WINDUP

    def _tick_exploder(self, dt: float, prey: tuple[int, int]) -> None:
        if self.explode_windup > 0:
            self.explode_windup = max(0.0, self.explode_windup - dt)
            if self.explode_windup <= 0:
                self.just_boomed = True
                self.exploded = True
            return
        if is_cardinal_adjacent(self.pos, prey):
            self.explode_windup = EXPLODE_WINDUP

    def tick_and_maybe_move(
        self,
        dt: float,
        prey: tuple[int, int],
        rng: random.Random,
        rows: int = MAX_ROWS,
        cols: int = MAX_COLS,
    ) -> None:
        if self._locked_in_place():
            return
        self.move_timer -= dt
        if self.move_timer > 0:
            return
        self.move_timer = self.interval
        if self.kind == "chase":
            self._chase_step(prey, rng, rows, cols)
        elif self.kind == "hunter":
            self._hunt_step(prey, rng, rows, cols)
        else:
            self._wander_step(rng, rows, cols)

    def _locked_in_place(self) -> bool:
        if self.exploded:
            return True
        if self.kind == "fire" and (self.fire_active > 0 or self.fire_windup > 0):
            return True
        if self.kind == "exploder" and self.explode_windup > 0:
            return True
        return False

    def _apply(self, dr: int, dc: int, rows: int, cols: int) -> bool:
        nr, nc = self.row + dr, self.col + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            self.row, self.col = nr, nc
            if dr or dc:
                self.heading = (dc, dr)
            return True
        return False

    def _wander_step(self, rng: random.Random, rows: int, cols: int) -> None:
        dc, dr = self.heading
        if rng.random() < 0.22 or not self._apply(dr, dc, rows, cols):
            dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
            rng.shuffle(dirs)
            for ndc, ndr in dirs:
                if self._apply(ndr, ndc, rows, cols):
                    return

    def _chase_step(
        self,
        prey: tuple[int, int],
        rng: random.Random,
        rows: int,
        cols: int,
        wander_chance: float = 0.22,
    ) -> None:
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
        if not options or rng.random() < wander_chance:
            self._wander_step(rng, rows, cols)
            return
        rng.shuffle(options)
        for dr, dc in options:
            if self._apply(dr, dc, rows, cols):
                return
        self._wander_step(rng, rows, cols)

    def _hunt_step(self, prey: tuple[int, int], rng: random.Random, rows: int, cols: int) -> None:
        snacks = [t for t in self._others if t is not self and t.kind != "hunter" and not t.exploded]
        if not snacks:
            if rng.random() < 0.45:
                self._chase_step(prey, rng, rows, cols)
            else:
                self._wander_step(rng, rows, cols)
            return
        nearest = min(snacks, key=lambda t: abs(t.row - self.row) + abs(t.col - self.col))
        if nearest.pos == self.pos:
            return
        self._chase_step(nearest.pos, rng, rows, cols, wander_chance=0.08)


def player_hits_hazard(
    pos: tuple[int, int],
    troggles: list[Troggle],
    rows: int,
    cols: int,
) -> bool:
    """True if the player should lose a life this frame (contact, fire, or boom)."""
    for troggle in troggles:
        if troggle.pos == pos:
            return True
        if troggle.is_firing:
            fr, fc = troggle.front_cell()
            if (fr, fc) == pos and 0 <= fr < rows and 0 <= fc < cols:
                return True
        if troggle.kind == "exploder" and troggle.just_boomed and is_cardinal_adjacent(troggle.pos, pos):
            return True
    return False


def apply_hunter_eats(troggles: list[Troggle]) -> list[Troggle]:
    """Remove Troggles that share a cell with a hunter (hunters are not eaten)."""
    eaten: set[int] = set()
    hunters = [i for i, t in enumerate(troggles) if t.kind == "hunter"]
    for hi in hunters:
        hunter = troggles[hi]
        for i, other in enumerate(troggles):
            if i == hi or i in eaten:
                continue
            if other.kind == "hunter":
                continue
            if other.pos == hunter.pos:
                eaten.add(i)
    return [t for i, t in enumerate(troggles) if i not in eaten]


def troggle_interval_for(level: int, kind: str) -> float:
    """Seconds between steps. Higher = slower. Kid-fair curve for grades 2–5."""
    base = max(TROGGLE_INTERVAL_FLOOR, TROGGLE_INTERVAL_START - (level - 1) * TROGGLE_INTERVAL_STEP)
    return max(TROGGLE_KIND_INTERVAL_MIN, base + _KIND_INTERVAL_BIAS.get(kind, 0.0))


def troggle_kinds_for_level(level: int) -> tuple[str, ...]:
    """Slow introduction: one wanderer first, all five types by level 10."""
    if level <= 2:
        return ("wander",)
    if level <= 4:
        return ("wander", "chase")
    if level == 5:
        return ("wander", "fire")
    if level == 6:
        return ("wander", "chase", "fire")
    if level == 7:
        return ("wander", "fire", "exploder")
    if level == 8:
        return ("chase", "fire", "exploder")
    if level == 9:
        return ("wander", "chase", "fire", "hunter")
    kinds = ["wander", "chase", "fire", "exploder", "hunter"]
    if level >= 13:
        kinds.append("wander")
    return tuple(kinds)


def max_troggles_for(rows: int, cols: int, level: int) -> int:
    """Keep early / small boards sparse so they stay roomy."""
    cells = rows * cols
    if cells <= 16:
        return 1
    if cells <= 24:
        return 2
    if cells <= 36:
        return 3
    return 4 if level < 10 else 5


def _spawn_spots(
    rows: int,
    cols: int,
    player: tuple[int, int],
    rng: random.Random,
) -> list[tuple[int, int]]:
    pr, pc = player
    min_dist = 3 if rows * cols >= 20 else 2
    corners = [(0, 0), (0, cols - 1), (rows - 1, 0), (rows - 1, cols - 1)]
    edges = [
        (0, cols // 2),
        (rows - 1, cols // 2),
        (rows // 2, 0),
        (rows // 2, cols - 1),
    ]
    far = [p for p in corners if abs(p[0] - pr) + abs(p[1] - pc) >= min_dist]
    rng.shuffle(far)
    spots = list(far)
    for extra in edges:
        if extra not in spots and abs(extra[0] - pr) + abs(extra[1] - pc) >= min_dist:
            spots.append(extra)
    if not spots:
        fallback = (0, cols - 1)
        if fallback != player:
            spots = [fallback]
        else:
            spots = [(0, 0)]
    return spots


def _inward_heading(row: int, col: int, rows: int, cols: int) -> tuple[int, int]:
    if col == 0:
        return (1, 0)
    if col == cols - 1:
        return (-1, 0)
    if row == 0:
        return (0, 1)
    if row == rows - 1:
        return (0, -1)
    return (1, 0)


def spawn_troggles(
    level: int,
    player: tuple[int, int],
    rng: random.Random,
    rows: int | None = None,
    cols: int | None = None,
) -> list[Troggle]:
    """Sparse early; types unlock over levels. Never on/next-to the player if possible."""
    if rows is None or cols is None:
        rows, cols = board_size_for_level(level)
    kinds = list(troggle_kinds_for_level(level))
    cap = max_troggles_for(rows, cols, level)
    kinds = kinds[:cap]
    spots = _spawn_spots(rows, cols, player, rng)

    troggles: list[Troggle] = []
    for i, kind in enumerate(kinds):
        row, col = spots[i % len(spots)]
        # If we wrapped spots, nudge unused nearby edges when possible.
        if i >= len(spots):
            for alt in _spawn_spots(rows, cols, player, rng):
                if alt not in {(t.row, t.col) for t in troggles} and alt != player:
                    row, col = alt
                    break
        interval = troggle_interval_for(level, kind)
        t = Troggle(row=row, col=col, kind=kind, interval=interval)
        t.heading = _inward_heading(row, col, rows, cols)
        t.move_timer = 1.15 + i * 0.32
        t.fire_cooldown = 2.4 + i * 0.50
        troggles.append(t)
    return troggles


def safe_player_spawn(
    occupied: set[tuple[int, int]],
    rng: random.Random,
    rows: int = MAX_ROWS,
    cols: int = MAX_COLS,
) -> tuple[int, int]:
    """Prefer a central-ish empty cell on the current board."""
    preferred = [
        (rows // 2, cols // 2),
        (rows // 2, max(0, cols // 2 - 1)),
        (min(rows - 1, rows // 2 + 1), cols // 2),
        (max(0, rows // 2 - 1), cols // 2),
        (max(0, rows - 2), min(cols - 1, 2)),
        (min(rows - 1, 2), min(cols - 1, 2)),
    ]
    seen: set[tuple[int, int]] = set()
    for pos in preferred:
        if pos in seen:
            continue
        seen.add(pos)
        if 0 <= pos[0] < rows and 0 <= pos[1] < cols and pos not in occupied:
            return pos
    candidates = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in occupied]
    return candidates[rng.randrange(len(candidates))] if candidates else (0, 0)
