# Python API reference

Import public operations from jautomata:

Start an interactive packaged session from the repository root with
uv run --project python python, then use the imports below.

~~~python
from jautomata import RegexSyntaxError, accepts, compile_regex, epsilon_closure, to_dfa
from jautomata.model import Automaton, Transition
~~~

## compile_regex(expression)

compile_regex returns a fresh immutable Thompson epsilon-NFA. expression must be
a non-empty string using one-character literals, explicit ., |, postfix * and +,
and parentheses. It raises RegexSyntaxError, a ValueError subtype, for malformed
expressions and TypeError for non-string input. Parsing and construction are
iterative and linear in expression length.

## epsilon_closure(automaton, states)

epsilon_closure returns a frozenset containing seeds and all states reachable
via None-labelled edges. Every seed must be a state in automaton. It raises
TypeError for incorrect automaton/state types and ValueError for unknown IDs.
The visited work list terminates on epsilon cycles.

## accepts(automaton, text)

accepts returns bool for an NFA or DFA. It starts with epsilon closure, advances
every currently reachable state for each Unicode character, and closes again.
It raises TypeError when text is not str. It never changes the immutable input.
Its local adjacency-map setup is O(T); subsequent work depends on reached
states and transitions.

## to_dfa(automaton)

to_dfa returns an epsilon-free, complete DFA using breadth-first subset
construction and sorted alphabet traversal. Output state 0 represents the
epsilon closure of the NFA start. A DFA state is final exactly when its full NFA
subset intersects input finals. Worst-case state growth is exponential; no
minimization is included.

## Model values

Transition(source, symbol, target) is immutable. symbol is one Unicode character
or None. Automaton(states, start_state, final_states, transitions) normalizes
collections to frozensets, checks endpoint/final/start membership, exposes
alphabet without None, and offers transitions_from(state).
