"""Board generation: fair mix of correct and incorrect cells.

The playfield starts small (3×4) and grows every two levels up to 6×8.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random

from omunch.constants import MAX_COLS, MAX_ROWS
from omunch.rules import Rule, factors_of, is_prime

# (rows, cols) for levels 1–2, 3–4, 5–6, 7–8, then 9+ stays at full size.
BOARD_STEPS: tuple[tuple[int, int], ...] = (
    (3, 4),
    (4, 5),
    (5, 6),
    (5, 7),
    (MAX_ROWS, MAX_COLS),
)


def board_size_for_level(level: int) -> tuple[int, int]:
    """Return (rows, cols) for a 1-based level. Grows toward MAX_ROWS × MAX_COLS."""
    idx = max(0, (max(1, level) - 1) // 2)
    if idx >= len(BOARD_STEPS):
        return BOARD_STEPS[-1]
    return BOARD_STEPS[idx]


@dataclass
class Cell:
    row: int
    col: int
    label: str
    value: int
    munched: bool = False


@dataclass
class Board:
    cells: list[list[Cell]] = field(default_factory=list)
    rule: Rule | None = None

    @property
    def rows(self) -> int:
        return len(self.cells)

    @property
    def cols(self) -> int:
        return len(self.cells[0]) if self.cells else 0

    def cell(self, row: int, col: int) -> Cell:
        return self.cells[row][col]

    def all_cells(self) -> list[Cell]:
        return [c for row in self.cells for c in row]

    def remaining_correct(self) -> int:
        assert self.rule is not None
        return sum(1 for c in self.all_cells() if not c.munched and self.rule.is_correct(c.value))

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols


def _additions_for(target: int) -> list[tuple[str, int]]:
    items = []
    for a in range(0, target + 1):
        b = target - a
        if 0 <= b <= 20:
            items.append((f"{a}+{b}", target))
    return items


def _subtractions_for(target: int) -> list[tuple[str, int]]:
    items = []
    for a in range(target, min(target + 16, 36) + 1):
        b = a - target
        if 1 <= b <= 20:
            items.append((f"{a}−{b}", target))
    return items


def _products_for(target: int) -> list[tuple[str, int]]:
    items = []
    for a in range(2, 11):
        if target % a == 0:
            b = target // a
            if 2 <= b <= 12:
                items.append((f"{a}×{b}", target))
    return items


def _equals_pool(target: int, want_correct: bool, level: int) -> list[tuple[str, int]]:
    if want_correct:
        pool = _additions_for(target)
        if level >= 2:
            pool.extend(_subtractions_for(target))
        if level >= 4:
            pool.extend(_products_for(target))
        # Always include the bare target so early boards stay readable.
        pool.append((str(target), target))
        return pool or [(str(target), target)]

    wrong: list[tuple[str, int]] = []
    nearby = [n for n in range(max(1, target - 8), target + 10) if n != target]
    for n in nearby:
        wrong.extend(_additions_for(n)[:6])
        if level >= 2:
            wrong.extend(_subtractions_for(n)[:4])
        if level >= 4:
            wrong.extend(_products_for(n))
        wrong.append((str(n), n))
    return wrong or [(str(target + 1), target + 1)]


def _multiples_pool(factor: int, max_n: int, want_correct: bool) -> list[tuple[str, int]]:
    if want_correct:
        return [(str(n), n) for n in range(factor, max_n + 1, factor)]
    return [(str(n), n) for n in range(1, max_n + 1) if n % factor != 0]


def _factors_pool(n: int, want_correct: bool) -> list[tuple[str, int]]:
    good = factors_of(n)
    if want_correct:
        return [(str(v), v) for v in good]
    wrong_vals = [v for v in range(1, n + 10) if v not in good]
    return [(str(v), v) for v in wrong_vals]


def _primes_pool(max_n: int, want_correct: bool) -> list[tuple[str, int]]:
    if want_correct:
        return [(str(n), n) for n in range(2, max_n + 1) if is_prime(n)]
    return [(str(n), n) for n in range(1, max_n + 1) if not is_prime(n)]


def item_pools(rule: Rule, level: int) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    max_n = rule.max_n or 30
    if rule.mode == "multiples":
        assert rule.param is not None
        return _multiples_pool(rule.param, max_n, True), _multiples_pool(rule.param, max_n, False)
    if rule.mode == "factors":
        assert rule.param is not None
        return _factors_pool(rule.param, True), _factors_pool(rule.param, False)
    if rule.mode == "primes":
        return _primes_pool(max_n, True), _primes_pool(max_n, False)
    if rule.mode == "equals":
        assert rule.param is not None
        return _equals_pool(rule.param, True, level), _equals_pool(rule.param, False, level)
    raise ValueError(rule.mode)


def _n_correct(total: int, level: int) -> int:
    """About one third correct; never empty, never all, never more than half."""
    target = max(3, (total + 2) // 3)
    bump = min(total // 8, (level - 1) // 3)
    return max(2, min(target + bump, total // 2, total - 2))


def generate_board(
    rule: Rule,
    level: int,
    rng: random.Random | None = None,
    rows: int | None = None,
    cols: int | None = None,
) -> Board:
    rng = rng or random.Random()
    if rows is None or cols is None:
        rows, cols = board_size_for_level(level)
    correct_pool, wrong_pool = item_pools(rule, level)
    if not correct_pool:
        raise RuntimeError(f"No correct answers for {rule}")
    if not wrong_pool:
        raise RuntimeError(f"No wrong answers for {rule}")

    total = rows * cols
    n_correct = _n_correct(total, level)

    picks: list[tuple[str, int]] = [
        correct_pool[rng.randrange(len(correct_pool))] for _ in range(n_correct)
    ]
    while len(picks) < total:
        picks.append(wrong_pool[rng.randrange(len(wrong_pool))])
    rng.shuffle(picks)

    cells: list[list[Cell]] = []
    i = 0
    for r in range(rows):
        row: list[Cell] = []
        for c in range(cols):
            label, value = picks[i]
            row.append(Cell(r, c, label, value))
            i += 1
        cells.append(row)

    board = Board(cells=cells, rule=rule)
    # Guarantee the mix after shuffle (paranoia if pools were tiny).
    if board.remaining_correct() == 0:
        label, value = correct_pool[0]
        cells[0][0] = Cell(0, 0, label, value)
    if board.remaining_correct() == total:
        label, value = wrong_pool[0]
        cells[0][min(1, cols - 1)] = Cell(0, min(1, cols - 1), label, value)
    return board
