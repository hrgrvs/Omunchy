"""Pairings: sum rules, grab/carry/eat, and the complementary-pair win."""

from __future__ import annotations

import os
import unittest

from omunchy.board import Board, Cell, generate_board
from omunchy.constants import MODE_BLURBS, MODE_LABELS, MODES
from omunchy.pairings import (
    LEVELS_MAKE_10,
    LEVELS_MAKE_100,
    WRONG_PAIR_COSTS_LIFE,
    apply_pairings_space,
    pair_sum_correct,
    pairings_spec,
    remaining_complements,
    restore_carry,
)
from omunchy.rules import rule_for


def _tiny_make_ten() -> Board:
    rule = rule_for("pairings", 1)
    cells = [
        [Cell(0, 0, "1", 1), Cell(0, 1, "9", 9), Cell(0, 2, "11", 11)],
        [Cell(1, 0, "2", 2), Cell(1, 1, "8", 8), Cell(1, 2, "12", 12)],
    ]
    return Board(cells=cells, rule=rule)


class PairSumTests(unittest.TestCase):
    def test_sums_to_ten_hundred_thousand(self) -> None:
        self.assertTrue(pair_sum_correct(1, 9, 10))
        self.assertTrue(pair_sum_correct(2, 8, 10))
        self.assertTrue(pair_sum_correct(5, 5, 10))
        self.assertFalse(pair_sum_correct(1, 8, 10))
        self.assertFalse(pair_sum_correct(4, 4, 10))
        self.assertTrue(pair_sum_correct(10, 90, 100))
        self.assertTrue(pair_sum_correct(25, 75, 100))
        self.assertTrue(pair_sum_correct(50, 50, 100))
        self.assertFalse(pair_sum_correct(20, 70, 100))
        self.assertTrue(pair_sum_correct(100, 900, 1000))
        self.assertTrue(pair_sum_correct(400, 600, 1000))
        self.assertTrue(pair_sum_correct(250, 750, 1000))
        self.assertFalse(pair_sum_correct(100, 800, 1000))

    def test_progression_is_ten_then_hundred_then_thousand(self) -> None:
        self.assertEqual(LEVELS_MAKE_10, 6)
        self.assertEqual(LEVELS_MAKE_100, 6)
        self.assertEqual(pairings_spec(1)[0], 10)
        self.assertEqual(pairings_spec(6)[0], 10)
        self.assertEqual(pairings_spec(7)[0], 100)
        self.assertEqual(pairings_spec(12)[0], 100)
        self.assertEqual(pairings_spec(13)[0], 1000)
        self.assertEqual(pairings_spec(20)[0], 1000)
        self.assertEqual(pairings_spec(1), pairings_spec(1))
        self.assertIn((1, 9), pairings_spec(1)[1])
        self.assertIn((10, 90), pairings_spec(7)[1])
        self.assertIn((100, 900), pairings_spec(13)[1])

    def test_wrong_pair_is_kid_fair(self) -> None:
        self.assertFalse(WRONG_PAIR_COSTS_LIFE)


class GrabCarryEatTests(unittest.TestCase):
    def test_grab_then_eat_correct_pair(self) -> None:
        board = _tiny_make_ten()
        grab = apply_pairings_space(board, None, 0, 0)
        self.assertEqual(grab.kind, "grab")
        self.assertIsNotNone(grab.carry)
        assert grab.carry is not None
        self.assertEqual(grab.carry.value, 1)
        self.assertTrue(board.cell(0, 0).munched)
        self.assertEqual(board.remaining_correct(), 2)  # 2+8 still; 9 has no partner yet

        eat = apply_pairings_space(board, grab.carry, 0, 1)
        self.assertEqual(eat.kind, "eat_ok")
        self.assertIsNone(eat.carry)
        self.assertTrue(board.cell(0, 1).munched)
        self.assertEqual(eat.eat_label, "1+9")
        self.assertFalse(eat.pending_clear)
        self.assertEqual(board.remaining_correct(), 2)

    def test_wrong_pair_drops_carried_and_keeps_both_cells(self) -> None:
        board = _tiny_make_ten()
        grab = apply_pairings_space(board, None, 0, 0)
        miss = apply_pairings_space(board, grab.carry, 1, 0)  # 1+2 != 10
        self.assertEqual(miss.kind, "eat_miss")
        self.assertIsNone(miss.carry)
        self.assertFalse(board.cell(0, 0).munched)
        self.assertFalse(board.cell(1, 0).munched)
        self.assertEqual(board.remaining_correct(), 4)

    def test_space_on_empty_drops_carry(self) -> None:
        board = _tiny_make_ten()
        grab = apply_pairings_space(board, None, 0, 0)
        drop = apply_pairings_space(board, grab.carry, 0, 0)
        self.assertEqual(drop.kind, "drop")
        self.assertIsNone(drop.carry)
        self.assertFalse(board.cell(0, 0).munched)

    def test_grab_on_empty_is_noop(self) -> None:
        board = _tiny_make_ten()
        board.cell(0, 2).munched = True
        result = apply_pairings_space(board, None, 0, 2)
        self.assertEqual(result.kind, "noop")
        self.assertIsNone(result.carry)

    def test_troggle_hit_restores_carried_number(self) -> None:
        board = _tiny_make_ten()
        grab = apply_pairings_space(board, None, 0, 0)
        restore_carry(board, grab.carry)
        self.assertFalse(board.cell(0, 0).munched)


class WinConditionTests(unittest.TestCase):
    def test_level_clears_when_complementary_pairs_are_gone(self) -> None:
        board = _tiny_make_ten()
        self.assertEqual(remaining_complements(board.all_cells(), 10), 4)
        first = apply_pairings_space(board, None, 0, 0)
        first = apply_pairings_space(board, first.carry, 0, 1)
        self.assertFalse(first.pending_clear)
        second = apply_pairings_space(board, None, 1, 0)
        second = apply_pairings_space(board, second.carry, 1, 1)
        self.assertEqual(second.kind, "eat_ok")
        self.assertTrue(second.pending_clear)
        self.assertEqual(board.remaining_correct(), 0)
        self.assertFalse(board.cell(0, 2).munched)
        self.assertFalse(board.cell(1, 2).munched)

    def test_decoys_do_not_count_as_remaining_pairs(self) -> None:
        board = _tiny_make_ten()
        for cell in board.all_cells():
            if cell.value in (1, 9, 2, 8):
                cell.munched = True
        self.assertEqual(board.remaining_correct(), 0)


class PairingsBoardTests(unittest.TestCase):
    def test_generated_boards_have_pairs_and_safe_decoys(self) -> None:
        for level in (1, 6, 7, 12, 13):
            rule = rule_for("pairings", level)
            board = generate_board(rule, level)
            target = rule.param
            assert target is not None
            self.assertGreater(board.remaining_correct(), 0, msg=level)
            self.assertLess(board.remaining_correct(), board.rows * board.cols, msg=level)
            self.assertEqual(board.remaining_correct() % 2, 0, msg=level)
            live = [c for c in board.all_cells() if not c.munched]
            for i, a in enumerate(live):
                self.assertEqual(a.label, str(a.value), msg=(level, a.label))
                self.assertNotIn("+", a.label)
                for j, b in enumerate(live):
                    if i >= j:
                        continue
                    if a.value + b.value == target:
                        self.assertTrue(rule.is_correct_pair(a.value, b.value))

    def test_same_level_is_deterministic(self) -> None:
        rule = rule_for("pairings", 1)
        a = [c.label for c in generate_board(rule, 1).all_cells()]
        b = [c.label for c in generate_board(rule, 1).all_cells()]
        self.assertEqual(a, b)
        other = [c.label for c in generate_board(rule_for("pairings", 2), 2).all_cells()]
        self.assertNotEqual(a, other)


class PairingsModeSelectTests(unittest.TestCase):
    def test_pairings_is_on_the_menu_and_mixed_is_not(self) -> None:
        self.assertEqual(MODES, ("multiples", "factors", "primes", "equals", "pairings"))
        self.assertNotIn("mixed", MODES)
        self.assertNotIn("mixed", MODE_LABELS)
        self.assertNotIn("mixed", MODE_BLURBS)
        self.assertEqual(MODE_LABELS["pairings"], "Pairings")
        self.assertIn("10", MODE_BLURBS["pairings"])
        self.assertIn("1000", MODE_BLURBS["pairings"])


class PairingsPlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        try:
            import pygame
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest("pygame is not installed") from exc
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        from omunchy.app import Game, PLAY_ST

        cls.Game = Game
        cls.PLAY_ST = PLAY_ST
        cls.pygame = pygame

    @classmethod
    def tearDownClass(cls) -> None:
        cls.pygame.display.quit()
        cls.pygame.quit()

    def _play(self, level: int = 1):
        game = self.Game()
        game.start_run("pairings")
        game.level = level
        game._begin_level()
        game.state = self.PLAY_ST
        game.player.chomp_timer = 0
        return game

    def _two_complements(self, game):
        assert game.board is not None and game.rule is not None
        target = game.rule.param
        cells = [c for c in game.board.all_cells() if not c.munched]
        for i, a in enumerate(cells):
            for b in cells[i + 1 :]:
                if a.value + b.value == target:
                    return a, b
        self.fail("pairings board had no complementary pair")

    def test_space_grabs_then_eats_a_correct_pair(self) -> None:
        game = self._play()
        first, second = self._two_complements(game)
        game.player.row, game.player.col = first.row, first.col
        game._munch()
        self.assertIsNotNone(game.carried)
        assert game.carried is not None
        self.assertEqual(game.carried.value, first.value)
        self.assertTrue(game.board.cell(first.row, first.col).munched)

        game.player.row, game.player.col = second.row, second.col
        before = game.score
        lives = game.lives
        game._munch()
        self.assertIsNone(game.carried)
        self.assertTrue(game.board.cell(second.row, second.col).munched)
        self.assertGreater(game.score, before)
        self.assertEqual(game.lives, lives)
        self.assertIsNotNone(game.eat_fx)
        assert game.eat_fx is not None
        self.assertTrue(game.eat_fx.correct)
        self.assertIn("+", game.eat_fx.label)

    def test_wrong_pair_drops_carry_without_losing_a_life(self) -> None:
        game = self._play()
        first, partner = self._two_complements(game)
        decoy = next(
            c
            for c in game.board.all_cells()
            if not c.munched and c.value + first.value != game.rule.param and (c.row, c.col) != (partner.row, partner.col)
        )
        game.player.row, game.player.col = first.row, first.col
        game._munch()
        game.player.row, game.player.col = decoy.row, decoy.col
        lives = game.lives
        game._munch()
        self.assertIsNone(game.carried)
        self.assertFalse(game.board.cell(first.row, first.col).munched)
        self.assertFalse(game.board.cell(decoy.row, decoy.col).munched)
        self.assertEqual(game.lives, lives)
        self.assertIsNotNone(game.eat_fx)
        assert game.eat_fx is not None
        self.assertFalse(game.eat_fx.correct)
        self.assertFalse(game.eat_fx.pending_life)

    def test_carried_digit_is_drawn_beside_the_muncher(self) -> None:
        from omunchy.constants import GOLD, WHITE, WINDOW_H, WINDOW_W, grid_geometry
        from omunchy.sprites import cell_rect

        game = self._play()
        first, _second = self._two_complements(game)
        game.player.row, game.player.col = first.row, first.col
        game._munch()
        game._draw()
        self.assertEqual(game.screen.get_size(), (WINDOW_W, WINDOW_H))
        left, top, _w, _h = grid_geometry(game.board.rows, game.board.cols)
        pref = cell_rect(game.player.row, game.player.col, left, top)
        # Badge sits above / beside the sprite, not in the mouth hole.
        found_white = 0
        found_gold = 0
        for x in range(max(0, pref.left - 20), min(WINDOW_W, pref.right + 30)):
            for y in range(max(0, pref.top - 16), pref.centery):
                rgb = game.screen.get_at((x, y))[:3]
                if rgb == WHITE:
                    found_white += 1
                if rgb == GOLD:
                    found_gold += 1
        self.assertGreater(found_white, 4, msg=game.carried)
        self.assertGreater(found_gold, 0, msg="carry badge outline")


if __name__ == "__main__":
    unittest.main()
