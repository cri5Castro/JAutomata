"""Independent small-oracle tests for Thompson construction."""

import unittest

from jautomata import RegexSyntaxError, compile_regex
from jautomata.model import Automaton


def accepts(automaton: Automaton, text: str) -> bool:
    """Small test-only NFA oracle; production recognition belongs to T-004."""
    current = epsilon_closure(automaton, {automaton.start_state})
    for character in text:
        moved = {
            edge.target
            for state in current
            for edge in automaton.transitions_from(state)
            if edge.symbol == character
        }
        current = epsilon_closure(automaton, moved)
    return bool(current.intersection(automaton.final_states))


def epsilon_closure(automaton: Automaton, states: set[int]) -> set[int]:
    """Iterative closure prevents the Java reference's epsilon-cycle recursion."""
    closure = set(states)
    pending = list(states)
    while pending:
        state = pending.pop()
        for edge in automaton.transitions_from(state):
            if edge.symbol is None and edge.target not in closure:
                closure.add(edge.target)
                pending.append(edge.target)
    return closure


class ThompsonTests(unittest.TestCase):
    def test_public_exports_compile_a_literal_and_preserve_invariants(self) -> None:
        automaton = compile_regex("a")
        self.assertEqual(len(automaton.states), 2)
        self.assertEqual(len(automaton.transitions), 1)
        self.assertEqual(automaton.alphabet, frozenset({"a"}))
        self.assertTrue(accepts(automaton, "a"))
        self.assertFalse(accepts(automaton, ""))

    def test_operator_topologies_have_expected_counts(self) -> None:
        self.assertEqual((len(compile_regex("a.b").states), len(compile_regex("a.b").transitions)), (4, 3))
        self.assertEqual((len(compile_regex("a|b").states), len(compile_regex("a|b").transitions)), (6, 6))
        self.assertEqual((len(compile_regex("a*").states), len(compile_regex("a*").transitions)), (4, 5))
        self.assertEqual((len(compile_regex("a+").states), len(compile_regex("a+").transitions)), (4, 4))

    def test_independent_language_fixtures(self) -> None:
        fixtures = {
            "a.b": ({"ab"}, {"", "a", "b", "aba"}),
            "a|b": ({"a", "b"}, {"", "ab", "c"}),
            "a*": ({"", "a", "aa"}, {"b", "ab"}),
            "a+": ({"a", "aa"}, {"", "b"}),
            "a|b.c": ({"a", "bc"}, {"", "b", "c", "ac"}),
            "(a|b).c": ({"ac", "bc"}, {"a", "b", "abc"}),
            "a*+": ({"", "a", "aa"}, {"b"}),
            "(a*)+": ({"", "a", "aa"}, {"b"}),
        }
        for expression, (accepted, rejected) in fixtures.items():
            automaton = compile_regex(expression)
            for text in accepted:
                with self.subTest(expression=expression, text=text):
                    self.assertTrue(accepts(automaton, text))
            for text in rejected:
                with self.subTest(expression=expression, text=text):
                    self.assertFalse(accepts(automaton, text))

    def test_compilations_are_independent_immutable_values(self) -> None:
        first = compile_regex("a.b")
        second = compile_regex("a.b")
        self.assertIsNot(first, second)
        self.assertIsNot(first.states, second.states)
        self.assertIsNot(first.transitions, second.transitions)
        self.assertEqual(first, second)
        for edge in first.transitions:
            self.assertIn(edge.source, first.states)
            self.assertIn(edge.target, first.states)

    def test_compile_propagates_syntax_errors(self) -> None:
        with self.assertRaises(RegexSyntaxError):
            compile_regex("ab")

    def test_compiles_long_concatenation_and_deep_groups_iteratively(self) -> None:
        long_concatenation = ".".join(["a"] * 1500)
        deeply_grouped = "(" * 300 + "a" + ")" * 300
        long_automaton = compile_regex(long_concatenation)
        grouped_automaton = compile_regex(deeply_grouped)
        self.assertEqual(len(long_automaton.states), 3000)
        self.assertEqual(len(long_automaton.transitions), 2999)
        self.assertTrue(accepts(grouped_automaton, "a"))


if __name__ == "__main__":
    unittest.main()
