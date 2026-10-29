# Tutorial: check totality and the empty-subset sink

**Objective:** Check exactly one transition per state/source-symbol pair, then test empty alphabets, unreachable source symbols and no-final-state machines.

**Prerequisites:** [Subset construction](../theory/subset-construction.md) and the paired [complete-DFA theory](../theory/complete-dfa.md). Use [Getting started](../getting-started.md) for the project's Python environment.

A count of transitions is useful but insufficient: a duplicate destination choice can conceal a missing pair. This tutorial checks each state/symbol pair directly.

## 1. Predict the source alphabet

Start at 0 and make 1 final. State 9 is disconnected from the start:

**Read the figure:** Compare the two separate components. The `z` loop contributes to the alphabet even though the start cannot reach it.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="The alphabet includes unreachable edges, scrollable diagram" style="--diagram-width: 443px">
  <img class="diagram" src="/JAutomata/diagrams/complete-alphabet.svg" alt="Start 0 reaches accepting state 1 on a. Disconnected state 9 loops on z, so the source alphabet is {a, z}.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/complete-alphabet.svg">Open full-size diagram</a></p>

Predict the source alphabet, whether empty input accepts, and whether conversion includes a `z` transition from every returned state.

<details>
<summary>Reveal the alphabet and acceptance prediction</summary>

The alphabet is `{a, z}` because the model extracts labels from all source transitions, even unreachable ones. Empty input rejects, and only `a` accepts. Every converted state has a `z` transition. No subset contains 9; `z` takes the reachable subsets to the empty-subset sink instead.

</details>

## 2. Trace the complete table

| ID | Represented subset | On `a` | On `z` | Final? |
| --- | --- | --- | --- | --- |
| 0 | `{0}` | 1 | 2 | no |
| 1 | `{1}` | 2 | 2 | yes |
| 2 | `∅` | 2 | 2 | no |

The sink loops because moving from an empty set returns an empty set for every symbol. Completion is relative to `{a, z}`; no `b` edge is required.

**Stop cue:** Save the table and its alphabet. **Resume cue:** Run the program, then inspect the separate empty-alphabet example near its end.

## 3. Run the complete program

Save as `complete_dfa_lesson.py` in the repository root, then run from that root:

~~~sh
uv run --project python python complete_dfa_lesson.py
~~~

~~~python
from jautomata import accepts, to_dfa
from jautomata.model import Automaton, Transition


def check_complete(machine: Automaton, alphabet: frozenset[str]) -> None:
    """Check the stated source alphabet, no epsilon, and exactly one edge per pair."""
    assert machine.alphabet == alphabet
    assert all(edge.symbol is not None for edge in machine.transitions)
    for state in machine.states:
        for symbol in alphabet:
            outgoing = [
                edge for edge in machine.transitions
                if edge.source == state and edge.symbol == symbol
            ]
            assert len(outgoing) == 1, (state, symbol, outgoing)
    assert len(machine.transitions) == len(machine.states) * len(alphabet)


source = Automaton(
    states={0, 1, 9},
    start_state=0,
    final_states={1},
    transitions={Transition(0, "a", 1), Transition(9, "z", 9)},
)
assert source.alphabet == frozenset({"a", "z"})
dfa = to_dfa(source)
check_complete(dfa, source.alphabet)
assert dfa.states == frozenset({0, 1, 2})
assert dfa.start_state == 0
assert dfa.final_states == frozenset({1})
assert dfa.transitions == frozenset({
    Transition(0, "a", 1), Transition(0, "z", 2),
    Transition(1, "a", 2), Transition(1, "z", 2),
    Transition(2, "a", 2), Transition(2, "z", 2),
})
sink = 2  # The hand-worked subset table identifies ID 2 with the empty set.
assert sink not in dfa.final_states
for symbol in source.alphabet:
    assert Transition(sink, symbol, sink) in dfa.transitions

fixtures = {"": False, "a": True, "aa": False, "z": False, "az": False}
for word, expected in fixtures.items():
    assert accepts(source, word) is expected
    assert accepts(dfa, word) is expected
# A character outside the alphabet rejects without adding any transition.
assert "b" not in dfa.alphabet
assert not accepts(dfa, "b")
assert not accepts(dfa, "ab")

# With no finals, conversion keeps the transitions but marks no state final.
no_finals = Automaton(
    states=source.states,
    start_state=source.start_state,
    final_states=set(),
    transitions=source.transitions,
)
rejecting_dfa = to_dfa(no_finals)
check_complete(rejecting_dfa, no_finals.alphabet)
assert not rejecting_dfa.final_states
assert rejecting_dfa.transitions == dfa.transitions
assert all(not accepts(rejecting_dfa, word) for word in fixtures)

# An epsilon-only source has an empty consuming alphabet.
epsilon_only = Automaton(
    states={10, 11},
    start_state=10,
    final_states={11},
    transitions={Transition(10, None, 11)},
)
empty_alphabet_dfa = to_dfa(epsilon_only)
check_complete(empty_alphabet_dfa, frozenset())
assert empty_alphabet_dfa.states == frozenset({0})
assert empty_alphabet_dfa.final_states == frozenset({0})
assert not empty_alphabet_dfa.transitions
assert accepts(empty_alphabet_dfa, "")
assert not accepts(empty_alphabet_dfa, "a")

empty_rejector = Automaton(
    states={10}, start_state=10, final_states=set(), transitions=set()
)
empty_rejector_dfa = to_dfa(empty_rejector)
check_complete(empty_rejector_dfa, frozenset())
assert empty_rejector_dfa.states == frozenset({0})
assert not empty_rejector_dfa.final_states
assert not accepts(empty_rejector_dfa, "")

# Complete does not imply that an empty-subset sink must be reachable.
loop = Automaton(
    states={8}, start_state=8, final_states={8},
    transitions={Transition(8, "a", 8)},
)
loop_dfa = to_dfa(loop)
check_complete(loop_dfa, frozenset({"a"}))
assert loop_dfa.states == frozenset({0})
assert loop_dfa.final_states == frozenset({0})
assert loop_dfa.transitions == frozenset({Transition(0, "a", 0)})
assert accepts(loop_dfa, "") and accepts(loop_dfa, "aaa")
print("Source alphabet [a, z]: 3 complete states, including the empty sink.")
print("No-final, outside-alphabet, empty-alphabet and no-empty-sink checks passed.")
~~~

Expected output:

~~~text
Source alphabet [a, z]: 3 complete states, including the empty sink.
No-final, outside-alphabet, empty-alphabet and no-empty-sink checks passed.
~~~

## 4. Interpret the boundary cases

The original graph has at most one edge per state/symbol pair and no epsilon edges, so it is deterministic in the partial sense. It is not total over `{a, z}`. Conversion fills every pair, including `z` transitions even though the source's only `z` edge is unreachable.

The empty-alphabet checker performs zero pair checks. That is correct: there are no state/symbol pairs to fill. Both a final singleton and a nonfinal singleton can be complete with no transitions; finality still determines empty-input acceptance.

The final one-state loop is complete and accepting but never reaches an empty subset. A sink is created when a missing move reaches `∅`, not as an unconditional extra state. In contrast, removing all finals from the first example changes acceptance without changing its reachable subsets or transition table.

## Common mistake to diagnose

A test that iterates only over `machine.transitions_from(state)` never asks about absent labels. Use the **source alphabet** for every state's checks, as the helper does. The helper validates a graph; it does not add edges or implement another converter.

## Exercises

1. Remove the unreachable `z` edge and state 9 from the first source. How does the converted table change?
2. Change the first source's final set from `{1}` to `{0, 1}`. Does the empty-subset sink become final?
3. Why is one final state with no edges complete over the empty alphabet but incomplete over `{a}`?

<details>
<summary>Reveal answers with reasoning</summary>

1. The source alphabet becomes `{a}`. The output still has `{0}`, `{1}`, and `∅`, because consuming a second `a` reaches the empty subset. It now has three transitions, one per row, and no `z` column. The recognized language stays `{a}` even though the completion contract uses a smaller alphabet.
2. The start subset `{0}` becomes final and `{1}` stays final. The empty subset remains nonfinal: it contains neither 0 nor 1, or any other state. Empty input is newly accepted.
3. Over an empty alphabet there is no pair requiring a transition. Over `{a}`, the pair consisting of that state and `a` requires a destination, which is missing. In the current model an empty-edge machine derives an empty alphabet; completion over a separately enlarged alphabet is not an option exposed by `to_dfa`.

</details>

## Source connection

**Commentary:** The [complete-DFA policy](../../python/src/jautomata/subsets.py#L1-L11) describes the empty sink and the source alphabet. **Behavior:** [Alphabet extraction](../../python/src/jautomata/model.py#L128-L134) includes every consuming source label, and [the transition loop](../../python/src/jautomata/subsets.py#L106-L117) processes every one for every reached subset. The edge-case graphs and assertions here supplement those rules; they are not claims about historical Java behavior.

## Recap and resume

You checked totality by pairs, the rejecting sink's loops, whole-source alphabet extraction, outside-alphabet rejection, no finals, empty alphabets and a complete machine with no empty-subset sink.

**Stop cue:** Keep the alphabet beside each saved graph. **Resume cue:** Revisit the [total-function explanation](../theory/complete-dfa.md), then study [identity and equality](../theory/identity.md) to separate graph structure from recognized language.
