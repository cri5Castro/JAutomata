"""Pure iterative epsilon-NFA simulation.

This module corrects the Java evaluator's threaded branches, single-transition
lookup, and mutable accepted/visited flags. It works only with immutable
Automaton values: each call builds local adjacency maps and local work lists.

None labels represent epsilon. Epsilon closure and acceptance are iterative, so
epsilon cycles terminate without a recursion limit. The implementation is
deliberately suitable for both hand-built NFAs and Thompson output.
"""

from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Iterable

from .model import Automaton

_EpsilonAdjacency = dict[int, tuple[int, ...]]
_SymbolAdjacency = dict[int, dict[str, tuple[int, ...]]]


def _validate_automaton(automaton: object) -> Automaton:
    """Return an Automaton or make public-call type errors explicit."""
    if not isinstance(automaton, Automaton):
        raise TypeError("automaton must be an Automaton")
    return automaton


def _validate_states(automaton: Automaton, states: Iterable[int]) -> frozenset[int]:
    """Normalize closure seeds and reject IDs that cannot belong to automaton."""
    normalized: set[int] = set()
    for state in states:
        if isinstance(state, bool) or not isinstance(state, int):
            raise TypeError("states must contain int state identifiers")
        if state not in automaton.states:
            raise ValueError("states must belong to automaton")
        normalized.add(state)
    return frozenset(normalized)


def _adjacency(automaton: Automaton) -> tuple[_EpsilonAdjacency, _SymbolAdjacency]:
    """Build local immutable traversal views in O(T) time.

    The model intentionally favors immutable value semantics over precomputed
    mutable indexes. Simulation creates these views per call, avoiding cached
    execution state and ensuring repeated calls cannot leak prior results.
    """
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


def _close(seeds: Iterable[int], epsilon: _EpsilonAdjacency) -> frozenset[int]:
    """Compute a cycle-safe epsilon closure from already validated seed IDs."""
    closure = set(seeds)
    pending = list(closure)
    while pending:
        state = pending.pop()
        for target in epsilon.get(state, ()):
            if target not in closure:
                closure.add(target)
                pending.append(target)
    return frozenset(closure)


def epsilon_closure(automaton: Automaton, states: Iterable[int]) -> frozenset[int]:
    """Return every state epsilon-reachable from states, including the seeds.

    Parameters:
        automaton: Immutable finite automaton to inspect.
        states: Iterable of start-state IDs, each belonging to automaton.

    Returns:
        A frozenset containing each seed and every state reached by zero or more
        None-labelled transitions.

    Raises:
        TypeError: If automaton or a state identifier has the wrong type.
        ValueError: If a supplied state is not in automaton.

    Invariants:
        A visited set admits each state at most once, so self-loops and cycles
        terminate. The input automaton and caller collection are never mutated.

    Complexity:
        O(Ve + Ee) for the epsilon-reachable subgraph after O(T) local adjacency
        construction, where T is total transitions.

    Correspondence:
        Java ContructorAFNtoAFD.cerraduraEpsilon recurses without a visited set.
        This work-list implementation intentionally fixes that defect.
    """
    automaton = _validate_automaton(automaton)
    seeds = _validate_states(automaton, states)
    epsilon, _ = _adjacency(automaton)
    return _close(seeds, epsilon)


def accepts(automaton: Automaton, text: str) -> bool:
    """Return whether an epsilon-NFA accepts text using complete state sets.

    Parameters:
        automaton: Immutable NFA or DFA. Epsilon transitions may be present.
        text: Unicode text; one model transition consumes one character.

    Returns:
        True precisely when the epsilon-closed state set after consuming all
        characters intersects automaton.final_states.

    Raises:
        TypeError: If automaton is not Automaton or text is not str.

    Algorithm:
        Start with closure(start). For each character, collect targets from
        every current state on that character, then close that target set.
        This explores same-symbol nondeterminism and consuming/epsilon
        alternatives simultaneously.

    Complexity:
        O(T + sum_i(Ei + Vi)) with local adjacency setup O(T), where each
        character i explores its reached transition/state subgraph. Space is
        O(T + V) for local maps and the current closure.

    Example:
        >>> from .thompson import compile_regex
        >>> accepts(compile_regex("a*"), "")
        True
    """
    automaton = _validate_automaton(automaton)
    if not isinstance(text, str):
        raise TypeError("text must be str")
    epsilon, symbols = _adjacency(automaton)
    current = _close((automaton.start_state,), epsilon)
    for character in text:
        moved: set[int] = set()
        for state in current:
            moved.update(symbols.get(state, {}).get(character, ()))
        current = _close(moved, epsilon)
    return bool(current.intersection(automaton.final_states))
