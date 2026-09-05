import unittest

from omunchy.board import generate_board
from omunchy.entities import spawn_troggles, troggle_kinds_for_level
from omunchy.progress import stable_rng, stable_seed
from omunchy.rules import rule_for


class DeterminismTests(unittest.TestCase):
    def test_seeds_ignore_python_hash_salt(self) -> None:
        self.assertEqual(stable_seed("multiples", 1, "board"), stable_seed("multiples", 1, "board"))
        self.assertNotEqual(stable_seed("multiples", 1), stable_seed("multiples", 2))
        self.assertEqual(stable_rng("x").random(), stable_rng("x").random())

    def test_same_mode_and_level_same_board(self) -> None:
        rule = rule_for("multiples", 1)
        a = generate_board(rule, 1)
        b = generate_board(rule, 1)
        labels_a = [c.label for c in a.all_cells()]
        labels_b = [c.label for c in b.all_cells()]
        self.assertEqual(labels_a, labels_b)
        self.assertEqual((a.rows, a.cols), (4, 5))
        other = generate_board(rule_for("multiples", 3), 3)
        self.assertNotEqual(labels_a, [c.label for c in other.all_cells()])

    def test_rules_and_troggle_mix_are_fixed_per_level(self) -> None:
        self.assertEqual(rule_for("factors", 3), rule_for("factors", 3))
        self.assertEqual(troggle_kinds_for_level(1), ("wander",))
        player = (2, 2)
        a = spawn_troggles(1, player, stable_rng("spawn", "multiples", 1), 4, 5)
        b = spawn_troggles(1, player, stable_rng("spawn", "multiples", 1), 4, 5)
        self.assertEqual([(t.kind, t.row, t.col) for t in a], [(t.kind, t.row, t.col) for t in b])


if __name__ == "__main__":
    unittest.main()
