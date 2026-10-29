# Tutorial: trace every NFA branch

**Objective:** Verify a closure–move–closure trace against the public recognizer, including competing paths and acceptance after the full word.

**Prerequisites:** [Automata](../theory/automata.md), [epsilon closure](../theory/epsilon-closure.md), and the paired [NFA simulation theory](../theory/nfa-simulation.md). Use [Getting started](../getting-started.md) for the existing Python environment.

The program creates its own graph and data. Its trace is a teaching view of one fixed input; `accepts` remains the recognizer used to decide the example words.

## 1. Predict before running

Start at 0. Final states are 4 and 5.

**Read the figure:** Start at `0`; keep both direct `a` branches and the `ε` route to `1`. Double circles mark finals `4` and `5`.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Three ways to consume a, then follow b, scrollable diagram" style="--diagram-width: 596px">
  <img class="diagram" src="/JAutomata/diagrams/competing-paths.svg" alt="Start 0 has epsilon to 1 and a edges to 2 and 3; 1 has a to final 5, 3 has epsilon to final 4, 2 has b to 5, and 4 loops on b.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/competing-paths.svg">Open full-size diagram</a></p>

State 0 can consume `a` in two ways **and** has an epsilon alternative through 1. Predict empty input, `a`, `abb`, and `aa`. Keep all paths until the input determines which survive.

<details>
<summary>Reveal the language prediction</summary>

Empty input rejects: initial closure `{0, 1}` has no final state. `a` accepts because its closure contains 4 and 5. `abb` accepts through the loop at 4. `aa` rejects because no active state after the first `a` can consume another `a`. The graph accepts `a` followed by zero or more `b`s; that description is inferred from the graph, not copied from a source comment.

</details>

## 2. Trace `abb`

| Prefix already consumed | Raw move targets | Active set after closure |
| --- | --- | --- |
| `""` | — | `{0, 1}` |
| `a` | `{2, 3, 5}` | `{2, 3, 4, 5}` |
| `ab` | `{4, 5}` | `{4, 5}` |
| `abb` | `{4}` | `{4}` |

On `a`, states 2 and 3 come from the two direct edges. State 5 comes from consuming at epsilon-reachable state 1. Closure adds 4 after the move. Skipping either class of alternative makes the first row incomplete.

**Stop cue:** Keep the table. **Resume cue:** Compare each row with the program's expected data; the assertions check intermediate sets, not just the final Boolean.

## 3. Run the complete program

Save as `nfa_simulation_lesson.py` in the repository root, then run from that root:

~~~sh
uv run --project python python nfa_simulation_lesson.py
~~~

~~~python
from jautomata import accepts, epsilon_closure
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

active = epsilon_closure(nfa, {nfa.start_state})
assert active == frozenset({0, 1})
expected_rows = [
    ("a", frozenset({2, 3, 5}), frozenset({2, 3, 4, 5})),
    ("ab", frozenset({4, 5}), frozenset({4, 5})),
    ("abb", frozenset({4}), frozenset({4})),
]
prefix = ""
for character, (expected_prefix, expected_move, expected_active) in zip(
    "abb", expected_rows
):
    moved = frozenset(
        edge.target
        for edge in nfa.transitions
        if edge.source in active and edge.symbol == character
    )
    active = epsilon_closure(nfa, moved)
    prefix += character
    assert (prefix, moved, active) == (
        expected_prefix, expected_move, expected_active
    )
    assert bool(active & nfa.final_states) == accepts(nfa, prefix)
assert prefix == "abb"

fixtures = {
    "": False,
    "a": True,
    "ab": True,
    "abb": True,
    "abbb": True,
    "aa": False,
    "b": False,
    "ba": False,
    "ac": False,
}
for word, expected in fixtures.items():
    assert accepts(nfa, word) is expected, word

# The graph stays fixed; change only which states count as final.
initially_final = Automaton(
    states=nfa.states,
    start_state=nfa.start_state,
    final_states={1},
    transitions=nfa.transitions,
)
assert accepts(initially_final, "")  # An epsilon path reaches final state 1.
assert not accepts(initially_final, "a")
assert not accepts(initially_final, "b")

no_finals = Automaton(
    states=nfa.states,
    start_state=nfa.start_state,
    final_states=set(),
    transitions=nfa.transitions,
)
assert all(not accepts(no_finals, word) for word in fixtures)
assert epsilon_closure(nfa, set()) == frozenset()
print("Trace verified: '', 'a', 'ab', 'abb'.")
print("9 word fixtures and final-state variants passed.")
~~~

Expected output:

~~~text
Trace verified: '', 'a', 'ab', 'abb'.
9 word fixtures and final-state variants passed.
~~~

## 4. Interpret what passed

The first move checks same-symbol branching: both 2 and 3 are present. It also checks that taking epsilon from 0 does not suppress the consuming edges at 0, because 5 is present as well. The post-move closure check verifies that 4 is added before consuming a `b`.

The original machine has two finals, and either one suffices. Changing finals to `{1}` makes empty input accept without changing a single edge. Giving the same graph no finals makes every fixture reject. This separates reachability from the acceptance condition.

The `aa` fixture checks that an accepting prefix does not finish the match early. The `ac` fixture checks a character outside the alphabet. Both lose every active path before the entire word has a final active state.

## Common mistake to diagnose

If a recognizer returns true for `aa` because it saw a final state after the first `a`, it has recognized a prefix, not the whole input. JAutomata's `accepts` decides full-word membership. The last character matters even when a prior prefix could have ended successfully.

## Exercises

1. Remove the epsilon edge 3 → 4 but keep all other edges. Predict `a`, `ab`, and `abb`.
2. Keep the original graph, but use final states `{2}`. Predict `a` and `ab`.
3. Why would one successful run of a threaded path explorer be weaker evidence than the invariant in the theory page?

<details>
<summary>Reveal answers with reasoning</summary>

1. `a` still accepts through 0 → 1 → 5. `ab` still accepts through 0 → 2 → 5. `abb` rejects: state 4 and its loop have become unreachable, so after `ab` only 5 remains and it has no `b` edge.
2. `a` accepts because its active set contains 2. `ab` rejects: the next move leaves 2 and produces `{4, 5}`, neither of which is final in this variant. Finality does not stick to a path after the path leaves a final state.
3. One run checks one input under one execution schedule. It cannot show that every possible consuming and epsilon alternative was retained for every prefix. The complete-set invariant establishes that semantic property independently of thread scheduling; tests then check concrete implementation cases.

</details>

## Source connection

**Commentary:** The [Python acceptance docstring](../../python/src/jautomata/simulation.py#L113-L142) states the recurrence and complete-set contract. **Behavior:** The [implementation](../../python/src/jautomata/simulation.py#L143-L153) collects all targets, closes them and tests finals after the loop. The graph and trace here supplement those sources.

The historical Java [branch handling](../../src/Model/AutomataStructure/Estado.java#L32-L80) and [single matching-edge lookup](../../src/Model/AutomataStructure/Estado.java#L100-L110) motivate these cases. Their limitations are source-flow findings from the [Java audit](../java-reference.md#defects-and-port-decisions), not reproduced Java runs. No new evaluator or threads are needed to perform this tutorial.

## Recap and resume

You verified complete active sets, same-symbol branches, epsilon/consuming alternatives, empty input, multiple finals, no finals and full-word rejection.

**Stop cue:** Keep the `abb` trace and explain why 4 survives its last step. **Resume cue:** Revisit the [prefix invariant](../theory/nfa-simulation.md), then turn each whole active set into a DFA state in the [subset tutorial](subset-construction.md).
