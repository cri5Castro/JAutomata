# Tutorial: inspect bypasses and repetition

**Objective:** Verify `a*` edge by edge, then trace a nested star with an epsilon-only cycle.

**Prerequisites:** [Literal](literal.md), [concatenation](concatenation.md), and [union](union.md) tutorials, plus [star theory](../theory/kleene-star.md).

**Setup:** Follow [Getting started](../getting-started.md). Save the complete program as `kleene_star_lesson.py` in the repository root and run:

~~~sh
uv run --project python python kleene_star_lesson.py
~~~

Successful execution prints `star checks passed`. The program calls the delivered cycle-safe closure and recognizer rather than introducing a separate evaluator.

## 1. Predict zero, one, and many

The compiler builds the literal `0 --a--> 1`, then wraps it with entry `2` and exit `3`. Label the four epsilon edges by purpose:

| Edge | Purpose |
| --- | --- |
| `2 → 0` | enter |
| `2 → 3` | bypass |
| `1 → 0` | repeat |
| `1 → 3` | finish |

Before running, predict whether the initial epsilon closure contains final state `3`. Then predict what changes after reading one `a`.

## 2. Run the complete experiment

~~~python
from jautomata import accepts, compile_regex, epsilon_closure
from jautomata.model import Transition

star = compile_regex("a*")
assert star.states == frozenset({0, 1, 2, 3})
assert star.start_state == 2
assert star.final_states == frozenset({3})
assert star.transitions == frozenset({
    Transition(0, "a", 1),
    Transition(2, None, 0), Transition(2, None, 3),
    Transition(1, None, 0), Transition(1, None, 3),
})
initial = epsilon_closure(star, {star.start_state})
assert initial == frozenset({0, 2, 3})
after_a = epsilon_closure(star, {
    edge.target for edge in star.transitions
    if edge.source in initial and edge.symbol == "a"
})
assert after_a == frozenset({0, 1, 3})
after_aa = epsilon_closure(star, {
    edge.target for edge in star.transitions
    if edge.source in after_a and edge.symbol == "a"
})
assert after_aa == after_a

cases = {
    "": True, "a": True, "aa": True, "aaaa": True,
    "b": False, "aab": False, "ba": False,
}
for word, expected in cases.items():
    assert accepts(star, word) == expected, word

block_star = compile_regex("(a.b)*")
for word, expected in {
    "": True, "ab": True, "abab": True,
    "a": False, "b": False, "aba": False, "abb": False,
}.items():
    assert accepts(block_star, word) == expected, word

# The inner star is the operand of the outer star.
nested = compile_regex("(a*)*")
assert nested.states == frozenset(range(6))
assert nested.start_state == 4
assert nested.final_states == frozenset({5})
assert nested.transitions == star.transitions | frozenset({
    Transition(4, None, 2), Transition(4, None, 5),
    Transition(3, None, 2), Transition(3, None, 5),
})
# The inner bypass and outer repeat edge form an epsilon-only cycle.
assert Transition(2, None, 3) in nested.transitions
assert Transition(3, None, 2) in nested.transitions
nested_initial = epsilon_closure(nested, {nested.start_state})
assert nested_initial == frozenset({0, 2, 3, 4, 5})
assert epsilon_closure(nested, nested_initial) == nested_initial
nested_after_a = epsilon_closure(nested, {
    edge.target for edge in nested.transitions
    if edge.source in nested_initial and edge.symbol == "a"
})
assert nested_after_a == frozenset({0, 1, 2, 3, 5})
for word, expected in cases.items():
    assert accepts(nested, word) == expected, word

print("star checks passed")
~~~

Expected output:

~~~text
star checks passed
~~~

## 3. Interpret the repetition trace

| Prefix in `a*` | Closed active set | Available choices |
| --- | --- | --- |
| empty | `{0, 2, 3}` | accept now through bypass, or consume `a` |
| `a` | `{0, 1, 3}` | accept now through exit, or repeat |
| `aa` | `{0, 1, 3}` | the same choices after another whole operand |

Reaching the same set after another `a` describes repeatable behavior; it does not mean the input failed to advance. The consuming edge processed one character each time.

For `(a.b)*`, returning to the repeat point takes two consumed characters. The fixtures rejecting `a` and `aba` test that the machine cannot finish halfway through a block.

## 4. Trace the epsilon cycle once

The nested graph contains `2 --ε--> 3 --ε--> 2`. Starting from `4`, an example exploration goes as follows; actual set iteration order is not significant:

| Newly inspected state | Epsilon destinations | Newly discovered states |
| --- | --- | --- |
| `4` | `2`, `5` | `2`, `5` |
| `2` | `0`, `3` | `0`, `3` |
| `3` | `2`, `5` | none: both already known |
| `0` and `5` | none | none |

The reachable set is `{0, 2, 3, 4, 5}`. The non-consuming cycle can be walked indefinitely, but it never adds another state. The visited-set algorithm stops after the finite reachable states have been processed. Closing the already closed set returns it unchanged, which the program also checks.

These fixtures support the expected behavior on the listed words. The argument that `(L*)* = L*` in [star theory](../theory/kleene-star.md) explains the language relationship beyond finite testing.

## 5. Predict, then reveal

**Exercise A:** Why is `1` missing from the initial closure of `(a*)*` even though final `5` is present?

<details>
<summary>Reveal the answer and reason</summary>

Reaching `1` requires the consuming edge `0 --a--> 1`. Epsilon closure follows only non-consuming edges, so it cannot cross that edge. Final `5` is reachable through the outer bypass or through the inner empty route. Finality and numeric order do not determine reachability.

</details>

**Exercise B:** If the operand changes from `a` to `a.b`, does the star still accept empty input? Does it accept `ababab`?

<details>
<summary>Reveal the answer and reason</summary>

Yes to both. The wrapper bypass does not depend on the operand, so zero repetitions still accepts. `ababab` consists of three complete `ab` words, so the repeat edge joins three successful operand traversals. The word `ababa` would stop before the third traversal's `b` and reject.

</details>

## Common mistakes and checks

- Count five total transitions for `a*`: one consuming edge plus four epsilon edges.
- The diagram's `ε` corresponds to `None`, not the empty Python string as a transition label.
- Do not use the historical unguarded recursive closure to run the cycle example. The Python API's visited work list is the verified execution path.

## Source evidence

**Original commentary:** [Java Kleene closure, lines 165–186](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L165-L186), describes the star operation.

**Verified behavior:** [Python wrapper, lines 84–92](../../python/src/jautomata/thompson.py#L84-L92), supplies the repeat and bypass edges. [Closure's visited work list, lines 67–77](../../python/src/jautomata/simulation.py#L67-L77), explains termination for the nested cycle.

**Supplement:** The block fixtures, illustrative exploration order, and exact state-set traces are teaching experiments. See the [source curriculum](../reference/source-curriculum.md) for their relationship to the historical sources.

## Recap and stop/resume cue

You verified the bypass, repeat edge, grouped-word repetition, and finite closure of a graph with an epsilon-only cycle.

**Stop:** Identify which edge admits zero repetitions and which admits another repetition. **Resume:** Open the [positive-closure tutorial](positive-closure.md) and remove only the outer bypass.
