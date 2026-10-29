# Tutorial: inspect epsilon closure on cycles

**Objective:** Run closure on a graph with a cycle, self-loops and multiple seeds, then explain each returned set.

**Prerequisites:** [Automata](../theory/automata.md), [literal fragments](../theory/literal.md), and the paired [epsilon-closure theory](../theory/epsilon-closure.md). Complete [Getting started](../getting-started.md) so `jautomata` is available in the project's Python environment.

Work in four short passes: predict, trace, run, interpret. You can stop after any pass and resume at the next numbered section.

## 1. Predict the free destinations

We use `None` for epsilon. Our graph contains the cycle 0 → 1 → 2 → 0 and epsilon self-loops at 1 and 5. The edge 2 → 3 consumes `a`.

**Read the figure:** Begin at `0` and follow only `ε` arrows. Keep the `a` edge and the separate component out of that closure.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Epsilon closure with cycles and separate components, scrollable diagram" style="--diagram-width: 752px">
  <img class="diagram" src="/JAutomata/diagrams/theory-epsilon-closure.svg" alt="Epsilon cycles connect 0, 1 and 2; reaching final 3 requires a. Separate state 4 reaches final 5 by epsilon, and 1 and 5 have epsilon self-loops.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/theory-epsilon-closure.svg">Open full-size diagram</a></p>

| Source | Label | Target |
| --- | --- | --- |
| 0 | ε | 1 |
| 1 | ε | 1 |
| 1 | ε | 2 |
| 2 | ε | 0 |
| 2 | a | 3 |
| 4 | ε | 5 |
| 5 | ε | 5 |

Before running anything, write the result for seeds `{0}`, `{3}`, `{0, 4}`, and the empty set. Decide whether reaching a final state should stop closure.

<details>
<summary>Check your prediction</summary>

The results are `{0, 1, 2}`, `{3}`, `{0, 1, 2, 4, 5}`, and `∅`. Seeds are always retained. State 3 cannot be reached from 0 without consuming `a`. Finality does not stop closure: this operation finds reachable states, independently of word acceptance.

</details>

## 2. Trace one work list

For seeds `{0}`, read `pending` as a stack with the next item at the right.

| After action | Visited | Pending |
| --- | --- | --- |
| Initialize | `{0}` | `[0]` |
| Process 0, discover 1 | `{0, 1}` | `[1]` |
| Process 1, skip visited 1, discover 2 | `{0, 1, 2}` | `[2]` |
| Process 2, skip visited 0 | `{0, 1, 2}` | `[]` |

Mark a destination when it is discovered, before scheduling its work. Both returning to 0 and looping on 1 then find an existing mark. The public API returns the resulting `frozenset`, not this work-list history; the table is an explanatory trace.

**Stop cue:** Save your four predictions. **Resume cue:** Copy the complete program below; it needs no definitions from another lesson.

## 3. Run the complete program

Save this as `epsilon_closure_lesson.py` in the repository root. From that root, run:

~~~sh
uv run --project python python epsilon_closure_lesson.py
~~~

~~~python
from jautomata import epsilon_closure
from jautomata.model import Automaton, Transition

machine = Automaton(
    states={0, 1, 2, 3, 4, 5},
    start_state=0,
    final_states={3, 5},
    transitions={
        Transition(0, None, 1),
        Transition(1, None, 1),
        Transition(1, None, 2),
        Transition(2, None, 0),
        Transition(2, "a", 3),
        Transition(4, None, 5),
        Transition(5, None, 5),
    },
)

cases = [
    (set(), frozenset()),
    ({0}, frozenset({0, 1, 2})),
    ({3}, frozenset({3})),
    ({0, 4}, frozenset({0, 1, 2, 4, 5})),
    ({5}, frozenset({5})),
]
for seeds, expected in cases:
    before = seeds.copy()
    result = epsilon_closure(machine, seeds)
    assert result == expected
    assert isinstance(result, frozenset)
    assert seeds == before  # Caller-owned sets are not mutated.
    assert seeds <= result  # Extensiveness: keep every seed.
    assert epsilon_closure(machine, result) == result  # Idempotence.
    assert all(
        edge.target in result
        for edge in machine.transitions
        if edge.source in result and edge.symbol is None
    )  # Fixed point: no epsilon edge leaves the returned set.
    print(f"{sorted(seeds)} -> {sorted(result)}")

# Different starting points in the same epsilon cycle give the same closure.
assert epsilon_closure(machine, {1}) == frozenset({0, 1, 2})
assert epsilon_closure(machine, {2}) == frozenset({0, 1, 2})
# Repeated seeds do not duplicate states or traversal work after validation.
assert epsilon_closure(machine, [0, 0, 4]) == epsilon_closure(machine, {0, 4})
# Closing several seeds combines all their free destinations.
assert epsilon_closure(machine, {0, 4}) == (
    epsilon_closure(machine, {0}) | epsilon_closure(machine, {4})
)
# A consuming edge is excluded even though its destination is final.
assert 3 not in epsilon_closure(machine, {0})
print("Closure checks passed.")
~~~

Expected output:

~~~text
[] -> []
[0] -> [0, 1, 2]
[3] -> [3]
[0, 4] -> [0, 1, 2, 4, 5]
[5] -> [5]
Closure checks passed.
~~~

## 4. Interpret the checks

The cycle terminates, and each result contains the seed set. Reclosing a result leaves it unchanged. The outgoing-epsilon assertion checks that no free successor was missed; the expected sets also reject extra unreachable states. Fixed-point membership alone would not establish that the result was the **least** closed superset.

No assertion depends on traversal ordering. Sorting is only for readable output. The immutable result describes a set, so `{0, 1, 2}` and `{2, 0, 1}` have the same meaning.

The work-list traversal visits reachable states and epsilon edges, but the public call first builds adjacency maps from every transition. Even the empty-seed call performs setup. These small examples verify semantics; they do not measure general performance.

## Common mistake to diagnose

Replacing `None` with `"ε"` changes the graph: that string is a consuming label. Closure would no longer follow the edge. A printed epsilon glyph is notation; the model's internal epsilon value is `None`.

## Exercises

1. Add an epsilon edge from 2 to 3 alongside the existing `a` edge. Which of the listed closures change?
2. Remove the visited check from the work-list explanation. Why can both a self-loop and a two-state cycle prevent termination?
3. If a returned set is epsilon-closed and includes every seed, what additional fact establishes that it is exactly the desired closure?

<details>
<summary>Reveal answers with reasoning</summary>

1. Closures seeded with `{0}` or `{0, 4}` gain state 3 because it is now freely reachable from the cycle. The results for empty seeds, `{3}`, and `{5}` stay unchanged. The extra assertion that 3 is absent must be updated because the graph's meaning changed.
2. Without checking discovery, processing 1 can schedule 1 again forever. In a two-state cycle, processing one schedules the other, which schedules the first again. A finite graph can have infinitely many walks; visited states bound the work by distinct reachable states instead.
3. Every included state must actually be epsilon-reachable from a seed. Closedness prevents omissions along free paths; reachability prevents unrelated extra states. The theory lesson's invariant proves both directions for arbitrary graphs.

</details>

## Source connection

**Commentary:** The [Python closure contract](../../python/src/jautomata/simulation.py#L80-L106) describes these guarantees. **Behavior:** The [visited work list](../../python/src/jautomata/simulation.py#L67-L77) supplies the mechanism, after [adjacency setup](../../python/src/jautomata/simulation.py#L42-L64). Our graph, trace and property checks are supplemental teaching examples.

The historical Java [“fixed” progress note](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L51-L54) must be read alongside its [unguarded recursive closure](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L119-L133). This tutorial verifies the delivered Python correction; it does not execute or repair that Java recursion.

## Recap and resume

You checked empty seeds, multiple seeds, self-loops, cycles, zero-step reachability and the boundary between epsilon and consuming edges.

**Stop cue:** Keep the program and its expected output. **Resume cue:** Review the [optional closure invariant](../theory/epsilon-closure.md), then use closure to recognize whole words in the [NFA simulation tutorial](nfa-simulation.md).
