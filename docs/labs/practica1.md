# Practica 1: reconstruct a hand-built NFA

**Goal:** rebuild the original six-state graph, explain its two branches, and compare recognition with an independent parity predicate.

**Prerequisites:** [automata](../theory/automata.md), [epsilon closure](../theory/epsilon-closure.md), [NFA simulation](../theory/nfa-simulation.md) and [subset construction](../theory/subset-construction.md). The [pure-execution lesson](../theory/pure-execution.md) explains why a cycle does not require threads.

**Route:** read the graph → predict a short trace → run 127 checks → explain the language.

## What comes from the historical source?

The active [Practica1Main example](../../src/Practica1/Practica1Main.java#L11-L42) creates six states, marks 3 and 6 final, starts at 1, and evaluates `11111`. Its transition comment flags the epsilon cycle as a concern. Java represents epsilon with an empty transition string; Python uses `None`.

The language description below is **inferred from the graph**, not stated by that comment. This lab runs the delivered Python implementation; it does not rely on output from the historical evaluator. The [Java reference](../java-reference.md#defects-and-port-decisions) documents its known limitations.

## Reconstruct the graph

A double circle marks a final state. `ε` means consume no character.

Read the figure: follow the upper branch for ones and the lower branch for zeros. Double circles mark final states; epsilon edges consume nothing.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Practica 1: odd ones or even zeros, scrollable diagram" style="--diagram-width: 790px">
  <img class="diagram" src="/JAutomata/diagrams/practica1-language.svg" alt="Start 1 branches by epsilon to the odd-ones cycle 2–3 and even-zeros branch 4–5–6. Finals 3 and 6 are double circles; 4 and 6 form an epsilon cycle.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/practica1-language.svg">Open full-size diagram</a></p>

The exact transition list is the authoritative reading of the diagram:

| Origin | Label | Target |
| --- | --- | --- |
| 1 | ε | 2 |
| 1 | ε | 4 |
| 2 | `1` | 3 |
| 3 | `1` | 2 |
| 4 | `0` | 5 |
| 5 | `0` | 6 |
| 4 | ε | 6 |
| 6 | ε | 4 |

The upper branch alternates between nonfinal 2 and final 3 as each `1` is read. The lower branch consumes two `0` characters per return to final 6; its epsilon links also make 6 reachable before reading anything.

## Predict the closures

| Word | Final active set after closure | Accept? |
| --- | --- | --- |
| empty | `{1, 2, 4, 6}` | yes: contains 6 |
| `1` | `{3}` | yes |
| `11` | `{2}` | no |
| `11111` | `{3}` | yes |
| `0` | `{5}` | no |
| `00` | `{4, 6}` | yes |
| `01` | `{}` | no |

Pause before the program: why does empty input accept even though state 1 is not final? Why can neither branch recover after a mixed word such as `01`?

## Run the complete reconstruction

Follow [Getting started](../getting-started.md), save as `practica1_lab.py` in the repository root, then run:

~~~sh
uv run --project python python practica1_lab.py
~~~

~~~python
from itertools import product
from jautomata import accepts, epsilon_closure, to_dfa
from jautomata.model import Automaton, Transition

nfa = Automaton(
    states={1, 2, 3, 4, 5, 6},
    start_state=1,
    final_states={3, 6},
    transitions={
        Transition(1, None, 2), Transition(1, None, 4),
        Transition(2, "1", 3), Transition(3, "1", 2),
        Transition(4, "0", 5), Transition(5, "0", 6),
        Transition(4, None, 6), Transition(6, None, 4),
    },
)
assert len(nfa.states) == 6
assert len(nfa.transitions) == 8
assert nfa.alphabet == frozenset({"0", "1"})
assert epsilon_closure(nfa, {1}) == frozenset({1, 2, 4, 6})
assert epsilon_closure(nfa, {4}) == frozenset({4, 6})
assert epsilon_closure(nfa, {6}) == frozenset({4, 6})
dfa = to_dfa(nfa)

# This independent predicate uses character content and parity, not graph moves.
def inferred_language(word):
    odd_ones = len(word) % 2 == 1 and set(word) <= {"1"}
    even_zeros = len(word) % 2 == 0 and set(word) <= {"0"}
    return odd_ones or even_zeros

expected_sets = {
    "": {1, 2, 4, 6}, "1": {3}, "11": {2}, "11111": {3},
    "0": {5}, "00": {4, 6}, "01": set(),
}
for word, expected_set in expected_sets.items():
    current = epsilon_closure(nfa, {nfa.start_state})
    for symbol in word:
        moved = {edge.target for edge in nfa.transitions
                 if edge.source in current and edge.symbol == symbol}
        current = epsilon_closure(nfa, moved)
    assert current == frozenset(expected_set)
    result = accepts(nfa, word)
    assert result is inferred_language(word)
    assert accepts(dfa, word) is result
    print(repr(word) + ": " + str(result))

checked = 0
for length in range(7):
    for letters in product("01", repeat=length):
        word = "".join(letters)
        expected = inferred_language(word)
        assert accepts(nfa, word) is expected
        assert accepts(dfa, word) is expected
        checked += 1
assert checked == 127
assert not accepts(nfa, "2")
assert not accepts(dfa, "2")
print("binary words checked:", checked)
~~~

Expected output:

~~~text
'': True
'1': True
'11': False
'11111': True
'0': False
'00': True
'01': False
binary words checked: 127
~~~

## Interpret the language

The inferred language consists of **odd-length words made entirely of `1`**, together with **even-length words made entirely of `0`, including empty input**. “Odd” and “even” describe length, not the integer represented by the word.

There are `1 + 2 + 4 + 8 + 16 + 32 + 64 = 127` binary words of lengths 0–6. Comparing both machines with a predicate that does not use transitions is stronger evidence than comparing the two machines alone: a shared bug could otherwise make them agree on a wrong result. These finite tests still do not prove a claim about arbitrary lengths.

<details>
<summary>Optional depth: why the characterization holds for every length</summary>

Any nonempty accepting path must leave state 1 on one of its epsilon edges. It cannot return to 1 or switch branches afterward. The upper branch has only `1` edges and reaches final 3 after exactly an odd number of them. The lower branch has only `0` edges; one `0` reaches 5, a second reaches 6, and epsilon returns to 4 allow another pair. Its epsilon path from 1 already reaches final 6 for zero characters. Consequently no mixed word accepts, and the stated parity conditions are both necessary and sufficient. This argument is added reasoning from the graph, not a historical comment.

</details>

## Exercise: remove one epsilon edge

Suppose only `4 → 6` on epsilon is removed. Keep `6 → 4`. Which of empty input, `00` and `0000` still accepts?

<details>
<summary>Answer and reason</summary>

Empty input now rejects because the initial closure is `{1, 2, 4}`. Both `00` and `0000` still accept: each pair of zeros reaches 6, and the retained `6 → 4` epsilon edge enables another pair. The lower branch now accepts positive even lengths, while the upper odd-ones branch is unchanged.

</details>

**Common mistake:** declaring the graph nonterminating because it contains an epsilon cycle. The graph permits infinitely many walks, but reachability needs only a finite visited set. Another mistake is excluding empty input by checking only whether the original start state is final.

## Recap and stop point

You reconstructed every source edge, traced both branches and checked the NFA, DFA and independent parity predicate on 127 words.

**Stop here:** explain the initial closure without looking at the table. **Resume:** [Practica 2](practica2.md) replaces the manual graph with a compound expression and follows its constructors.
