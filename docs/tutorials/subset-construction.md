# Tutorial: verify a full subset table

**Objective:** Match a hand-built subset table to `to_dfa`, inspect stable state IDs and finality, and test bounded language agreement.

**Prerequisites:** [NFA simulation](../theory/nfa-simulation.md) and the paired [subset-construction theory](../theory/subset-construction.md). Follow [Getting started](../getting-started.md) to prepare the project's environment.

This program constructs its own NFA. You do not need a variable or file from an earlier tutorial. The table is explanatory data; the delivered converter creates the DFA.

## 1. Predict the five represented sets

The NFA starts at 0, has finals `{4, 5}`, and has these edges:

**Read the figure:** Start at `0`; keep both direct `a` branches and the `ε` route to `1`. Double circles mark finals `4` and `5`.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Three ways to consume a, then follow b, scrollable diagram" style="--diagram-width: 596px">
  <img class="diagram" src="/JAutomata/diagrams/competing-paths.svg" alt="Start 0 has epsilon to 1 and a edges to 2 and 3; 1 has a to final 5, 3 has epsilon to final 4, 2 has b to 5, and 4 loops on b.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/competing-paths.svg">Open full-size diagram</a></p>

Close `{0}` first. Process discovered sets in BFS order, always trying `a` before `b`.

| ID | Represented set | On `a` | On `b` | Final? |
| --- | --- | --- | --- | --- |
| 0 | `{0, 1}` | 1 | 2 | no |
| 1 | `{2, 3, 4, 5}` | 2 | 3 | yes |
| 2 | `∅` | 2 | 2 | no |
| 3 | `{4, 5}` | 2 | 4 | yes |
| 4 | `{4}` | 2 | 4 | yes |

**Prediction check:** The first `a` move produces `{2, 3, 5}`. Why is that not the subset stored as ID 1?

<details>
<summary>Reveal the missing member</summary>

The move result is the kernel. Closing it adds 4 through 3 → 4, so ID 1 represents `{2, 3, 4, 5}`. That extra state is final and supplies the `b` self-loop used by longer accepted words. The closure, not the raw kernel, determines future behavior.

</details>

## 2. Follow discovery order

Processing ID 0 discovers ID 1 on `a` and ID 2 on `b`. Processing ID 1 discovers ID 3 on `b`. ID 2 only returns to itself. Processing ID 3 discovers ID 4, which adds no new subset. This yields five states and ten transitions.

The public return value contains integer state IDs. It does not expose a subset-to-ID dictionary, so the program records our independently worked mapping and checks each table entry by a move and closure. It then checks the converter's entire transition set against the table.

**Stop cue:** Save the five-row table. **Resume cue:** Run the program and read the assertion that checks the first kernel separately.

## 3. Run the complete program

Save as `subset_construction_lesson.py` in the repository root. From that root, run:

~~~sh
uv run --project python python subset_construction_lesson.py
~~~

~~~python
from itertools import product

from jautomata import accepts, epsilon_closure, to_dfa
from jautomata.model import Automaton, Transition

nfa = Automaton(
    states={0, 1, 2, 3, 4, 5},
    start_state=0,
    final_states={4, 5},
    transitions={
        Transition(0, None, 1),
        Transition(0, "a", 2),
        Transition(0, "a", 3),
        Transition(1, "a", 5),
        Transition(3, None, 4),
        Transition(2, "b", 5),
        Transition(4, "b", 4),
    },
)

# These are the hand-worked table's represented subsets, not converter internals.
subsets = {
    0: frozenset({0, 1}),
    1: frozenset({2, 3, 4, 5}),
    2: frozenset(),
    3: frozenset({4, 5}),
    4: frozenset({4}),
}
expected_targets = {
    (0, "a"): 1, (0, "b"): 2,
    (1, "a"): 2, (1, "b"): 3,
    (2, "a"): 2, (2, "b"): 2,
    (3, "a"): 2, (3, "b"): 4,
    (4, "a"): 2, (4, "b"): 4,
}
assert epsilon_closure(nfa, {nfa.start_state}) == subsets[0]
for (source_id, symbol), target_id in expected_targets.items():
    moved = frozenset(
        edge.target
        for edge in nfa.transitions
        if edge.source in subsets[source_id] and edge.symbol == symbol
    )
    assert epsilon_closure(nfa, moved) == subsets[target_id]
    if (source_id, symbol) == (0, "a"):
        assert moved == frozenset({2, 3, 5})
        assert moved != subsets[target_id]  # Kernel differs from closure.

# Distinct kernels can have the same complete closed set.
assert epsilon_closure(nfa, {3}) == epsilon_closure(nfa, {3, 4})
assert epsilon_closure(nfa, {3}) == frozenset({3, 4})

dfa = to_dfa(nfa)
assert dfa.start_state == 0
assert dfa.states == frozenset(subsets)
assert dfa.final_states == frozenset({1, 3, 4})
assert dfa.final_states == frozenset(
    state_id for state_id, subset in subsets.items()
    if subset & nfa.final_states
)
assert dfa.transitions == frozenset(
    Transition(source, symbol, target)
    for (source, symbol), target in expected_targets.items()
)
assert dfa == to_dfa(nfa)  # Stable BFS numbering, not arbitrary fresh names.
assert len(dfa.states) <= 2 ** len(nfa.states)

# Finality must include the initial closure, even through an epsilon path.
initially_final = Automaton(
    states=nfa.states,
    start_state=nfa.start_state,
    final_states={1},
    transitions=nfa.transitions,
)
initially_final_dfa = to_dfa(initially_final)
assert initially_final_dfa.final_states == frozenset({0})
assert accepts(initially_final_dfa, "")
assert initially_final_dfa.transitions == dfa.transitions

# Independent language description: one a, followed only by zero or more b's.
checked = 0
for length in range(5):
    for letters in product("ab", repeat=length):
        word = "".join(letters)
        expected = word[:1] == "a" and all(c == "b" for c in word[1:])
        assert accepts(nfa, word) is expected, word
        assert accepts(dfa, word) is expected, word
        checked += 1
assert checked == 31
print("Subset table verified: 5 states, 10 transitions, finals [1, 3, 4].")
print("31 words of lengths 0 through 4 agree with the language fixture.")
~~~

Expected output:

~~~text
Subset table verified: 5 states, 10 transitions, finals [1, 3, 4].
31 words of lengths 0 through 4 agree with the language fixture.
~~~

## 4. Interpret what the checks establish

The complete transition comparison checks stable BFS IDs and every row of the table, including the empty subset. The final-state checks use full subset membership. The `{1}`-final variant checks the easily missed initial-finality case.

The enumeration covers all 31 words over `{a, b}` of lengths zero through four. Both machines match an independently stated language predicate, so simple agreement cannot hide a shared wrong answer on those inputs. This is still a **bounded test**, not a proof for all lengths. The [theory's prefix correspondence](../theory/subset-construction.md) supplies that reasoning.

The `2 ** N` assertion checks the upper bound for this one graph. Five reached subsets do not demonstrate exponential growth, and the bound does not say every NFA reaches all possible subsets.

## Common mistake to diagnose

Do not demand that every correct determinization use these same integer names unless its numbering policy is specified. This implementation promises BFS with sorted symbols, so these exact IDs are testable here. In another converter, a consistently renamed graph could recognize the same language.

## Exercises

1. Why does the converter keep both ID 3 and ID 4, even though both accept exactly zero or more `b`s from that point onward?
2. A proposed test checks only `accepts(nfa, word) == accepts(dfa, word)`. What extra evidence does our predicate provide, and what does it still not prove?
3. If the source finals become empty, which rows disappear and which output states remain final?

<details>
<summary>Reveal answers with reasoning</summary>

1. Their represented sets differ: `{4, 5}` versus `{4}`. Subset construction reuses equal sets; it does not merge all states with equal future languages. That second operation is DFA minimization and is outside this converter.
2. The predicate checks a separately derived expected language, which can detect a mistake shared by the two implementations on the tested words. It still covers only lengths zero through four and cannot establish arbitrary-length equivalence.
3. No rows disappear. Edges and reachability are unchanged, so the same five sets are discovered. Every output state becomes nonfinal because no subset intersects an empty set of source finals.

</details>

## Source connection

**Commentary:** The [Python conversion contract](../../python/src/jautomata/subsets.py#L57-L87) specifies full subsets, BFS, stable numbering and the exponential bound. **Behavior:** The [construction loop](../../python/src/jautomata/subsets.py#L91-L124) implements those rules. This table and the independent word predicate are supplemental examples.

Java's [kernel equality experiment](../../src/AFDtoAFDbySubsets/Subconjunto.java#L53-L67) and [finality handling](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L93-L114) explain why the distinction matters. Its [initial-state construction](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L44-L48) does not mark initial finality. These are qualified static limitations in the [Java audit](../java-reference.md#defects-and-port-decisions); no claim is made that every historical example fails.

## Recap and resume

You verified complete subset membership, kernel-versus-closure identity, initial finality, BFS IDs, every table entry and bounded language agreement.

**Stop cue:** Save the checked table and the number 31 with its length bound. **Resume cue:** Open the [complete-DFA tutorial](complete-dfa.md) to examine the empty subset and the source-alphabet boundary.
