# Tutorial: one repetition can consume nothing

**Objective:** Compare the exact graphs for `a+`, `a*`, and `(a*)+`, then explain their empty-input behavior from actual paths.

**Prerequisites:** [Star tutorial](kleene-star.md) and [positive-closure theory](../theory/positive-closure.md).

**Setup:** Follow [Getting started](../getting-started.md). Save this complete program as `positive_closure_lesson.py` in the repository root and run:

~~~sh
uv run --project python python positive_closure_lesson.py
~~~

Successful execution prints `positive closure checks passed` after all assertions.

## 1. Predict the three cases

For each expression, ask two separate questions: does its outer wrapper have a bypass, and can its operand itself consume an empty word?

| Expression | Outer bypass? | Operand nullable? | Empty input? |
| --- | --- | --- | --- |
| `a+` | no | no | reject |
| `a*` | yes | no | accept |
| `(a*)+` | no | yes | accept |

“Nullable” means accepting the empty word. The third row is the main experiment: one traversal of the inner star can consume zero characters.

## 2. Run the complete experiment

~~~python
from jautomata import accepts, compile_regex, epsilon_closure
from jautomata.model import Transition

plus = compile_regex("a+")
assert plus.states == frozenset({0, 1, 2, 3})
assert plus.start_state == 2
assert plus.final_states == frozenset({3})
assert plus.transitions == frozenset({
    Transition(0, "a", 1), Transition(2, None, 0),
    Transition(1, None, 0), Transition(1, None, 3),
})
star = compile_regex("a*")
assert star.transitions - plus.transitions == frozenset({Transition(2, None, 3)})
assert plus.transitions - star.transitions == frozenset()
assert epsilon_closure(plus, {2}) == frozenset({0, 2})
assert epsilon_closure(star, {2}) == frozenset({0, 2, 3})
assert epsilon_closure(plus, {1}) == frozenset({0, 1, 3})

nullable_plus = compile_regex("(a*)+")
assert nullable_plus.states == frozenset(range(6))
assert nullable_plus.start_state == 4
assert nullable_plus.final_states == frozenset({5})
assert nullable_plus.transitions == star.transitions | frozenset({
    Transition(4, None, 2), Transition(3, None, 2),
    Transition(3, None, 5),
})
assert Transition(4, None, 5) not in nullable_plus.transitions
# An indirect empty path still crosses the operand from entry to exit.
empty_path = (
    Transition(4, None, 2),
    Transition(2, None, 3),
    Transition(3, None, 5),
)
assert all(edge in nullable_plus.transitions for edge in empty_path)
assert epsilon_closure(nullable_plus, {4}) == frozenset({0, 2, 3, 4, 5})

cases = {
    "": (False, True, True),
    "a": (True, True, True),
    "aa": (True, True, True),
    "aaaa": (True, True, True),
    "b": (False, False, False),
    "ab": (False, False, False),
}
machines = (plus, star, nullable_plus)
for word, expected_results in cases.items():
    actual = tuple(accepts(machine, word) for machine in machines)
    assert actual == expected_results, (word, actual)

block_plus = compile_regex("(a.b)+")
for word, expected in {
    "": False, "ab": True, "abab": True,
    "a": False, "b": False, "aba": False, "abb": False,
}.items():
    assert accepts(block_plus, word) == expected, word

# At the language level, one-or-more equals one followed by zero-or-more.
expanded = compile_regex("a.a*")
assert len(plus.states) == 4
assert len(expanded.states) == 6
assert plus != expanded
for word in cases:
    assert accepts(plus, word) == accepts(expanded, word), word

print("positive closure checks passed")
~~~

Expected output:

~~~text
positive closure checks passed
~~~

## 3. Interpret the direct edge comparison

For `a+` and `a*`, both compilers happen to allocate the same operand and wrapper IDs. Subtracting the transition sets isolates a single difference: `2 --ε--> 3` exists only in star. Both graphs retain the enter, repeat, and finish edges.

The initial closure of `a+` is `{0, 2}` and excludes final state `3`. After the first `a`, the destination is `1`; its closure `{0, 1, 3}` makes both another traversal and successful completion possible.

This explains why `a+` rejects only the zero-length all-`a` word while accepting all positive lengths. The rejected `b` and `ab` fixtures also check that repetition does not admit unrelated characters.

## 4. Trace one empty operand word

The absence of the direct outer bypass in `(a*)+` is an explicit assertion. The program then verifies each edge in this alternative path:

| Step | Edge | Meaning | Characters consumed |
| --- | --- | --- | --- |
| 1 | `4 --ε--> 2` | enter the inner star operand | zero |
| 2 | `2 --ε--> 3` | finish one inner-star word via its bypass | zero |
| 3 | `3 --ε--> 5` | leave the outer plus | zero |

The result satisfies both requirements: at least one operand word was completed, and all input was consumed. The word chosen from the operand language was empty.

The return edge `3 --ε--> 2` also permits another empty traversal. The closure algorithm records reachable states once, so the cycle does not force unbounded execution. Read [epsilon closure](../theory/epsilon-closure.md) next for the work-list invariant.

## 5. Predict, then reveal

**Exercise A:** Does `(a+)*` accept empty input for the same immediate reason as `(a*)+`?

<details>
<summary>Reveal the answer and reason</summary>

Both accept, but their immediate empty paths differ. `(a+)*` has an outer star bypass and can skip its non-nullable operand. `(a*)+` has no outer bypass; it enters its nullable inner star, completes that operand's empty word, and exits. Tracing the graph distinguishes the reasons.

</details>

**Exercise B:** Why is the six-state graph for `a.a*` different from the four-state graph for `a+` if the languages agree?

<details>
<summary>Reveal the answer and reason</summary>

The expanded expression has two literal occurrences, each requiring fresh states, and one star wrapper. Concatenation adds an epsilon edge between the pieces. The dedicated plus construction reuses one operand through its repeat edge and adds only one wrapper. Graph size and graph equality do not define language equality. The listed fixtures are finite checks; the identity `L+ = LL*` supplies a general language argument.

</details>

**Exercise C:** Does `(a.b)+` accept `aba` because it has consumed at least one character?

<details>
<summary>Reveal the answer and reason</summary>

No. One repetition means one whole `ab` word. After `ab`, the extra `a` begins a second repetition but leaves its `b` unconsumed. There is no complete path accepting the entire word `aba`.

</details>

## Common mistakes and checks

- Do not replace “one or more operand words” with “at least one character.” Check operand nullability first.
- Do not search only for a direct start-to-final edge. Empty acceptance depends on all epsilon paths through the graph.
- Reusing a fragment for two occurrences in an expanded expression can break freshness. Let `compile_regex` allocate each occurrence independently.

## Source evidence

**Original commentary:** [Java positive closure, lines 144–164](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L144-L164), describes the operation. [Python's node meaning, lines 72–75](../../python/src/jautomata/regex.py#L72-L75), says one-or-more closure.

**Verified behavior:** [The shared wrapper, lines 84–92](../../python/src/jautomata/thompson.py#L84-L92), conditions only the direct bypass on `*`. The graph and path assertions above inspect that implementation.

**Supplement:** The nullable-operand reasoning, transition-set comparison, and expanded-expression example are teaching additions. Their formal language argument appears in [positive-closure theory](../theory/positive-closure.md); provenance is collected in the [source curriculum](../reference/source-curriculum.md).

## Recap and stop/resume cue

You distinguished a missing wrapper bypass from a missing empty path, and checked whole-block repetition as well as repeated characters.

**Stop:** Explain the path `4 → 2 → 3 → 5` in `(a*)+` and name the operand word it completes. **Resume:** Continue with the [epsilon-closure tutorial](epsilon-closure.md), which makes these state-set calculations explicit.
