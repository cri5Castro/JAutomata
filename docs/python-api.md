# Python API reference

This page is a contract lookup, not a prerequisite for the learning path. For
one small trace before the signatures, start at [Foundations](learn/foundations.md).

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

## Java correspondence

The generated entries below document the delivered Python contract. The original
Java coursework remains explanatory source evidence: compare the parser and
Thompson comments in [Java reference behavior](java-reference.md), especially
the [ShuntingYard](../src/ExpresionRegularToAFN/ShuntingYard.java#L13-L61) and
[ConstructorDeAutomatas](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L9-L238)
commentary. Python intentionally corrects the Java evaluator and closure defects
described there rather than preserving their mutable execution behavior.

<!-- GENERATED API REFERENCE: START -->
## Generated API reference

This section is generated from public Python signatures and explanatory
docstrings. Do not edit inside these markers; run
`uv run --project python python python/scripts/generate_api_docs.py` instead.

### `jautomata`

#### `RegexSyntaxError`

**Signature:** `RegexSyntaxError(message: 'str', expression: 'str', position: 'int') -> 'None'`

**Source:** [jautomata](../python/src/jautomata/regex.py#L21)

> Raised when text is not in the supported explicit-concatenation grammar.
>
> Attributes:
>     expression: Original expression supplied by the caller.
>     position: Zero-based character offset at which parsing failed.
>
> Example:
>     >>> to_postfix("a|")
>     Traceback (most recent call last):
>     ...
>     jautomata.regex.RegexSyntaxError: expected an operand after '|' at index 2

#### `compile_regex`

**Signature:** `compile_regex(expression: 'str') -> 'Automaton'`

**Source:** [jautomata](../python/src/jautomata/thompson.py#L97)

> Compile expression into a fresh immutable Thompson epsilon-NFA.
>
> Parameters:
>     expression: Explicit-concatenation regex accepted by regex.parse.
>
> Returns:
>     Automaton with integer IDs, exactly one final state, and None-labelled
>     epsilon edges. The graph is immutable and contains no evaluation flags.
>
> Raises:
>     TypeError: If expression is not str.
>     RegexSyntaxError: If expression is malformed.
>
> Example:
>     >>> automaton = compile_regex("a.b*")
>     >>> automaton.alphabet == frozenset({"a", "b"})
>     True
>
> Correspondence:
>     This is the value-oriented counterpart of Java
>     ExpresionRegularToAFN/ConstructorDeAutomatas.java. Union/star/plus use
>     the standard fresh-entry/fresh-exit Thompson topology; concatenation
>     uses the Java class's available epsilon-link variant instead of its
>     mutable fusion variant.

#### `epsilon_closure`

**Signature:** `epsilon_closure(automaton: 'Automaton', states: 'Iterable[int]') -> 'frozenset[int]'`

**Source:** [jautomata](../python/src/jautomata/simulation.py#L80)

> Return every state epsilon-reachable from states, including the seeds.
>
> Parameters:
>     automaton: Immutable finite automaton to inspect.
>     states: Iterable of start-state IDs, each belonging to automaton.
>
> Returns:
>     A frozenset containing each seed and every state reached by zero or more
>     None-labelled transitions.
>
> Raises:
>     TypeError: If automaton or a state identifier has the wrong type.
>     ValueError: If a supplied state is not in automaton.
>
> Invariants:
>     A visited set admits each state at most once, so self-loops and cycles
>     terminate. The input automaton and caller collection are never mutated.
>
> Complexity:
>     O(Ve + Ee) for the epsilon-reachable subgraph after O(T) local adjacency
>     construction, where T is total transitions.
>
> Correspondence:
>     Java ContructorAFNtoAFD.cerraduraEpsilon recurses without a visited set.
>     This work-list implementation intentionally fixes that defect.

#### `accepts`

**Signature:** `accepts(automaton: 'Automaton', text: 'str') -> 'bool'`

**Source:** [jautomata](../python/src/jautomata/simulation.py#L113)

> Return whether an epsilon-NFA accepts text using complete state sets.
>
> Parameters:
>     automaton: Immutable NFA or DFA. Epsilon transitions may be present.
>     text: Unicode text; one model transition consumes one character.
>
> Returns:
>     True precisely when the epsilon-closed state set after consuming all
>     characters intersects automaton.final_states.
>
> Raises:
>     TypeError: If automaton is not Automaton or text is not str.
>
> Algorithm:
>     Start with closure(start). For each character, collect targets from
>     every current state on that character, then close that target set.
>     This explores same-symbol nondeterminism and consuming/epsilon
>     alternatives simultaneously.
>
> Complexity:
>     O(T + sum_i(Ei + Vi)) with local adjacency setup O(T), where each
>     character i explores its reached transition/state subgraph. Space is
>     O(T + V) for local maps and the current closure.
>
> Example:
>     >>> from .thompson import compile_regex
>     >>> accepts(compile_regex("a*"), "")
>     True

#### `to_dfa`

**Signature:** `to_dfa(automaton: 'Automaton') -> 'Automaton'`

**Source:** [jautomata](../python/src/jautomata/subsets.py#L57)

> Convert automaton to a complete DFA by deterministic BFS subsets.
>
> Parameters:
>     automaton: Immutable NFA or DFA with integer states and optional
>         None-labelled epsilon transitions.
>
> Returns:
>     A new epsilon-free Automaton whose states are BFS-assigned integer IDs.
>     The start subset receives ID 0. Every returned state has exactly one
>     transition per sorted source-alphabet symbol; an empty-subset sink is
>     included whenever it becomes reachable.
>
> Raises:
>     TypeError: If automaton is not an Automaton.
>
> Invariants:
>     Each output state represents one full epsilon-closed NFA subset. It is
>     final iff that subset intersects the NFA final-state set, including the
>     initial subset. The input is never mutated.
>
> Complexity:
>     With N NFA states and A alphabet symbols, at most 2**N DFA states are
>     reachable. Conversion is exponential in the worst case; each discovered
>     subset processes every symbol through local adjacency maps. BFS and
>     sorted symbols make output numbering and transition construction stable.
>
> Correspondence:
>     This replaces Java subset conversion's recursive closure and inconsistent
>     kernel-only finality with complete subset membership.

### `jautomata.model`

#### `Transition`

**Signature:** `Transition(source: 'int', symbol: 'Symbol', target: 'int') -> None`

**Source:** [jautomata.model](../python/src/jautomata/model.py#L34)

> An immutable directed transition in a finite automaton.
>
> Parameters:
>     source: Integer identifier of the origin state.
>     symbol: One Unicode character, or None for an epsilon transition.
>     target: Integer identifier of the destination state.
>
> Raises:
>     TypeError: If a state id is not an int, or the label is not str or None.
>     ValueError: If a non-epsilon label is not exactly one character.
>
> Invariants:
>     The object is independently valid; Automaton additionally verifies both
>     endpoints belong to its finite state set. Value equality makes duplicate
>     supplied transitions collapse naturally during normalization.

#### `Automaton`

**Signature:** `Automaton(states: 'FrozenSet[int]', start_state: 'int', final_states: 'FrozenSet[int]', transitions: 'FrozenSet[Transition]') -> None`

**Source:** [jautomata.model](../python/src/jautomata/model.py#L67)

> An immutable finite automaton graph with one designated start state.
>
> Parameters:
>     states: Finite iterable of integer state IDs.
>     start_state: State at which recognition begins.
>     final_states: Iterable of accepting state IDs; it may be empty.
>     transitions: Iterable of immutable Transition values.
>
> Returns:
>     A normalized value object: all supplied collections become frozenset
>     values, preventing aliases to caller-owned mutable collections.
>
> Raises:
>     TypeError: For non-integer IDs or non-Transition edges.
>     ValueError: For an empty state set, a start/final outside states, or an
>     edge whose endpoint is outside states.
>
> Invariants:
>     states is non-empty, start_state is in states, final_states is a subset
>     of states, and every transition remains inside states. The class carries
>     no visited/accepted flags, unlike the Java evaluator.
>
> Complexity:
>     Construction is O(S + F + T), where S, F, and T are supplied states,
>     finals, and transitions. alphabet and transitions_from are O(T).

<!-- GENERATED API REFERENCE: END -->
