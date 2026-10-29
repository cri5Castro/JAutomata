# Python compatibility contract

This is the normative implementation contract. For progressive examples and
revealable exercises, use the [learning path](index.md#learn) before returning
here for exact grammar and algorithm rules.

## Purpose and assumptions

The Python implementation lives under python/src/jautomata; tests live under
python/tests. It ports intended regular-language semantics, not incidental Java
API behavior or known defects. This contract is based on the source audit in
[Java reference behavior](java-reference.md).

The supported regex dialect is deliberately small:

- Literals are single Unicode characters except the reserved . | * + ( ).
  Whitespace and other punctuation are literals.
- Concatenation is explicit with ., union uses |, star and plus are postfix,
  and parentheses group. There are no escapes, character classes, wildcard,
  implicit concatenation, or source-level epsilon token.
- Precedence is postfix closure (3), concatenation (2), then union (1).
  Binary operators are left-associative; postfix chains are left-to-right.
- Internal epsilon is None, not a public alphabet member. It maps the Java
  internal empty-string edge convention to an unambiguous Python value.
- Empty expressions and malformed grouping/operator sequences raise
  RegexSyntaxError(ValueError); parsing never relies on stack underflow or
  partially constructed automata.

## Public API and Java mapping

| Java reference | Python responsibility/API | Compatibility decision |
|---|---|---|
| Automata, Estado, Transicion | jautomata.model: immutable Automaton and Transition values | No mutable acceptance or visited execution flags. |
| ShuntingYard.postfix | jautomata.regex parser and postfix conversion | Preserve grammar/precedence; reject malformed input explicitly. |
| ConstructorDeAutomatas | jautomata.thompson.compile_regex(expression) -> Automaton | Basic, union, concat, star, plus; use fresh immutable construction. |
| Subconjunto, ContructorAFNtoAFD | jautomata.subsets.to_dfa(automaton) -> Automaton | Store complete represented subsets and derive finality from all members. |
| Automata.evaluar / Estado.procesar | jautomata.simulation.accepts(automaton, text) -> bool | Synchronous complete state-set simulation. |
| Java epsilon convention | jautomata.simulation.epsilon_closure(automaton, states) -> frozenset[int] | Internal None edges only; cycles terminate. |
| Practice classes / Main | Documentation examples and tests | Educational inputs, not output assertions. |

The package exports compile_regex, RegexSyntaxError, accepts, epsilon_closure,
and to_dfa. Model types remain available from jautomata.model.

## Required semantic behavior

1. **Thompson NFA.** A literal has two states and one labelled edge. Union adds
   a fresh start/final with epsilon edges; concatenation epsilon-links its
   fragments; star admits a bypass; plus does not. Each compile call allocates
   fresh immutable graph values.
2. **Epsilon closure.** From a state set, traverse every epsilon edge and return
   each reachable state once. Self-loops and cycles terminate.
3. **NFA evaluation.** Begin with closure(start). For every input character,
   move from every current state then close the result. Accept iff the final
   state set intersects accepting states after all input is consumed. Empty
   input therefore works when start closure reaches a final.
4. **Subset conversion.** The DFA start is closure(NFA start). Every DFA state
   represents a complete immutable NFA-state set. For each source-alphabet
   symbol, make closure(move(set, symbol)); it is final iff the full subset
   contains an NFA final.
5. **Complete DFA policy.** The returned DFA is complete over the original NFA
   alphabet. If a reachable subset has no transition for a symbol, the empty
   subset is an explicit sink. No minimization is performed.
6. **Repeated calls.** accepts, epsilon_closure, and to_dfa do not mutate
   transitions, alphabet, final states, or later answers.

## Intentional incompatibilities and regression targets

| Java behavior | Python requirement | Regression coverage |
|---|---|---|
| evaluar starts epsilon threads and checks flags without joining. | accepts is synchronous and returns bool. | [simulation tests](../python/tests/test_simulation.py) exercise repeated calls and epsilon alternatives. |
| One matching edge is selected; epsilons are tried only when there is no match. | Explore all matching edges plus full epsilon closure. | [simulation tests](../python/tests/test_simulation.py) cover same-symbol branches and consuming/epsilon alternatives. |
| Recursive closure has no visited set. | Work-list closure uses a visited set. | [simulation tests](../python/tests/test_simulation.py) cover epsilon cycles and self-loops. |
| Subset conversion checks finality inconsistently and does not safely close cycles. | Full subsets determine finality; iterative closure terminates. | [subset tests](../python/tests/test_subsets.py) cover initial finality and cycles. |
| Lazy alphabet cache can change epsilon inclusion by query order. | Immutable public alphabet always excludes None. | [model tests](../python/tests/test_model.py) cover alphabet normalization. |
| Parser has no malformed-input contract and does not insert dots. | Explicit dots only; RegexSyntaxError for invalid syntax. | [regex tests](../python/tests/test_regex.py) cover malformed grammar. |

## Implemented evaluation and DFA guarantees

The implementation deliberately corrects the Java evaluator rather than
emulating its concurrency/state-leak defects. It builds local adjacency maps
for every operation and uses iterative work lists; no evaluation flags or
threads are stored on Automaton values.

Subset conversion uses sorted source-alphabet symbols and breadth-first subset
discovery, so output IDs and transitions are deterministic. Worst-case subset
growth is exponential in the number of NFA states. Independent tests cover
bounded NFA/DFA agreement, complete sinks, unreachable source symbols, no-final
machines, epsilon-only machines, and a Python re full-match oracle only for
the overlapping literal/dot/union/closure syntax.

## Minimum verification matrix

Implementation and release checks must include:

- parser precedence for a|b.c and (a|b).c;
- rejection of implicit ab and malformed grammar;
- NFA/DFA agreement over independent fixture strings;
- manually constructed epsilon cycles with bounded completion;
- repeated accepts calls for accepting and rejecting strings;
- absence of epsilon from the public input alphabet;
- complete DFA transitions for every returned state and source alphabet symbol.

Java compilation/execution is not a prerequisite: this environment has no usable
Java runtime. Python tests are the independent language oracle and remain valid
when Java is unavailable.
