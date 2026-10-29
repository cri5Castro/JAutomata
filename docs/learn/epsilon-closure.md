---
title: "Epsilon closure and NFA evaluation"
---

import TracePlayer from '../../../components/TracePlayer.astro';

**Objective:** compute an epsilon closure and use it to explain why an NFA can
follow several possibilities at once.

An epsilon transition consumes no character. The epsilon closure of a seed set
contains the seeds and every state reachable through zero or more epsilon
transitions. The package represents epsilon by `None` in `Transition`; user
input never contains a special epsilon character.

## Worked trace: an epsilon cycle

Suppose `0 --ε--> 1`, `1 --ε--> 0`, and `1 --a--> 2`, where `2` is final.

1. Start from `{0}`. Closure visits `0`, then `1`, then sees already-visited
   `0`: the closure is `{0, 1}`.
2. On `a`, move from every active state. Only `1` reaches `{2}`.
3. Close `{2}`. It stays `{2}`, which intersects the final set, so accept.

<img class="diagram" src="/JAutomata/diagrams/epsilon-closure.svg" alt="States 0 and 1 form an epsilon cycle; state 1 has an a transition to accepting state 2." />

| Moment | Active states | Why |
| --- | --- | --- |
| seed | `{0}` | evaluation begins at 0 |
| epsilon closure | `{0, 1}` | epsilon reaches 1 and the visited set stops the cycle |
| after `a` | `{2}` | only 1 has an `a` transition |

<TracePlayer trace="closure-cycle" />

~~~python
from jautomata import accepts, epsilon_closure
from jautomata.model import Automaton, Transition

cycle = Automaton(
    states={0, 1, 2}, start_state=0, final_states={2},
    transitions={Transition(0, None, 1), Transition(1, None, 0), Transition(1, "a", 2)},
)
assert epsilon_closure(cycle, {0}) == frozenset({0, 1})
assert accepts(cycle, "a") is True
assert accepts(cycle, "") is False
~~~

**Expected output:** the code terminates and prints nothing. The cycle does
not create an infinite search because each state is visited at most once.

### Common mistake

Applying closure only at the start is insufficient. For each input character,
the evaluator moves on that character *from every active state*, then computes
epsilon closure again. That second closure can reveal a final state or another
choice.

<details>
<summary>Exercise — predict <code>accepts(compile_regex("(a*)+"), "")</code>.</summary>

It is `True`. The outer plus requires one repetition, but one repetition of
`a*` can itself match the empty string.

~~~python
from jautomata import accepts, compile_regex

assert accepts(compile_regex("(a*)+"), "") is True
~~~
</details>

## Deeper: a work-list invariant and cost

The work list contains discovered epsilon-reachable states still to inspect;
the visited set contains every state already admitted to the answer. Therefore
each reachable state enters once, including in self-loops. After building local
adjacency maps in `O(T)` for `T` transitions, closure costs `O(Vε + Eε)` over
its reached epsilon subgraph. NFA recognition repeats move-then-close for each
input character.

This is intentional: the Java converter's `cerraduraEpsilon` recurses without
a visited set ([source](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L119-L126)),
and the Java evaluator can miss competing paths. The Python
[`epsilon_closure`](../python-api.md#epsilon_closureautomaton-states) and
[`accepts`](../python-api.md#acceptsautomaton-text) contracts correct those
historical behaviors rather than reproducing them.

**Next:** package each active NFA set as one DFA state in
[Subset construction](subset-construction.md).
