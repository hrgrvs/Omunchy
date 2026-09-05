"""Stable per-(mode, level) randomness so a run plays the same way each time."""

from __future__ import annotations

import hashlib
import random


def stable_seed(*parts: object) -> int:
    """Integer seed that does not depend on PYTHONHASHSEED."""
    blob = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(blob).digest()[:8], "big")


def stable_rng(*parts: object) -> random.Random:
    """Return a Random seeded from the given parts (mode, level, stream name, …)."""
    return random.Random(stable_seed(*parts))
