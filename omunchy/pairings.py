"""Pairings mode: grab one number, carry it, eat it with a partner.

Kid-fair miss: a wrong pair *drops* the carried number back onto its cell.
Lives are not spent on a math miss — only Troggles (and other modes' wrong
munches) cost a life.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Practice families, in teaching order.
PAIRS_10: tuple[tuple[int, int], ...] = (
    (1, 9),
    (2, 8),
    (3, 7),
    (4, 6),
    (5, 5),
)
PAIRS_100: tuple[tuple[int, int], ...] = (
    (10, 90),
    (20, 80),
    (30, 70),
    (40, 60),
    (50, 50),
    (15, 85),
    (25, 75),
    (35, 65),
    (45, 55),
)
PAIRS_1000: tuple[tuple[int, int], ...] = (
    (100, 900),
    (200, 800),
    (300, 700),
    (400, 600),
    (500, 500),
    (150, 850),
    (250, 750),
    (350, 650),
    (450, 550),
)

# Sequential bands. Same (mode, level) every playthrough.
LEVELS_MAKE_10 = 6
LEVELS_MAKE_100 = 6

# Documented product choice: wrong pair does not cost a life.
WRONG_PAIR_COSTS_LIFE = False


def pair_sum_correct(a: int, b: int, target: int) -> bool:
    """True when the two numbers make the level target."""
    return a + b == target


def pairings_spec(level: int) -> tuple[int, tuple[tuple[int, int], ...]]:
    """Return (target, practice pairs) for a 1-based Pairings level."""
    idx = max(0, level - 1)
    if idx < LEVELS_MAKE_10:
        # 3 pairs, then 4, then all five ten-pairs.
        n = min(len(PAIRS_10), 3 + idx // 2)
        return 10, PAIRS_10[:n]
    if idx < LEVELS_MAKE_10 + LEVELS_MAKE_100:
        sub = idx - LEVELS_MAKE_10
        n = min(len(PAIRS_100), 4 + sub)
        return 100, PAIRS_100[:n]
    sub = idx - LEVELS_MAKE_10 - LEVELS_MAKE_100
    n = min(len(PAIRS_1000), 4 + sub)
    return 1000, PAIRS_1000[:n]


def addends_of(pairs: tuple[tuple[int, int], ...]) -> frozenset[int]:
    found: set[int] = set()
    for a, b in pairs:
        found.add(a)
        found.add(b)
    return frozenset(found)


def remaining_complements(cells: list[Any], target: int) -> int:
    """Unmunched cells that still have a partner summing to target."""
    live = [c for c in cells if not c.munched]
    n = 0
    for i, cell in enumerate(live):
        if any(i != j and pair_sum_correct(cell.value, other.value, target) for j, other in enumerate(live)):
            n += 1
    return n


@dataclass(frozen=True)
class Carry:
    """Number the muncher is holding after a grab."""

    value: int
    label: str
    row: int
    col: int


@dataclass(frozen=True)
class PairSpaceResult:
    """Outcome of Space in Pairings (grab, drop, eat, or no-op)."""

    kind: str
    carry: Carry | None
    eat_label: str = ""
    eat_row: int = 0
    eat_col: int = 0
    pending_clear: bool = False


def restore_carry(board: Any, carry: Carry | None) -> None:
    """Put a dropped / interrupted grab back on its cell."""
    if carry is None:
        return
    if board.in_bounds(carry.row, carry.col):
        board.cell(carry.row, carry.col).munched = False


def apply_pairings_space(board: Any, carry: Carry | None, row: int, col: int) -> PairSpaceResult:
    """Resolve Space on (row, col). Mutates the board; returns the new carry."""
    assert board.rule is not None
    target = board.rule.param
    assert target is not None
    if not board.in_bounds(row, col):
        return PairSpaceResult("noop", carry)

    cell = board.cell(row, col)

    if carry is None:
        if cell.munched:
            return PairSpaceResult("noop", None)
        cell.munched = True
        return PairSpaceResult("grab", Carry(cell.value, cell.label, row, col))

    # Space on the empty plate you grabbed from (or any empty cell): drop.
    if cell.munched:
        restore_carry(board, carry)
        return PairSpaceResult("drop", None)

    eat_label = f"{carry.label}+{cell.label}"
    if pair_sum_correct(carry.value, cell.value, target):
        cell.munched = True
        pending_clear = remaining_complements(board.all_cells(), target) == 0
        return PairSpaceResult(
            "eat_ok",
            None,
            eat_label=eat_label,
            eat_row=row,
            eat_col=col,
            pending_clear=pending_clear,
        )

    restore_carry(board, carry)
    return PairSpaceResult(
        "eat_miss",
        None,
        eat_label=eat_label,
        eat_row=row,
        eat_col=col,
    )
