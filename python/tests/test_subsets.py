"""Subset-conversion language and completion tests."""

from itertools import product
import re
import unittest

from jautomata import accepts, compile_regex, to_dfa
from jautomata.model import Automaton, Transition


def words(alphabet: tuple[str, ...], maximum_length: int) -> list[str]:
    """Enumerate each string over alphabet through maximum_length."""
    return [
        "".join(parts)
        for length in range(maximum_length + 1)
        for parts in product(alphabet, repeat=length)
    ]


class SubsetTests(unittest.TestCase):
    def test_dfa_agrees_with_nfa_for_fixtures_through_length_four(self) -> None:
        for expression in ("a|b.c", "(a|b).c", "a*", "a+", "(a.b|a*.c)+"):
            with self.subTest(expression=expression):
                nfa = compile_regex(expression)
                dfa = to_dfa(nfa)
                for text in words(tuple(sorted(nfa.alphabet)), 4):
                    self.assertEqual(accepts(nfa, text), accepts(dfa, text), text)

    def test_dfa_is_complete_deterministic_and_epsilon_free(self) -> None:
        nfa = compile_regex("a|b.c")
        dfa = to_dfa(nfa)
        for state in dfa.states:
            outgoing = [edge for edge in dfa.transitions if edge.source == state]
            self.assertEqual({edge.symbol for edge in outgoing}, dfa.alphabet)
            self.assertEqual(len(outgoing), len(dfa.alphabet))
        self.assertFalse(any(edge.symbol is None for edge in dfa.transitions))

    def test_initial_finality_cycle_and_unreachable_alphabet_symbol(self) -> None:
        nfa = Automaton(
            {0, 1, 2, 3},
            0,
            {1},
            {
                Transition(0, None, 1),
                Transition(1, None, 0),
                Transition(0, "a", 0),
                Transition(2, "b", 3),
            },
        )
        dfa = to_dfa(nfa)
        self.assertIn(0, dfa.final_states)
        self.assertEqual(dfa.alphabet, frozenset({"a", "b"}))
        self.assertTrue(accepts(dfa, ""))
        self.assertTrue(accepts(dfa, "aaa"))
        self.assertFalse(accepts(dfa, "b"))
        self.assertEqual(len(dfa.transitions), len(dfa.states) * len(dfa.alphabet))

    def test_no_final_states_and_repeated_conversion_are_stable(self) -> None:
        nfa = Automaton({0, 1}, 0, set(), {Transition(0, "a", 1)})
        before = (nfa.states, nfa.final_states, nfa.transitions)
        first = to_dfa(nfa)
        second = to_dfa(nfa)
        self.assertEqual(first, second)
        self.assertEqual(before, (nfa.states, nfa.final_states, nfa.transitions))
        for text in ("", "a", "aa", "b"):
            self.assertFalse(accepts(first, text))

    def test_reference_re_oracle_for_overlapping_syntax(self) -> None:
        fixtures = ("a.b", "a|b.c", "(a|b).c", "a*", "a+")
        for expression in fixtures:
            with self.subTest(expression=expression):
                translated = expression.replace(".", "")
                nfa = compile_regex(expression)
                for text in words(("a", "b", "c"), 3):
                    self.assertEqual(
                        accepts(nfa, text),
                        re.fullmatch(translated, text) is not None,
                        text,
                    )


if __name__ == "__main__":
    unittest.main()
