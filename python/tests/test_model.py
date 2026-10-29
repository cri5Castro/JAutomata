"""Tests for immutable structural automaton invariants."""

from dataclasses import FrozenInstanceError
import unittest

from jautomata.model import Automaton, Transition


class TransitionTests(unittest.TestCase):
    def test_transition_is_immutable_and_validates_single_symbols(self) -> None:
        edge = Transition(0, "é", 1)
        with self.assertRaises(FrozenInstanceError):
            edge.target = 2
        with self.assertRaises(ValueError):
            Transition(0, "ab", 1)
        with self.assertRaises(TypeError):
            Transition(True, "a", 1)


class AutomatonTests(unittest.TestCase):
    def test_collections_are_normalized_and_alphabet_excludes_epsilon(self) -> None:
        states = [0, 1]
        finals = [1]
        edges = [Transition(0, None, 1), Transition(0, "a", 1)]
        automaton = Automaton(states, 0, finals, edges)
        states.append(2)
        finals.clear()
        edges.clear()
        self.assertEqual(automaton.states, frozenset({0, 1}))
        self.assertEqual(automaton.final_states, frozenset({1}))
        self.assertEqual(automaton.alphabet, frozenset({"a"}))
        self.assertEqual(automaton.transitions_from(0), frozenset(automaton.transitions))

    def test_empty_language_and_epsilon_only_models_are_valid(self) -> None:
        empty_language = Automaton({0}, 0, set(), set())
        epsilon_only = Automaton({0}, 0, {0}, set())
        self.assertEqual(empty_language.final_states, frozenset())
        self.assertEqual(epsilon_only.final_states, frozenset({0}))

    def test_rejects_structurally_invalid_graphs(self) -> None:
        with self.assertRaises(ValueError):
            Automaton(set(), 0, set(), set())
        with self.assertRaises(ValueError):
            Automaton({0}, 1, set(), set())
        with self.assertRaises(ValueError):
            Automaton({0}, 0, {1}, set())
        with self.assertRaises(ValueError):
            Automaton({0}, 0, set(), {Transition(0, "a", 1)})
        with self.assertRaises(TypeError):
            Automaton({0}, 0, set(), {(0, "a", 0)})


if __name__ == "__main__":
    unittest.main()
