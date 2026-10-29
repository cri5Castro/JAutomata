"""Independently verify the generated browser teaching fixtures."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from jautomata import accepts, compile_regex, to_dfa
from jautomata.model import Automaton, Transition


ROOT = Path(__file__).resolve().parents[2]
TRACE_FILE = ROOT / "site" / "src" / "data" / "traces.json"
GENERATOR = ROOT / "python" / "scripts" / "generate_teaching_traces.py"


def _cycle_machine() -> Automaton:
    """Build the documented epsilon-cycle fixture independently of the generator."""
    return Automaton(
        states={0, 1, 2},
        start_state=0,
        final_states={2},
        transitions={
            Transition(0, None, 1),
            Transition(1, None, 0),
            Transition(1, "a", 2),
        },
    )


class TeachingTraceTests(unittest.TestCase):
    """Check emitted states, epsilon moves, consumed input, and acceptance facts."""

    def _traces(self) -> dict[str, dict[str, object]]:
        payload = json.loads(TRACE_FILE.read_text())
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["generator"], "python/scripts/generate_teaching_traces.py")
        return {trace["id"]: trace for trace in payload["traces"]}

    def test_fixture_is_fresh(self) -> None:
        """The checked-in fixture exactly matches the Python generator's output."""
        subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_active_states_epsilon_steps_and_consumed_input(self) -> None:
        """Expected fixture facts are independent constants, not copied from the generator."""
        traces = self._traces()
        expected = {
            "thompson-ab": (["", "a", "ab"], [[0], [1, 2], [3]], [[], [2], []]),
            "closure-cycle": (["", "a"], [[0, 1], [2]], [[1], []]),
            "subset-union": (["", "a", "ab"], [[0, 2, 4], [1, 5], []], [[0, 2], [5], []]),
        }
        self.assertEqual(set(traces), set(expected))
        for identifier, (consumed, states, epsilon_added) in expected.items():
            steps = traces[identifier]["steps"]
            self.assertEqual([step["consumed"] for step in steps], consumed)
            self.assertEqual([step["active_states"] for step in steps], states)
            self.assertEqual([step["epsilon_added"] for step in steps], epsilon_added)

    def test_nfa_dfa_acceptance_matches_independent_models(self) -> None:
        """NFA/DFA truth values and the documented sink case agree with product calls."""
        fixtures = {
            "thompson-ab": (compile_regex("a.b"), "ab", True, 3),
            "closure-cycle": (_cycle_machine(), "a", True, 1),
            "subset-union": (compile_regex("a|b"), "ab", False, 3),
        }
        for identifier, (nfa, text, answer, dfa_state) in fixtures.items():
            with self.subTest(trace=identifier):
                dfa = to_dfa(nfa)
                trace = self._traces()[identifier]["verification"]
                self.assertEqual(accepts(nfa, text), answer)
                self.assertEqual(accepts(dfa, text), answer)
                self.assertEqual(trace["input"], text)
                self.assertEqual(trace["nfa_accepts"], answer)
                self.assertEqual(trace["dfa_accepts"], answer)
                self.assertEqual(trace["dfa_state"], dfa_state)


if __name__ == "__main__":
    unittest.main()
