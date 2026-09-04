"""Board generation: fair mix of correct and incorrect cells."""

from __future__ import annotations

from dataclasses import dataclass, field
import random

from omunch.constants import COLS, ROWS
from omunch.rules import Rule, factors_of, is_prime


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

    def cell(self, row: int, col: int) -> Cell:
        return self.cells[row][col]

    def all_cells(self) -> list[Cell]:
        return [c for row in self.cells for c in row]

    def remaining_correct(self) -> int:
        assert self.rule is not None
        return sum(1 for c in self.all_cells() if not c.munched and self.rule.is_correct(c.value))

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < ROWS and 0 <= col < COLS


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


def generate_board(rule: Rule, level: int, rng: random.Random | None = None) -> Board:
    rng = rng or random.Random()
    correct_pool, wrong_pool = item_pools(rule, level)
    if not correct_pool:
        raise RuntimeError(f"No correct answers for {rule}")
    if not wrong_pool:
        raise RuntimeError(f"No wrong answers for {rule}")

    total = ROWS * COLS
    # About a third of the board is correct — never a full-correct board.
    n_correct = 8 + min(6, (level - 1) // 2)
    n_correct = max(6, min(n_correct, total // 2, total - 8))

    picks: list[tuple[str, int]] = [
        correct_pool[rng.randrange(len(correct_pool))] for _ in range(n_correct)
    ]
    while len(picks) < total:
        picks.append(wrong_pool[rng.randrange(len(wrong_pool))])
    rng.shuffle(picks)

    cells: list[list[Cell]] = []
    i = 0
    for r in range(ROWS):
        row: list[Cell] = []
        for c in range(COLS):
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
        cells[0][1] = Cell(0, 1, label, value)
    return board