"""Generate the site teaching traces from actual immutable Python automata.

The browser only displays this fixture.  It does not parse regexes, simulate an
NFA, or construct a DFA; Python remains the single behavioral implementation.
Run with ``--check`` to fail instead of rewriting stale output.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Iterable

from jautomata import accepts, compile_regex, epsilon_closure, to_dfa
from jautomata.model import Automaton, Transition


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "site" / "src" / "data" / "traces.json"


def _states_text(states: Iterable[int]) -> str:
    """Render a sorted state collection consistently for the trace player."""
    return "{" + ", ".join(str(state) for state in sorted(states)) + "}"


def _move(machine: Automaton, states: Iterable[int], symbol: str) -> frozenset[int]:
    """Return direct symbol targets; closure remains delegated to public Python API."""
    return frozenset(
        transition.target
        for transition in machine.transitions
        if transition.source in states and transition.symbol == symbol
    )


def _nfa_steps(machine: Automaton, text: str) -> list[dict[str, object]]:
    """Trace closure, move, and closure states for one concrete input word."""
    seeds = frozenset({machine.start_state})
    active = epsilon_closure(machine, seeds)
    steps: list[dict[str, object]] = [
        {
            "label": "Initial epsilon closure",
            "consumed": "",
            "active": _states_text(active),
            "active_states": sorted(active),
            "epsilon_added": sorted(active.difference(seeds)),
            "note": "Start with the initial state, then follow every epsilon edge.",
        }
    ]
    consumed = ""
    for symbol in text:
        moved = _move(machine, active, symbol)
        active = epsilon_closure(machine, moved)
        consumed += symbol
        steps.append(
            {
                "label": f"Consume {symbol}",
                "consumed": consumed,
                "active": _states_text(active),
                "active_states": sorted(active),
                "epsilon_added": sorted(active.difference(moved)),
                "note": "Move from every active state, then close the resulting set.",
            }
        )
    return steps


def _dfa_state_after(machine: Automaton, text: str) -> int:
    """Follow the actual complete DFA transition relation for a fixture word."""
    state = machine.start_state
    for symbol in text:
        matches = [
            transition.target
            for transition in machine.transitions
            if transition.source == state and transition.symbol == symbol
        ]
        if len(matches) != 1:
            raise RuntimeError(f"DFA has no unique {symbol!r} move from state {state}")
        state = matches[0]
    return state


def _trace(
    identifier: str,
    title: str,
    expression: str,
    machine: Automaton,
    text: str,
    *,
    final_note: str,
) -> dict[str, object]:
    """Build one display fixture and attach NFA/DFA agreement evidence."""
    dfa = to_dfa(machine)
    steps = _nfa_steps(machine, text)
    nfa_answer = accepts(machine, text)
    dfa_answer = accepts(dfa, text)
    if nfa_answer != dfa_answer:
        raise RuntimeError(f"NFA/DFA disagreement for teaching trace {identifier}")
    steps[-1]["label"] = "Accept" if nfa_answer else "Reject"
    steps[-1]["note"] = final_note
    return {
        "id": identifier,
        "title": title,
        "expression": expression,
        "steps": steps,
        "verification": {
            "input": text,
            "nfa_accepts": nfa_answer,
            "dfa_accepts": dfa_answer,
            "dfa_state": _dfa_state_after(dfa, text),
        },
    }


def render_traces() -> dict[str, object]:
    """Create deterministic display fixtures from compiled and hand-built models."""
    cycle = Automaton(
        states={0, 1, 2},
        start_state=0,
        final_states={2},
        transitions={
            Transition(0, None, 1),
            Transition(1, None, 0),
            Transition(1, "a", 2),
        },
    )
    return {
        "schema_version": 1,
        "generator": "python/scripts/generate_teaching_traces.py",
        "traces": [
            _trace(
                "thompson-ab",
                "Run the Thompson NFA for a.b",
                "a.b",
                compile_regex("a.b"),
                "ab",
                final_note="The final active state accepts after both symbols are consumed.",
            ),
            _trace(
                "closure-cycle",
                "Close an epsilon cycle, then consume a",
                "epsilon cycle then a",
                cycle,
                "a",
                final_note="The final state is active after the complete input.",
            ),
            _trace(
                "subset-union",
                "Follow a|b into the complete DFA sink",
                "a|b",
                compile_regex("a|b"),
                "ab",
                final_note="After a then b, no NFA branch remains; the DFA is in its sink.",
            ),
        ],
    }


def main(arguments: Iterable[str] | None = None) -> int:
    """Write generated JSON, or return nonzero if ``--check`` finds stale output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when output is stale")
    options = parser.parse_args(arguments)
    expected = json.dumps(render_traces(), indent=2, ensure_ascii=False) + "\n"
    actual = OUTPUT.read_text() if OUTPUT.exists() else ""
    if actual == expected:
        print(f"Teaching traces are current: {OUTPUT.relative_to(ROOT)}")
        return 0
    if options.check:
        print(f"Teaching traces are stale: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    OUTPUT.write_text(expected)
    print(f"Generated teaching traces: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
