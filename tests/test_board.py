import random
import unittest

from omunchy.board import BOARD_STEPS, board_size_for_level, generate_board
from omunchy.constants import (
    CELL_H,
    CELL_W,
    MAX_COLS,
    MAX_ROWS,
    TITLE,
    WINDOW_H,
    WINDOW_W,
    grid_geometry,
)
from omunchy.entities import safe_player_spawn, spawn_troggles, troggle_kinds_for_level
from omunchy.rules import rule_for


class BoardSizeTests(unittest.TestCase):
    def test_level_one_is_visibly_smaller_than_max(self) -> None:
        rows, cols = board_size_for_level(1)
        self.assertEqual((rows, cols), (3, 4))
        self.assertLess(rows * cols, MAX_ROWS * MAX_COLS)

    def test_grows_every_two_levels_to_full_size(self) -> None:
        self.assertEqual(board_size_for_level(1), (3, 4))
        self.assertEqual(board_size_for_level(2), (3, 4))
        self.assertEqual(board_size_for_level(3), (4, 5))
        self.assertEqual(board_size_for_level(5), (5, 6))
        self.assertEqual(board_size_for_level(7), (5, 7))
        self.assertEqual(board_size_for_level(9), (MAX_ROWS, MAX_COLS))
        self.assertEqual(board_size_for_level(20), (MAX_ROWS, MAX_COLS))
        self.assertEqual(BOARD_STEPS[-1], (MAX_ROWS, MAX_COLS))

    def test_generated_board_uses_current_size(self) -> None:
        rng = random.Random(3)
        for level in (1, 3, 5, 7, 9, 12):
            rows, cols = board_size_for_level(level)
            board = generate_board(rule_for("multiples", level), level, rng)
            self.assertEqual(board.rows, rows)
            self.assertEqual(board.cols, cols)
            self.assertTrue(board.in_bounds(0, 0))
            self.assertTrue(board.in_bounds(rows - 1, cols - 1))
            self.assertFalse(board.in_bounds(rows, 0))
            self.assertFalse(board.in_bounds(0, cols))

    def test_grid_layout_uses_current_size(self) -> None:
        left, top, width, height = grid_geometry(3, 4)
        self.assertEqual(width, 4 * CELL_W)
        self.assertEqual(height, 3 * CELL_H)
        self.assertEqual(left, (WINDOW_W - width) // 2)
        full_left, _full_top, full_w, full_h = grid_geometry(MAX_ROWS, MAX_COLS)
        self.assertLess(width * height, full_w * full_h)
        self.assertGreater(left, full_left)

    def test_logical_frame_is_widescreen(self) -> None:
        self.assertEqual((WINDOW_W, WINDOW_H), (1280, 720))
        self.assertAlmostEqual(WINDOW_W / WINDOW_H, 16 / 9)
        self.assertEqual(TITLE, "Omunchy")


class BoardTests(unittest.TestCase):
    def test_all_modes_have_a_fair_mix(self) -> None:
        rng = random.Random(42)
        for mode in ("multiples", "factors", "primes", "equals", "mixed"):
            for level in range(1, 10):
                rule = rule_for(mode, level)
                board = generate_board(rule, level, rng)
                total = board.rows * board.cols
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
        for level in range(1, 14):
            rows, cols = board_size_for_level(level)
            player = safe_player_spawn(set(), rng, rows, cols)
            self.assertTrue(0 <= player[0] < rows)
            self.assertTrue(0 <= player[1] < cols)
            troggles = spawn_troggles(level, player, rng, rows, cols)
            spots = {(t.row, t.col) for t in troggles}
            self.assertNotIn(player, spots)
            for t in troggles:
                self.assertTrue(0 <= t.row < rows and 0 <= t.col < cols)

    def test_early_levels_are_sparse(self) -> None:
        rng = random.Random(11)
        player = (1, 1)
        one = spawn_troggles(1, player, rng, 3, 4)
        self.assertEqual(len(one), 1)
        self.assertEqual(one[0].kind, "wander")
        two = spawn_troggles(2, player, rng, 3, 4)
        self.assertEqual(len(two), 1)
        self.assertEqual(set(troggle_kinds_for_level(3)), {"wander", "chase"})

    def test_all_five_types_appear_by_mid_game(self) -> None:
        seen: set[str] = set()
        rng = random.Random(19)
        for level in range(1, 11):
            rows, cols = board_size_for_level(level)
            player = safe_player_spawn(set(), rng, rows, cols)
            for t in spawn_troggles(level, player, rng, rows, cols):
                seen.add(t.kind)
        self.assertEqual(seen, {"wander", "chase", "fire", "exploder", "hunter"})
        self.assertIn("hunter", troggle_kinds_for_level(9))
        self.assertEqual(
            set(troggle_kinds_for_level(10)),
            {"wander", "chase", "fire", "exploder", "hunter"},
        )


if __name__ == "__main__":
    unittest.main()
