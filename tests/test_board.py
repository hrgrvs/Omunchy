import random
import unittest

from omunch.board import generate_board
from omunch.constants import COLS, ROWS
from omunch.entities import safe_player_spawn, spawn_troggles
from omunch.rules import rule_for


class BoardTests(unittest.TestCase):
    def test_all_modes_have_a_fair_mix(self) -> None:
        rng = random.Random(42)
        total = ROWS * COLS
        for mode in ("multiples", "factors", "primes", "equals", "mixed"):
            for level in range(1, 10):
                rule = rule_for(mode, level)
                board = generate_board(rule, level, rng)
                correct = board.remaining_correct()
                self.assertGreater(correct, 0, msg=(mode, level, rule.title))
                self.assertLess(correct, total, msg=(mode, level, rule.title))
                self.assertLessEqual(correct, total // 2 + 2, msg=(mode, level))

    def test_munching_correct_clears_toward_advance(self) -> None:
        board = generate_board(rule_for("multiples", 1), 1, random.Random(1))
        remaining = board.remaining_correct()
        for cell in board.all_cells():
            if board.rule and board.rule.is_correct(cell.value):
                cell.munched = True
        self.assertEqual(board.remaining_correct(), 0)
        self.assertGreater(remaining, 0)


class SpawnTests(unittest.TestCase):
    def test_player_not_on_troggle(self) -> None:
        rng = random.Random(7)
        for level in range(1, 8):
            player = safe_player_spawn(set(), rng)
            troggles = spawn_troggles(level, player, rng)
            spots = {(t.row, t.col) for t in troggles}
            self.assertNotIn(player, spots)
            kinds = {t.kind for t in troggles}
            self.assertIn("wander", kinds)
            if level >= 3 and len(troggles) >= 2:
                self.assertTrue("chase" in kinds or len(troggles) >= 1)


if __name__ == "__main__":
    unittest.main()