"""Immutable data model for finite automata.

The Java reference represents automata with mutable Estado and Transicion
objects. This module deliberately replaces execution flags and mutable graph
lists with value objects: an Automaton describes a finite graph and never stores
evaluation state. The design supports both Thompson NFAs and later DFA output.

Transition labels are one Unicode character or None. None is internal epsilon;
it is intentionally absent from Automaton.alphabet.

Example:
    >>> start = 0
    >>> end = 1
    >>> edge = Transition(start, "a", end)
    >>> Automaton({start, end}, start, {end}, {edge}).alphabet
    frozenset({'a'})
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable, Optional

Symbol = Optional[str]


def _validate_state_id(value: object, *, name: str) -> int:
    """Return one valid state identifier or raise a precise structural error."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(name + " must be an int state identifier")
    return value


@dataclass(frozen=True, slots=True)
class Transition:
    """An immutable directed transition in a finite automaton.

    Parameters:
        source: Integer identifier of the origin state.
        symbol: One Unicode character, or None for an epsilon transition.
        target: Integer identifier of the destination state.

    Raises:
        TypeError: If a state id is not an int, or the label is not str or None.
        ValueError: If a non-epsilon label is not exactly one character.

    Invariants:
        The object is independently valid; Automaton additionally verifies both
        endpoints belong to its finite state set. Value equality makes duplicate
        supplied transitions collapse naturally during normalization.
    """

    source: int
    symbol: Symbol
    target: int

    def __post_init__(self) -> None:
        _validate_state_id(self.source, name="source")
        _validate_state_id(self.target, name="target")
        if self.symbol is not None:
            if not isinstance(self.symbol, str):
                raise TypeError("symbol must be a one-character str or None")
            if len(self.symbol) != 1:
                raise ValueError("symbol must be exactly one Unicode character")


@dataclass(frozen=True, slots=True)
class Automaton:
    """An immutable finite automaton graph with one designated start state.

    Parameters:
        states: Finite iterable of integer state IDs.
        start_state: State at which recognition begins.
        final_states: Iterable of accepting state IDs; it may be empty.
        transitions: Iterable of immutable Transition values.

    Returns:
        A normalized value object: all supplied collections become frozenset
        values, preventing aliases to caller-owned mutable collections.

    Raises:
        TypeError: For non-integer IDs or non-Transition edges.
        ValueError: For an empty state set, a start/final outside states, or an
        edge whose endpoint is outside states.

    Invariants:
        states is non-empty, start_state is in states, final_states is a subset
        of states, and every transition remains inside states. The class carries
        no visited/accepted flags, unlike the Java evaluator.

    Complexity:
        Construction is O(S + F + T), where S, F, and T are supplied states,
        finals, and transitions. alphabet and transitions_from are O(T).
    """

    states: FrozenSet[int]
    start_state: int
    final_states: FrozenSet[int]
    transitions: FrozenSet[Transition]

    def __post_init__(self) -> None:
        states = frozenset(
            _validate_state_id(state, name="state") for state in self.states
        )
        if not states:
            raise ValueError("states must not be empty")
        start_state = _validate_state_id(self.start_state, name="start_state")
        final_states = frozenset(
            _validate_state_id(state, name="final state") for state in self.final_states
        )
        transitions = frozenset(self.transitions)
        for transition in transitions:
            if not isinstance(transition, Transition):
                raise TypeError("transitions must contain Transition values")
        if start_state not in states:
            raise ValueError("start_state must belong to states")
        if not final_states.issubset(states):
            raise ValueError("final_states must be a subset of states")
        for transition in transitions:
            if transition.source not in states or transition.target not in states:
                raise ValueError("transition endpoints must belong to states")
        object.__setattr__(self, "states", states)
        object.__setattr__(self, "start_state", start_state)
        object.__setattr__(self, "final_states", final_states)
        object.__setattr__(self, "transitions", transitions)

    @property
    def alphabet(self) -> FrozenSet[str]:
        """Return immutable input symbols, excluding internal epsilon None."""
        return frozenset(
            transition.symbol
            for transition in self.transitions
            if transition.symbol is not None
        )

    def transitions_from(self, state: int) -> FrozenSet[Transition]:
        """Return immutable outgoing edges for state.

        This helper does not interpret symbols or take epsilon closure; later
        algorithms compose it with their own work lists. Its linear scan keeps
        the base representation simple and immutable.
        """
        _validate_state_id(state, name="state")
        return frozenset(
            transition for transition in self.transitions if transition.source == state
        )
