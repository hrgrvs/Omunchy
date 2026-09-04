import unittest

from omunch.rules import factors_of, is_prime, resolve_play_mode, rule_for


class PrimeTests(unittest.TestCase):
    def test_small_primes(self) -> None:
        for n in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29):
            self.assertTrue(is_prime(n), n)

    def test_composites_and_one(self) -> None:
        for n in (1, 4, 6, 8, 9, 15, 21, 25, 27):
            self.assertFalse(is_prime(n), n)


class RuleTests(unittest.TestCase):
    def test_multiples_level_one_is_twos(self) -> None:
        rule = rule_for("multiples", 1)
        self.assertEqual(rule.title, "Multiples of 2")
        self.assertTrue(rule.is_correct(2))
        self.assertTrue(rule.is_correct(18))
        self.assertFalse(rule.is_correct(9))
        self.assertFalse(rule.is_correct(0))

    def test_factors_of_twelve(self) -> None:
        rule = rule_for("factors", 3)
        self.assertEqual(rule.param, 12)
        self.assertTrue(rule.is_correct(1))
        self.assertTrue(rule.is_correct(6))
        self.assertTrue(rule.is_correct(12))
        self.assertFalse(rule.is_correct(5))
        self.assertEqual(factors_of(12), (1, 2, 3, 4, 6, 12))

    def test_primes_rule(self) -> None:
        rule = rule_for("primes", 1)
        self.assertEqual(rule.title, "Prime numbers")
        self.assertTrue(rule.is_correct(7))
        self.assertFalse(rule.is_correct(1))
        self.assertFalse(rule.is_correct(9))

    def test_equals_ten(self) -> None:
        rule = rule_for("equals", 1)
        self.assertEqual(rule.title, "Equals 10")
        self.assertTrue(rule.is_correct(10))
        self.assertFalse(rule.is_correct(9))

    def test_mixed_cycles_modes(self) -> None:
        self.assertEqual(resolve_play_mode("mixed", 1), "multiples")
        self.assertEqual(resolve_play_mode("mixed", 2), "factors")
        self.assertEqual(resolve_play_mode("mixed", 3), "primes")
        self.assertEqual(resolve_play_mode("mixed", 4), "equals")
        self.assertEqual(resolve_play_mode("mixed", 5), "multiples")

    def test_progression_stays_grade_band(self) -> None:
        for level in range(1, 16):
            multiples = rule_for("multiples", level)
            self.assertIn(multiples.param, (2, 3, 4, 5, 6, 10))
            self.assertLessEqual(multiples.max_n or 0, 60)
            factors = rule_for("factors", level)
            self.assertLessEqual(factors.param or 0, 36)
            primes = rule_for("primes", level)
            self.assertLessEqual(primes.max_n or 0, 29)
            equals = rule_for("equals", level)
            self.assertLessEqual(equals.param or 0, 20)


if __name__ == "__main__":
    unittest.main()