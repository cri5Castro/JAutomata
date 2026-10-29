"""Production simulation regressions for Java evaluator defects."""

from dataclasses import FrozenInstanceError
import unittest

from jautomata import accepts, compile_regex, epsilon_closure
from jautomata.model import Automaton, Transition


class SimulationTests(unittest.TestCase):
    def test_epsilon_closure_terminates_for_cycle_and_self_loop(self) -> None:
        automaton = Automaton(
            {0, 1, 2},
            0,
            {2},
            {
                Transition(0, None, 0),
                Transition(0, None, 1),
                Transition(1, None, 0),
                Transition(1, "a", 2),
            },
        )
        self.assertEqual(epsilon_closure(automaton, {0}), frozenset({0, 1}))
        self.assertTrue(accepts(automaton, "a"))
        self.assertFalse(accepts(automaton, ""))

    def test_explores_same_symbol_and_epsilon_alternatives(self) -> None:
        automaton = Automaton(
            {0, 1, 2, 3, 4},
            0,
            {3, 4},
            {
                Transition(0, "a", 1),
                Transition(0, "a", 2),
                Transition(1, "b", 3),
                Transition(0, None, 4),
                Transition(4, "a", 3),
            },
        )
        self.assertTrue(accepts(automaton, "a"))
        self.assertTrue(accepts(automaton, "ab"))
        self.assertFalse(accepts(automaton, "b"))

    def test_empty_initial_final_and_epsilon_only_languages(self) -> None:
        via_epsilon = Automaton({0, 1}, 0, {1}, {Transition(0, None, 1)})
        epsilon_only = Automaton({0}, 0, {0}, set())
        empty_language = Automaton({0}, 0, set(), set())
        self.assertTrue(accepts(via_epsilon, ""))
        self.assertTrue(accepts(epsilon_only, ""))
        self.assertFalse(accepts(epsilon_only, "a"))
        self.assertFalse(accepts(empty_language, ""))

    def test_repeated_calls_and_source_values_are_unchanged(self) -> None:
        automaton = compile_regex("(a|b).c")
        before = (automaton.states, automaton.final_states, automaton.transitions)
        answers = [accepts(automaton, text) for text in ("ac", "bc", "a", "ac")]
        self.assertEqual(answers, [True, True, False, True])
        self.assertEqual(before, (automaton.states, automaton.final_states, automaton.transitions))
        with self.assertRaises(FrozenInstanceError):
            automaton.start_state = 9

    def test_type_and_state_errors_are_explicit(self) -> None:
        automaton = compile_regex("a")
        with self.assertRaises(TypeError):
            accepts(automaton, None)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            epsilon_closure(automaton, {True})
        with self.assertRaises(ValueError):
            epsilon_closure(automaton, {99})


if __name__ == "__main__":
    unittest.main()
