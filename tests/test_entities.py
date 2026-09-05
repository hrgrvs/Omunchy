import random
import unittest

from omunch.constants import EXPLODE_WINDUP, FIRE_DURATION, FIRE_WINDUP
from omunch.entities import (
    Muncher,
    Troggle,
    apply_hunter_eats,
    front_cell,
    is_cardinal_adjacent,
    player_hits_hazard,
    troggle_kinds_for_level,
)


class BoundsTests(unittest.TestCase):
    def test_muncher_stays_on_small_board(self) -> None:
        muncher = Muncher(row=0, col=0)
        self.assertFalse(muncher.try_step(-1, 0, 3, 4))
        self.assertFalse(muncher.try_step(0, -1, 3, 4))
        self.assertTrue(muncher.try_step(1, 0, 3, 4))
        self.assertEqual(muncher.pos, (1, 0))
        muncher.row, muncher.col = 2, 3
        self.assertFalse(muncher.try_step(1, 0, 3, 4))
        self.assertFalse(muncher.try_step(0, 1, 3, 4))

    def test_troggle_wander_respects_bounds(self) -> None:
        rng = random.Random(0)
        t = Troggle(row=0, col=0, kind="wander", heading=(-1, 0), interval=0.01)
        t.move_timer = 0
        t.tick_and_maybe_move(0.02, (2, 2), rng, 3, 4)
        self.assertTrue(0 <= t.row < 3 and 0 <= t.col < 4)


class FireTests(unittest.TestCase):
    def test_front_cell_is_the_single_square_ahead(self) -> None:
        self.assertEqual(front_cell(2, 2, (1, 0)), (2, 3))  # right
        self.assertEqual(front_cell(2, 2, (-1, 0)), (2, 1))  # left
        self.assertEqual(front_cell(2, 2, (0, 1)), (3, 2))  # down
        self.assertEqual(front_cell(2, 2, (0, -1)), (1, 2))  # up
        t = Troggle(row=1, col=1, kind="fire", heading=(1, 0))
        self.assertEqual(t.front_cell(), (1, 2))

    def test_fire_activates_after_windup_on_front_cell(self) -> None:
        t = Troggle(row=1, col=1, kind="fire", heading=(1, 0))
        t.fire_cooldown = 0
        t.fire_windup = 0
        t.fire_active = 0
        t.tick_specials(0.0, (0, 0), 6, 8)
        self.assertGreater(t.fire_windup, 0)
        self.assertFalse(t.is_firing)
        t.fire_windup = 0.001
        t.tick_specials(0.02, (0, 0), 6, 8)
        self.assertTrue(t.is_firing)
        self.assertAlmostEqual(t.fire_active, FIRE_DURATION)
        self.assertTrue(player_hits_hazard((1, 2), [t], 6, 8))
        self.assertFalse(player_hits_hazard((1, 3), [t], 6, 8))
        self.assertFalse(player_hits_hazard((0, 1), [t], 6, 8))

    def test_fire_skipped_when_front_is_off_board(self) -> None:
        t = Troggle(row=0, col=0, kind="fire", heading=(-1, 0))
        t.fire_cooldown = 0
        t.fire_windup = FIRE_WINDUP
        t.tick_specials(FIRE_WINDUP + 0.01, (2, 2), 3, 4)
        self.assertFalse(t.is_firing)
        self.assertGreater(t.fire_cooldown, 0)

    def test_player_on_fire_body_still_takes_contact_damage(self) -> None:
        t = Troggle(row=2, col=2, kind="fire", heading=(1, 0))
        self.assertTrue(player_hits_hazard((2, 2), [t], 6, 8))


class ExploderTests(unittest.TestCase):
    def test_cardinal_adjacency_is_the_kid_fair_rule(self) -> None:
        self.assertTrue(is_cardinal_adjacent((2, 2), (2, 3)))
        self.assertTrue(is_cardinal_adjacent((2, 2), (1, 2)))
        self.assertFalse(is_cardinal_adjacent((2, 2), (3, 3)))
        self.assertFalse(is_cardinal_adjacent((2, 2), (2, 2)))

    def test_telegraph_then_boom_if_still_adjacent(self) -> None:
        t = Troggle(row=2, col=2, kind="exploder")
        t.tick_specials(0.01, (2, 3), 6, 8)
        self.assertGreater(t.explode_windup, 0)
        self.assertFalse(t.just_boomed)
        self.assertAlmostEqual(t.explode_windup, EXPLODE_WINDUP)
        t.explode_windup = 0.001
        t.tick_specials(0.02, (2, 3), 6, 8)
        self.assertTrue(t.just_boomed)
        self.assertTrue(t.exploded)
        self.assertTrue(player_hits_hazard((2, 3), [t], 6, 8))
        # Diagonal remains safe even at boom time.
        t.just_boomed = True
        self.assertFalse(player_hits_hazard((3, 3), [t], 6, 8))

    def test_no_boom_when_player_stays_diagonal(self) -> None:
        t = Troggle(row=2, col=2, kind="exploder")
        t.tick_specials(0.5, (3, 3), 6, 8)
        self.assertEqual(t.explode_windup, 0)
        self.assertFalse(t.exploded)


class HunterTests(unittest.TestCase):
    def test_hunter_eats_other_troggle_on_same_cell(self) -> None:
        hunter = Troggle(row=1, col=1, kind="hunter")
        wander = Troggle(row=1, col=1, kind="wander")
        left = apply_hunter_eats([hunter, wander])
        self.assertEqual(len(left), 1)
        self.assertEqual(left[0].kind, "hunter")

    def test_hunter_does_not_eat_itself_or_another_hunter(self) -> None:
        a = Troggle(row=2, col=2, kind="hunter")
        b = Troggle(row=2, col=2, kind="hunter")
        left = apply_hunter_eats([a, b])
        self.assertEqual(len(left), 2)

    def test_player_contact_with_hunter_is_a_hazard(self) -> None:
        hunter = Troggle(row=3, col=3, kind="hunter")
        self.assertTrue(player_hits_hazard((3, 3), [hunter], 6, 8))
        self.assertFalse(player_hits_hazard((3, 4), [hunter], 6, 8))

    def test_hunter_steps_toward_prey_troggle(self) -> None:
        hunter = Troggle(row=0, col=0, kind="hunter", interval=0.01)
        snack = Troggle(row=0, col=2, kind="wander")
        hunter.move_timer = 0
        hunter.update(0.02, (5, 5), random.Random(1), 6, 8, (hunter, snack))
        self.assertEqual(hunter.pos, (0, 1))


class RosterTests(unittest.TestCase):
    def test_kinds_unlock_in_order(self) -> None:
        self.assertEqual(troggle_kinds_for_level(1), ("wander",))
        self.assertIn("chase", troggle_kinds_for_level(3))
        self.assertIn("fire", troggle_kinds_for_level(5))
        self.assertIn("exploder", troggle_kinds_for_level(7))
        self.assertIn("hunter", troggle_kinds_for_level(9))


if __name__ == "__main__":
    unittest.main()
