"""Age-appropriate rules for grades 2–5. Progression ramps slowly."""

from __future__ import annotations

from dataclasses import dataclass
import math

from omunchy.pairings import addends_of, pair_sum_correct, pairings_spec

SMALL_PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29)


def _multiples_max_n(factor: int) -> int:
    """Grade 2–5 product ceiling for a Multiples-of-n board (capped at 60)."""
    if factor <= 5:
        span = 10
    elif factor <= 10:
        span = 6
    elif factor <= 15:
        span = 4
    else:
        span = 3
    return min(60, factor * span)


# Multiples of 2, then 3, … through 20. Same (mode, level) every playthrough.
MULTIPLES_STEPS = tuple((n, _multiples_max_n(n)) for n in range(2, 21))

FACTORS_STEPS = (8, 10, 12, 12, 16, 18, 20, 24, 24, 30, 36)

EQUALS_STEPS = (10, 10, 12, 12, 15, 16, 18, 20)

PRIME_MAX_STEPS = (20, 20, 23, 29, 29)


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n in SMALL_PRIMES:
        return True
    if n % 2 == 0:
        return False
    limit = int(math.sqrt(n)) + 1
    for d in range(3, limit, 2):
        if n % d == 0:
            return False
    return n <= 29 and n in SMALL_PRIMES


def factors_of(n: int) -> tuple[int, ...]:
    found = []
    for d in range(1, n + 1):
        if n % d == 0:
            found.append(d)
    return tuple(found)


@dataclass(frozen=True)
class Rule:
    mode: str
    title: str
    param: int | None = None
    max_n: int | None = None
    pairs: tuple[tuple[int, int], ...] = ()

    def is_correct(self, value: int) -> bool:
        if self.mode == "multiples":
            return self.param is not None and value > 0 and value % self.param == 0
        if self.mode == "factors":
            return self.param is not None and value > 0 and self.param % value == 0
        if self.mode == "primes":
            return is_prime(value)
        if self.mode == "equals":
            return self.param is not None and value == self.param
        if self.mode == "pairings":
            return self.is_pair_member(value)
        return False

    def is_pair_member(self, value: int) -> bool:
        return self.mode == "pairings" and value in addends_of(self.pairs)

    def is_correct_pair(self, a: int, b: int) -> bool:
        return self.mode == "pairings" and self.param is not None and pair_sum_correct(a, b, self.param)


def rule_for(selected_mode: str, level: int) -> Rule:
    """Build a rule for a 1-based level."""
    mode = selected_mode
    idx = level - 1
    if mode == "multiples":
        factor, max_n = MULTIPLES_STEPS[min(idx, len(MULTIPLES_STEPS) - 1)]
        if idx >= len(MULTIPLES_STEPS):
            factor, max_n = MULTIPLES_STEPS[idx % len(MULTIPLES_STEPS)]
            max_n = min(60, max_n + 6)
        return Rule("multiples", f"Multiples of {factor}", param=factor, max_n=max_n)
    if mode == "factors":
        n = FACTORS_STEPS[min(idx, len(FACTORS_STEPS) - 1)]
        if idx >= len(FACTORS_STEPS):
            n = FACTORS_STEPS[-1]
        return Rule("factors", f"Factors of {n}", param=n, max_n=n + 8)
    if mode == "primes":
        max_n = PRIME_MAX_STEPS[min(idx, len(PRIME_MAX_STEPS) - 1)]
        if idx >= len(PRIME_MAX_STEPS):
            max_n = 29
        return Rule("primes", "Prime numbers", param=None, max_n=max_n)
    if mode == "equals":
        target = EQUALS_STEPS[min(idx, len(EQUALS_STEPS) - 1)]
        if idx >= len(EQUALS_STEPS):
            target = EQUALS_STEPS[-1]
        return Rule("equals", f"Equals {target}", param=target, max_n=target + 12)
    if mode == "pairings":
        target, pairs = pairings_spec(level)
        max_n = max(max(pair) for pair in pairs)
        return Rule(
            "pairings",
            f"Make {target}",
            param=target,
            max_n=max_n,
            pairs=pairs,
        )
    raise ValueError(f"Unknown mode: {mode}")