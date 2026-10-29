# Tutorial: keep both alternatives

**Objective:** Verify the four epsilon edges of `a|b`, then test grouping and alternatives with the same first character.

**Prerequisites:** [Literal tutorial](literal.md), [concatenation tutorial](concatenation.md), and [union theory](../theory/union.md).

**Setup:** Follow [Getting started](../getting-started.md). Save this program as `union_lesson.py` in the repository root and run:

~~~sh
uv run --project python python union_lesson.py
~~~

Successful execution prints `union checks passed` after all structural and language assertions.

## 1. Predict the split and join

For `a|b`, the literal fragments use `0, 1` and `2, 3`. The union wrapper allocates fresh states `4, 5`. Fill in the four epsilon edges before reading the assertions:

**Read the figure:** From start `4`, follow either literal branch to the shared double-circle final `5`. Count four `ε` edges.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Union: split into alternatives, then join, scrollable diagram" style="--diagram-width: 745px">
  <img class="diagram" src="/JAutomata/diagrams/union.svg" alt="Start 4 splits by epsilon to 0 and 2; a takes 0 to 1 and b takes 2 to 3; both exits join final 5 by epsilon.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/union.svg">Open full-size diagram</a></p>

| Role | Edge |
| --- | --- |
| Enter left | `4 --ε--> 0` |
| Enter right | `4 --ε--> 2` |
| Leave left | `1 --ε--> 5` |
| Leave right | `3 --ε--> 5` |

There is no `4 --ε--> 5` bypass. Neither literal is nullable, so the empty word should reject.

## 2. Run the complete experiment

~~~python
from jautomata import accepts, compile_regex, epsilon_closure
from jautomata.model import Transition

choice = compile_regex("a|b")
assert choice.states == frozenset(range(6))
assert choice.start_state == 4
assert choice.final_states == frozenset({5})
assert choice.transitions == frozenset({
    Transition(0, "a", 1), Transition(2, "b", 3),
    Transition(4, None, 0), Transition(4, None, 2),
    Transition(1, None, 5), Transition(3, None, 5),
})
initial = epsilon_closure(choice, {choice.start_state})
assert initial == frozenset({0, 2, 4})
for symbol, expected in {"a": {1, 5}, "b": {3, 5}}.items():
    destinations = {
        edge.target for edge in choice.transitions
        if edge.source in initial and edge.symbol == symbol
    }
    assert epsilon_closure(choice, destinations) == frozenset(expected)
for word, expected in {
    "": False, "a": True, "b": True, "ab": False,
    "ba": False, "aa": False, "bb": False, "c": False,
}.items():
    assert accepts(choice, word) == expected, word

grouped = compile_regex("(a|b).c")
assert grouped.states == frozenset(range(8))
assert grouped.start_state == 4
assert grouped.final_states == frozenset({7})
assert grouped.transitions == choice.transitions | frozenset({
    Transition(5, None, 6), Transition(6, "c", 7),
})
for word, expected in {
    "ac": True, "bc": True, "": False, "a": False,
    "b": False, "c": False, "abc": False, "ca": False,
}.items():
    assert accepts(grouped, word) == expected, word

# Both alternatives begin with a; both destinations must remain possible.
shared_prefix = compile_regex("(a.b)|(a.c)")
initial_shared = epsilon_closure(shared_prefix, {shared_prefix.start_state})
assert initial_shared == frozenset({0, 4, 8})
a_destinations = {
    edge.target for edge in shared_prefix.transitions
    if edge.source in initial_shared and edge.symbol == "a"
}
assert a_destinations == {1, 5}
after_a = epsilon_closure(shared_prefix, a_destinations)
assert after_a == frozenset({1, 2, 5, 6})
assert accepts(shared_prefix, "ab")
assert accepts(shared_prefix, "ac")
assert not accepts(shared_prefix, "a")
assert not accepts(shared_prefix, "abc")

overlap = compile_regex("a|a")
assert accepts(overlap, "a")
assert not accepts(overlap, "aa")
nullable_choice = compile_regex("a*|b")
assert accepts(nullable_choice, "")
assert accepts(nullable_choice, "aaa")
assert accepts(nullable_choice, "b")
assert not accepts(nullable_choice, "ab")

print("union checks passed")
~~~

Expected output:

~~~text
union checks passed
~~~

## 3. Interpret the state sets

At the start of `a|b`, the set `{0, 2, 4}` includes both literal entries. After an `a`, only the left route has consumed a character; the epsilon join reaches final state `5`. A separate run on `b` reaches it through the right route.

The shared-prefix graph is more revealing:

| Prefix | Active states after epsilon moves | Next useful character |
| --- | --- | --- |
| empty | `{0, 4, 8}` | `a` from either branch |
| `a` | `{1, 2, 5, 6}` | `b` from `2`, or `c` from `6` |
| `ab` | `{3, 9}` | none; final `9` is reached |
| `ac` | `{7, 9}` | none; final `9` is reached |

The last two rows describe different continuations of the same prefix. Tracking only one `a` destination would incorrectly reject one of them. Tracking both is a set calculation; it does not require parallel threads.

For `(a|b).c`, the union's former exit `5` leads to the `c` fragment. It is no longer final in the completed machine. That is why the grouped graph rejects `a` and `b` by themselves.

## 4. Predict, then reveal

**Exercise A:** What changes if the expression is `a|b.c` without parentheses?

<details>
<summary>Reveal the answer and reason</summary>

Concatenation binds more tightly than union, so this means `a|(b.c)`. It accepts `a` and `bc`, while `(a|b).c` accepts `ac` and `bc`. The wrapper now surrounds a literal on the left and a concatenation on the right. If precedence is unclear, revisit the [parsing lesson](../theory/parsing.md) before changing the assertions.

</details>

**Exercise B:** Does `a|a` need to consume one `a` for each branch before it can accept?

<details>
<summary>Reveal the answer and reason</summary>

No. Acceptance requires one complete successful path. Both paths consume the same one-character word, so the language still contains only `a`. The two branches are alternatives, and no edge connects their literal transitions sequentially.

</details>

**Exercise C:** Why does `a*|b` accept empty input if the union wrapper has no bypass?

<details>
<summary>Reveal the answer and reason</summary>

Its left operand `a*` contains its own empty route. The union enters that operand, follows its bypass, and exits to the wrapper's final state. A nullable operand makes the union nullable even without a direct wrapper bypass.

</details>

## Common mistakes and checks

- Count four epsilon edges in the simple union: two entries and two exits. The two consuming edges make six transitions in total.
- Distinguish the start state from the smallest ID. The compiler allocates the wrapper after its operands.
- Never select only the first matching transition. The two `a` destinations are the central check in the shared-prefix example.

## Source evidence

**Original commentary:** [Java union, lines 119–143](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L119-L143), describes joining two operand automata.

**Verified behavior:** [Python union, lines 72–82](../../python/src/jautomata/thompson.py#L72-L82), allocates the wrapper and all four epsilon edges. [The recognition loop, lines 143–153](../../python/src/jautomata/simulation.py#L143-L153), retains all matching destinations before taking epsilon closure.

**Supplement:** The shared-prefix fixtures and state table explain nondeterministic possibilities. The [source curriculum](../reference/source-curriculum.md) records the evidence boundary.

## Recap and stop/resume cue

You verified the exact union topology, its interaction with concatenation, and the need to retain alternatives after a shared prefix.

**Stop:** Keep the two possible destinations after `a` in `(a.b)|(a.c)`. **Resume:** Open the [star tutorial](kleene-star.md), where a finished operand can either repeat or exit.
