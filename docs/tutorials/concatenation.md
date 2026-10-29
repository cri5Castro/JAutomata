# Tutorial: join fragments in order

**Objective:** Inspect the epsilon link in `a.b`, compare a safe three-state illustration, and demonstrate why arbitrary endpoint fusion is unsafe.

**Prerequisites:** [Literal tutorial](literal.md) and [concatenation theory](../theory/concatenation.md).

**Setup:** Follow [Getting started](../getting-started.md). Save the program as `concatenation_lesson.py` in the repository root and run:

~~~sh
uv run --project python python concatenation_lesson.py
~~~

Success prints `concatenation checks passed`. The program uses the existing compiler and evaluator; the hand-built graphs are explanatory data.

## 1. Predict the seam

The postfix tokens for `a.b` are `a b .`. The builder first creates two disjoint literal fragments, then joins them:

**Read the figure:** Follow left to right: consume `a`, cross the free `ε` seam, then consume `b`. Double circles mark accepting states.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Concatenation: a then b, scrollable diagram" style="--diagram-width: 747px">
  <img class="diagram" src="/JAutomata/diagrams/concatenation.svg" alt="Start 0 consumes a to 1, follows epsilon to 2, then consumes b to accepting state 3.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/concatenation.svg">Open full-size diagram</a></p>

Predict which state set is possible just after consuming `a`. It includes both sides of the epsilon link, but not the final state.

| Word | Prediction | Reason |
| --- | --- | --- |
| `ab` | accept | left word then right word |
| `a` | reject | right word is still missing |
| `ba` | reject | the operands were reversed in the input |
| `a.b` | reject | the dot is regex syntax, not an input edge |

## 2. Run the complete experiment

~~~python
from jautomata import accepts, compile_regex, epsilon_closure
from jautomata.model import Automaton, Transition
from jautomata.regex import to_postfix

nfa = compile_regex("a.b")
assert to_postfix("a.b") == ("a", "b", ".")
assert nfa.states == frozenset({0, 1, 2, 3})
assert nfa.start_state == 0
assert nfa.final_states == frozenset({3})
assert nfa.transitions == frozenset({
    Transition(0, "a", 1),
    Transition(1, None, 2),
    Transition(2, "b", 3),
})
initial = epsilon_closure(nfa, {nfa.start_state})
assert initial == frozenset({0})
after_a = epsilon_closure(nfa, {
    edge.target for edge in nfa.transitions
    if edge.source in initial and edge.symbol == "a"
})
assert after_a == frozenset({1, 2})
after_ab = epsilon_closure(nfa, {
    edge.target for edge in nfa.transitions
    if edge.source in after_a and edge.symbol == "b"
})
assert after_ab == frozenset({3})

# A hand-built illustration of fusing ONLY the two clean boundary states.
fused_literal_pair = Automaton(
    states={0, 1, 3}, start_state=0, final_states={3},
    transitions={Transition(0, "a", 1), Transition(1, "b", 3)},
)
cases = {
    "": False, "a": False, "b": False, "ab": True,
    "ba": False, "aab": False, "aba": False, "a.b": False,
}
for word, expected in cases.items():
    assert accepts(nfa, word) == expected, word
    assert accepts(fused_literal_pair, word) == expected, word
assert nfa != fused_literal_pair

# General endpoints with loops violate the clean-boundary assumptions.
# The link preserves the order: a, then zero or more b,
# then zero or more d, then c.
linked_general = Automaton(
    states={0, 1, 2, 3}, start_state=0, final_states={3},
    transitions={
        Transition(0, "a", 1), Transition(1, "b", 1),
        Transition(1, None, 2), Transition(2, "d", 2),
        Transition(2, "c", 3),
    },
)
fused_general = Automaton(
    states={0, 1, 3}, start_state=0, final_states={3},
    transitions={
        Transition(0, "a", 1), Transition(1, "b", 1),
        Transition(1, "d", 1), Transition(1, "c", 3),
    },
)
for word in ("ac", "abc", "adc", "abdc"):
    assert accepts(linked_general, word)
    assert accepts(fused_general, word)
assert not accepts(linked_general, "adbc")
assert accepts(fused_general, "adbc")  # Fusion introduced a new word.

nullable_left = compile_regex("a*.b")
assert accepts(nullable_left, "b")
assert accepts(nullable_left, "aab")
assert not accepts(nullable_left, "")
assert not accepts(nullable_left, "ba")

print("concatenation checks passed")
~~~

Expected output:

~~~text
concatenation checks passed
~~~

## 3. Interpret the first trace

The program performs one consuming move and then calls the delivered `epsilon_closure`. It exposes intermediate sets for inspection; `accepts` remains the complete recognizer.

| Prefix | Closed active set | Why it matters |
| --- | --- | --- |
| empty | `{0}` | no empty-word acceptance |
| `a` | `{1, 2}` | the seam consumes nothing |
| `ab` | `{3}` | the entire input is consumed at the only final |

The former left exit `1` is no longer final in the completed machine. Otherwise `a` would be accepted even though the right operand was never completed.

The three-state literal illustration recognizes the same language: its only successful path still consumes `ab`. It is not the graph returned by `compile_regex`; the compiler intentionally retains the epsilon connector.

## 4. Explain the unsafe-fusion counterexample

The general linked graph has a `b` loop at the left exit and a `d` loop at the right entry. These endpoints violate the ordinary Thompson boundary assumptions. Before crossing the seam, the graph can consume `b` characters. After crossing, it can consume `d` characters, but cannot return to consume another `b`.

| Graph | Trace of `adbc` | Result |
| --- | --- | --- |
| Linked | `a` reaches `1`; cross to `2`; `d` stays at `2`; no `b` edge | reject |
| Fused | `a` reaches seam `1`; `d` and `b` both loop there; `c` reaches `3` | accept |

Fusion has combined loops that were previously available in only one order. This is one counterexample to a general merging rule. It does not invalidate fusion at disjoint, clean Thompson endpoints with the appropriate outer final state.

## 5. Predict, then reveal

**Exercise A:** Change the compiled expression to `b.a`. What happens to `ab`, `ba`, and the two consuming edge labels?

<details>
<summary>Reveal the answer and reason</summary>

`ab` rejects and `ba` accepts. The first edge is now `0 --b--> 1`, the epsilon seam remains `1 --ε--> 2`, and the second edge becomes `2 --a--> 3`. The fragment count and number of edges stay the same. Update every affected assertion when trying this variation.

</details>

**Exercise B:** Why does `a*.b` accept `b` but reject the empty word?

<details>
<summary>Reveal the answer and reason</summary>

Its left operand can contribute the empty word through the star's bypass. Concatenation can then move directly into the right literal. That literal still requires `b`, so the completed expression is not nullable. An epsilon connector does not make either operand optional by itself.

</details>

## Common mistakes and checks

- Preserve operand order when reading a postfix stack: pop right, then left.
- Do not infer language equivalence from equal state counts or a few passing fixtures. The simple literal graphs have a path argument; the general graphs have a witnessed disagreement.
- The fusion example is hand-built. It does not mutate or test the historical Java evaluator.

## Source evidence

**Original commentary and implementation:** [Java concatenation variants, lines 87–117](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L87-L117), show the available link and fusion strategies.

**Verified behavior:** [Python policy, lines 1–10](../../python/src/jautomata/thompson.py#L1-L10), chooses epsilon links; [the constructor, lines 65–70](../../python/src/jautomata/thompson.py#L65-L70), pops operands in order and joins their boundaries.

**Supplement:** The safe three-state illustration, the loop counterexample, and the path reasoning are explanatory additions, not claims of a new Java runtime reproduction. See the [source curriculum](../reference/source-curriculum.md).

## Recap and stop/resume cue

You inspected the exact connector and witnessed both a safe explanatory fusion and an unsafe general merge.

**Stop:** Save the `{1, 2}` seam trace and the word `adbc` that exposes the counterexample. **Resume:** Open the [union tutorial](union.md) to build alternative routes instead of a sequence.
