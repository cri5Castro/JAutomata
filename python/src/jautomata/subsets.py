"""Deterministic subset construction for immutable epsilon-NFAs.

to_dfa implements breadth-first powerset construction over full epsilon-closed
NFA subsets. It intentionally fixes Java ContructorAFNtoAFD shortcomings:
cycle-safe closure, correct final-state membership, and deterministic handling
of every source alphabet symbol.

The result is a complete DFA over the original NFA alphabet. If a reachable
subset has no target on a symbol, the empty subset becomes an explicit sink and
receives its own complete self-loop transitions. No minimization is attempted.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import DefaultDict

from .model import Automaton, Transition

_EpsilonAdjacency = dict[int, tuple[int, ...]]
_SymbolAdjacency = dict[int, dict[str, tuple[int, ...]]]


def _adjacency(automaton: Automaton) -> tuple[_EpsilonAdjacency, _SymbolAdjacency]:
    """Construct local epsilon and symbol maps once for one conversion."""
    epsilon: DefaultDict[int, list[int]] = defaultdict(list)
    symbols: DefaultDict[int, DefaultDict[str, list[int]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for edge in automaton.transitions:
        if edge.symbol is None:
            epsilon[edge.source].append(edge.target)
        else:
            symbols[edge.source][edge.symbol].append(edge.target)
    return (
        {state: tuple(targets) for state, targets in epsilon.items()},
        {
            state: {symbol: tuple(targets) for symbol, targets in by_symbol.items()}
            for state, by_symbol in symbols.items()
        },
    )


def _close(seeds: set[int], epsilon: _EpsilonAdjacency) -> frozenset[int]:
    """Return iterative cycle-safe closure without mutating seeds."""
    closure = set(seeds)
    pending = list(closure)
    while pending:
        state = pending.pop()
        for target in epsilon.get(state, ()):
            if target not in closure:
                closure.add(target)
                pending.append(target)
    return frozenset(closure)


def to_dfa(automaton: Automaton) -> Automaton:
    """Convert automaton to a complete DFA by deterministic BFS subsets.

    Parameters:
        automaton: Immutable NFA or DFA with integer states and optional
            None-labelled epsilon transitions.

    Returns:
        A new epsilon-free Automaton whose states are BFS-assigned integer IDs.
        The start subset receives ID 0. Every returned state has exactly one
        transition per sorted source-alphabet symbol; an empty-subset sink is
        included whenever it becomes reachable.

    Raises:
        TypeError: If automaton is not an Automaton.

    Invariants:
        Each output state represents one full epsilon-closed NFA subset. It is
        final iff that subset intersects the NFA final-state set, including the
        initial subset. The input is never mutated.

    Complexity:
        With N NFA states and A alphabet symbols, at most 2**N DFA states are
        reachable. Conversion is exponential in the worst case; each discovered
        subset processes every symbol through local adjacency maps. BFS and
        sorted symbols make output numbering and transition construction stable.

    Correspondence:
        This replaces Java subset conversion's recursive closure and inconsistent
        kernel-only finality with complete subset membership.
    """
    if not isinstance(automaton, Automaton):
        raise TypeError("automaton must be an Automaton")

    epsilon, symbols = _adjacency(automaton)
    alphabet = tuple(sorted(automaton.alphabet))
    start_subset = _close({automaton.start_state}, epsilon)
    subset_ids: dict[frozenset[int], int] = {start_subset: 0}
    pending: deque[frozenset[int]] = deque((start_subset,))
    dfa_states: set[int] = {0}
    dfa_finals: set[int] = set()
    dfa_transitions: set[Transition] = set()

    while pending:
        subset = pending.popleft()
        source_id = subset_ids[subset]
        if subset.intersection(automaton.final_states):
            dfa_finals.add(source_id)

        for symbol in alphabet:
            moved: set[int] = set()
            for nfa_state in subset:
                moved.update(symbols.get(nfa_state, {}).get(symbol, ()))
            target_subset = _close(moved, epsilon)
            target_id = subset_ids.get(target_subset)
            if target_id is None:
                target_id = len(subset_ids)
                subset_ids[target_subset] = target_id
                dfa_states.add(target_id)
                pending.append(target_subset)
            dfa_transitions.add(Transition(source_id, symbol, target_id))

    return Automaton(
        states=dfa_states,
        start_state=0,
        final_states=dfa_finals,
        transitions=dfa_transitions,
    )
