# Tutorial: reuse a graph across independent runs

**Goal:** trace an epsilon cycle, preserve simultaneous branches, and verify that repeated accepted and rejected calls leave the machine unchanged.

**Prerequisites:** [pure-execution theory](../theory/pure-execution.md), [NFA simulation](../theory/nfa-simulation.md) and [identity](../theory/identity.md).

**Setup:** use [Getting started](../getting-started.md). Save the complete program as `pure_execution_demo.py` in the repository root:

~~~sh
uv run --project python python pure_execution_demo.py
~~~

## Predict and trace

Use this graph; a double circle marks a final state and `ε` consumes no character:

**Read the figure:** Follow the `ε` cycle first, then keep both `a` destinations. A double circle marks an accepting state.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Keep both branches after the epsilon cycle, scrollable diagram" style="--diagram-width: 596px">
  <img class="diagram" src="/JAutomata/diagrams/pure-execution.svg" alt="Start 0 and state 1 form an epsilon cycle. On a, 1 reaches final 2 and 0 reaches 3; from 3, b reaches final 4.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/pure-execution.svg">Open full-size diagram</a></p>

Start at `0`. Predict empty input, `a`, `ab` and `aa` before running. The two `a` routes are simultaneous possibilities, even though only one ends immediately in a final state.

| Prefix | Active states after closure | Why |
| --- | --- | --- |
| empty | `{0, 1}` | Follow the epsilon cycle once per discovered state. |
| `a` | `{2, 3}` | Retain both matching moves. |
| `ab` | `{4}` | Only state 3 has a `b` move. |

## Run the complete program

~~~python
from jautomata import accepts, epsilon_closure, to_dfa
from jautomata.model import Automaton, Transition

machine = Automaton(
    states={0, 1, 2, 3, 4},
    start_state=0,
    final_states={2, 4},
    transitions={
        Transition(0, None, 1),
        Transition(1, None, 0),
        Transition(1, "a", 2),
        Transition(0, "a", 3),
        Transition(3, "b", 4),
    },
)
before = (
    machine.states, machine.start_state,
    machine.final_states, machine.transitions,
)
before_hash = hash(machine)
seeds = {0}
current = epsilon_closure(machine, seeds)
assert seeds == {0}
assert current == frozenset({0, 1})
print("start:", sorted(current))

# An explanatory two-character trace using the public closure operation.
# accepts below remains the recognizer used for every test.
for symbol, expected in (("a", {2, 3}), ("b", {4})):
    moved = {
        edge.target for edge in machine.transitions
        if edge.source in current and edge.symbol == symbol
    }
    current = epsilon_closure(machine, moved)
    assert current == frozenset(expected)
    print("after " + symbol + ":", sorted(current))

dfa = to_dfa(machine)
cases = (("a", True), ("", False), ("ab", True),
         ("aa", False), ("b", False), ("aba", False))
calls = 0
for _ in range(10):
    for word, expected in cases:
        assert accepts(machine, word) is expected
        assert accepts(dfa, word) is expected
        calls += 1

assert calls == 60
after = (
    machine.states, machine.start_state,
    machine.final_states, machine.transitions,
)
assert before == after
assert hash(machine) == before_hash
assert epsilon_closure(machine, {0}) == frozenset({0, 1})
print("NFA calls checked:", calls)
print("graph unchanged:", before == after)
~~~

Expected output:

~~~text
start: [0, 1]
after a: [2, 3]
after b: [4]
NFA calls checked: 60
graph unchanged: True
~~~

## Interpret the result

The initial closure must terminate even though `0 → 1 → 0` cycles. A state is admitted to that closure's work list once. The next call starts a fresh closure, so earlier discovery of `0` does not suppress future work.

Each batch places a rejection immediately after an acceptance. That checks that the result is recomputed for the new word, while the snapshot checks that evaluation and conversion leave the graph's fields unchanged. The program also makes 60 corresponding DFA calls. These are regression checks for the chosen inputs, supported by the local-state implementation; repetition alone is not a proof about all executions or all words.

No operating-system threads are needed to retain `{2, 3}`. A set holds both possibilities, and acceptance examines it only after the whole word has been consumed. The manual trace scans the edge set for readability; the library evaluator builds adjacency maps for efficient repeated lookup inside each call.

## Exercise: final now, wrong later

Why does `a` accept but `aa` reject? What would break if the evaluator returned true as soon as state `2` appeared?

<details>
<summary>Answer and reason</summary>

After the first `a`, the active set is `{2, 3}`. State `2` is final, so that prefix is an accepted word. For `aa`, one more character remains, and neither state has an `a` move. The final active set is empty. Returning early would incorrectly accept `aa` and any other extension of `a` without processing its suffix.

</details>

**Common mistake:** putting `visited` or `accepted` on the permanent graph and forgetting when to reset it. A second mistake is discarding state `3` merely because state `2` is already final; that would lose the successful `ab` path.

## Source connection

**Commentary:** [the Java wait warning and flag reset](../../src/Model/AutomataStructure/Automata.java#L28-L52) and [Python's per-call indexing rationale](../../python/src/jautomata/simulation.py#L42-L48) motivate the exercise. **Verified implementation:** [local closure work](../../python/src/jautomata/simulation.py#L67-L77) and [local recognition state](../../python/src/jautomata/simulation.py#L143-L153).

**Supplement:** the five-state graph and repeated-call experiment are added teaching examples. The historical thread issue is a source-flow finding; this tutorial does not run the Java evaluator or claim to reproduce a particular interleaving.

## Recap and stop point

One graph can answer many independent questions. Keep all current possibilities, finish the word, and discard local traversal data after its use.

**Stop here:** trace `aba` without running it. **Resume:** use [validation and complexity](../theory/validation-complexity.md) to account for the maps and work lists created by each call.
