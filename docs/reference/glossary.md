# Reference glossary

Use this page as a lookup table; it does not replace the worked traces in
[Learn](../learn/foundations.md).

| Term | Meaning in JAutomata |
|---|---|
| **accept** | After all input is consumed, at least one active state is final. |
| **alphabet** | Immutable set of consuming one-character transition labels. It excludes `None`. |
| **closure** | A set plus every state reached through zero or more epsilon edges. |
| **complete DFA** | A DFA with exactly one transition for each state/symbol pair in the source alphabet. |
| **DFA** | Deterministic finite automaton: each state/symbol pair has one next state. |
| **epsilon / ε** | A transition that consumes no input; represented internally by Python `None`. |
| **final state** | A member of `Automaton.final_states`; it accepts only when input is exhausted. |
| **fragment** | Thompson builder value with one entry and one exit state. |
| **NFA** | Nondeterministic finite automaton: a state/symbol pair may have many next states. |
| **postfix** | Operator-after-operands representation used between parsing and Thompson construction. |
| **sink** | The non-final DFA state representing the reachable empty NFA subset. |
| **subset construction** | The NFA-to-DFA algorithm that treats one NFA-state set as one DFA state. |
| **transition** | `Transition(source, symbol, target)`, an immutable directed edge. |

## Public names

| Name | Use |
|---|---|
| `compile_regex(expression)` | Parse the explicit-dot language and return a fresh Thompson NFA. |
| `epsilon_closure(automaton, states)` | Return an immutable epsilon-closed state set. |
| `accepts(automaton, text)` | Decide recognition without mutating the automaton. |
| `to_dfa(automaton)` | Return an epsilon-free complete DFA; no minimization. |
| `RegexSyntaxError` | Positioned `ValueError` subtype for malformed supported regex syntax. |

For precise parameters and errors, see the [Python API](../python-api.md). For
the implementation's decisions and complexity, see [Algorithms](../algorithms.md).

## Historical names

The preserved Java names are Spanish: `Estado` means state, `Transicion` means
transition, `cerraduraEpsilon` means epsilon closure, and `ContructorAFNtoAFD`
is the NFA-to-DFA converter (including the original spelling). Their comments
are source evidence, not the Python behavior oracle; the audit marks the
intentional corrections in [Java reference behavior](../java-reference.md).
