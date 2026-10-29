"""Independent deterministic grammar and language oracles.

These tests intentionally avoid using the implementation under test as their
oracle. Fixed seeds make broad coverage repeatable in the normal unittest suite.
"""

from __future__ import annotations

from collections import deque
from itertools import product
import random
import re
import unittest

from jautomata import accepts, compile_regex, to_dfa
from jautomata.model import Automaton, Transition
from jautomata.regex import RegexSyntaxError, to_postfix


def generated_expression(rng: random.Random, depth: int) -> tuple[str, str]:
    """Return a port expression and independent Python-re reference pattern."""
    if depth == 0 or rng.random() < 0.25:
        literal = rng.choice("ab")
        return literal, re.escape(literal)
    left, reference = generated_expression(rng, depth - 1)
    operation = rng.choice(("concat", "union", "star", "plus"))
    if operation in ("star", "plus"):
        postfix = "*" if operation == "star" else "+"
        return "(" + left + ")" + postfix, "(?:" + reference + ")" + postfix
    right, other = generated_expression(rng, depth - 1)
    if operation == "concat":
        return "(" + left + ").(" + right + ")", "(?:" + reference + ")(?:" + other + ")"
    return "(" + left + ")|(" + right + ")", "(?:" + reference + ")|(?:" + other + ")"


def path_accepts(machine: Automaton, text: str) -> bool:
    """Independently search NFA configurations as (state, input offset) pairs."""
    queue: deque[tuple[int, int]] = deque(((machine.start_state, 0),))
    seen: set[tuple[int, int]] = set()
    while queue:
        state, offset = queue.popleft()
        if (state, offset) in seen:
            continue
        seen.add((state, offset))
        if offset == len(text) and state in machine.final_states:
            return True
        for edge in machine.transitions:
            if edge.source != state:
                continue
            if edge.symbol is None:
                queue.append((edge.target, offset))
            elif offset < len(text) and edge.symbol == text[offset]:
                queue.append((edge.target, offset + 1))
    return False


def grammar_accepts(text: str) -> bool:
    """Independent finite-state grammar recognizer for short expression strings."""
    depth = 0
    need_operand = True
    for token in text:
        if token == "(":
            if not need_operand:
                return False
            depth += 1
        elif token == ")":
            if need_operand or depth == 0:
                return False
            depth -= 1
        elif token in ".|":
            if need_operand:
                return False
            need_operand = True
        elif token in "*+":
            if need_operand:
                return False
        else:
            if not need_operand:
                return False
            need_operand = False
    return depth == 0 and not need_operand


class IndependentOracleTests(unittest.TestCase):
    """Durable broad checks for language, graph, and parser behavior."""

    def test_generated_regex_languages_against_python_re(self) -> None:
        rng = random.Random(29471)
        words = [
            "".join(chars)
            for length in range(6)
            for chars in product("ab", repeat=length)
        ] + ["c", "ac", "ca", "abc"]
        comparisons = 0
        for case in range(120):
            source, reference = generated_expression(rng, 3)
            nfa = compile_regex(source)
            dfa = to_dfa(nfa)
            for word in words:
                expected = re.fullmatch(reference, word) is not None
                self.assertEqual(accepts(nfa, word), expected, (case, "NFA", source, word))
                self.assertEqual(accepts(dfa, word), expected, (case, "DFA", source, word))
                comparisons += 2
            for word in reversed(words[:10]):
                expected = re.fullmatch(reference, word) is not None
                self.assertEqual(accepts(nfa, word), expected, (case, "repeat NFA", source, word))
                self.assertEqual(accepts(dfa, word), expected, (case, "repeat DFA", source, word))
        self.assertEqual(comparisons, 16080)

    def test_random_epsilon_graphs_against_configuration_search(self) -> None:
        rng = random.Random(61583)
        words = [
            "".join(chars)
            for length in range(5)
            for chars in product("ab", repeat=length)
        ] + ["c"]
        checks = 0
        for case in range(40):
            states = set(range(rng.randint(1, 6)))
            edges = {
                Transition(source, symbol, target)
                for source in states
                for target in states
                for symbol in (None, "a", "b")
                if rng.random() < 0.14
            }
            finals = {state for state in states if rng.random() < 0.4}
            nfa = Automaton(states, 0, finals, edges)
            original_hash = hash(nfa)
            dfa = to_dfa(nfa)
            self.assertEqual(dfa, to_dfa(nfa), ("determinism", case))
            for state in dfa.states:
                for symbol in nfa.alphabet:
                    outgoing = [
                        edge
                        for edge in dfa.transitions
                        if edge.source == state and edge.symbol == symbol
                    ]
                    self.assertEqual(len(outgoing), 1, ("completion", case, state, symbol))
            self.assertTrue(all(edge.symbol is not None for edge in dfa.transitions))
            for text in words:
                expected = path_accepts(nfa, text)
                self.assertEqual(accepts(nfa, text), expected, (case, "NFA", text))
                self.assertEqual(accepts(dfa, text), expected, (case, "DFA", text))
                checks += 2
            self.assertEqual(hash(nfa), original_hash, ("immutable source", case))
        self.assertEqual(checks, 2560)

    def test_exhaustive_short_syntax_against_independent_grammar(self) -> None:
        count = 0
        for length in range(6):
            for chars in product("ab.|*+()", repeat=length):
                expression = "".join(chars)
                expected = grammar_accepts(expression)
                try:
                    to_postfix(expression)
                    actual = True
                except RegexSyntaxError:
                    actual = False
                self.assertEqual(actual, expected, expression)
                count += 1
        self.assertEqual(count, 37449)


if __name__ == "__main__":
    unittest.main()
