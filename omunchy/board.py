"""Board generation: fair mix of correct and incorrect cells.

The playfield starts at 4×5 and grows every two levels up to 6×8.
When no RNG is passed, the layout is seeded from (rule.mode, level).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random

from omunchy.constants import MAX_COLS, MAX_ROWS
from omunchy.pairings import addends_of, remaining_complements
from omunchy.progress import stable_rng
from omunchy.rules import Rule, factors_of, is_prime

# (rows, cols) for levels 1–2, 3–4, 5–6, 7–8, then 9+ stays at full size.
BOARD_STEPS: tuple[tuple[int, int], ...] = (
    (4, 5),
    (5, 6),
    (5, 7),
    (6, 7),
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
        if self.rule.mode == "pairings":
            assert self.rule.param is not None
            return remaining_complements(self.all_cells(), self.rule.param)
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
    if rule.mode == "pairings":
        return _pairings_pools(rule)
    raise ValueError(rule.mode)


def _pairings_pools(rule: Rule) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """Bare numbers: practice addends vs decoys that cannot make the target."""
    assert rule.param is not None
    correct = [(str(a), a) for pair in rule.pairs for a in pair]
    decoys = _pairings_decoy_candidates(rule.param, {v for _, v in correct})
    wrong = [(str(n), n) for n in decoys]
    return correct, wrong


def _pairings_decoy_candidates(target: int, addends: set[int]) -> list[int]:
    """Numbers that do not complete the target with a practice addend."""
    if target == 10:
        raw = list(range(11, 25))
    elif target == 100:
        raw = list(range(1, 10)) + list(range(101, 125))
        raw.extend((11, 12, 13, 14, 16, 18, 21, 22, 24, 26, 28, 32, 33, 36, 44, 48, 66, 72, 77, 88, 99))
    else:
        raw = list(range(1, 20)) + list(range(1100, 1120))
        raw.extend((50, 75, 125, 175, 225, 333, 444, 555, 666, 777, 888, 999, 110, 120))
    return [n for n in raw if n not in addends and (target - n) not in addends]


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
    seed_key: str | None = None,
) -> Board:
    rng = rng or stable_rng("board", seed_key or rule.mode, level)
    if rows is None or cols is None:
        rows, cols = board_size_for_level(level)
    if rule.mode == "pairings":
        return _generate_pairings_board(rule, level, rng, rows, cols)
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


def _n_pair_cells(total: int, level: int) -> int:
    """Even count of pair-members: about a third, never empty, never all."""
    n = _n_correct(total, level)
    if n % 2:
        n -= 1
    return max(2, min(n, total - 2 if (total - 2) % 2 == 0 else total - 3))


def _cells_from_picks(picks: list[tuple[str, int]], rows: int, cols: int) -> list[list[Cell]]:
    cells: list[list[Cell]] = []
    i = 0
    for r in range(rows):
        row: list[Cell] = []
        for c in range(cols):
            label, value = picks[i]
            row.append(Cell(r, c, label, value))
            i += 1
        cells.append(row)
    return cells


def _generate_pairings_board(
    rule: Rule,
    level: int,
    rng: random.Random,
    rows: int,
    cols: int,
) -> Board:
    """Place complete complementary pairs plus decoys that cannot make the target."""
    assert rule.param is not None
    assert rule.pairs
    target = rule.param
    total = rows * cols
    n_pair = _n_pair_cells(total, level)
    pairs = list(rule.pairs)
    picks: list[tuple[str, int]] = []
    for _ in range(n_pair // 2):
        a, b = pairs[rng.randrange(len(pairs))]
        picks.append((str(a), a))
        picks.append((str(b), b))

    placed = [v for _, v in picks]
    decoys = _pairings_decoy_candidates(target, set(addends_of(rule.pairs)))
    if not decoys:
        decoys = [target + 1, target + 2, target + 3]
    while len(picks) < total:
        safe = [n for n in decoys if all(n + v != target for v in placed)]
        if not safe:
            n = target + 1
            while n in placed or any(n + v == target for v in placed):
                n += 1
            safe = [n]
        value = safe[rng.randrange(len(safe))]
        picks.append((str(value), value))
        placed.append(value)
    rng.shuffle(picks)
    board = Board(cells=_cells_from_picks(picks, rows, cols), rule=rule)
    if board.remaining_correct() == 0:
        a, b = pairs[0]
        board.cells[0][0] = Cell(0, 0, str(a), a)
        board.cells[0][min(1, cols - 1)] = Cell(0, min(1, cols - 1), str(b), b)
    return board
