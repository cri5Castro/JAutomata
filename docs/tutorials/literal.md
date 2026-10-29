# Tutorial: inspect a literal fragment

**Objective:** Check the exact two-state graph for a literal and explain why a differently numbered graph can accept the same words.

**Prerequisites:** [Literal theory](../theory/literal.md), [automata notation](../theory/automata.md), and [regex syntax](../theory/regex.md). If postfix order is unfamiliar, read [parsing](../theory/parsing.md).

**Setup:** Follow [Getting started](../getting-started.md). Save the complete program below as `literal_lesson.py` in the repository root, then run:

~~~sh
uv run --project python python literal_lesson.py
~~~

The program has no interactive input. Successful execution prints `literal checks passed`; a failed prediction encoded as an assertion raises `AssertionError`.

## 1. Predict the graph

Before running, sketch a machine for the expression `a`. It must accept only the whole word `a`. Use this checklist:

| Item | Your prediction |
| --- | --- |
| Number of states | two |
| Number of transitions | one |
| Edge label | the consuming character `a` |
| Empty input | reject |
| Two `a` characters | reject |

The current allocator starts at `0`, so this compilation produces `0 --a--> 1`. State `0` is the entry/start and `1` is the exit/final. Exact IDs are a way to inspect this implementation; acceptance does not depend on those particular numbers.

**Read the figure:** Follow the single `a` arrow from the start to the double-circle final state.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="One literal, two states, scrollable diagram" style="--diagram-width: 443px">
  <img class="diagram" src="/JAutomata/diagrams/literal.svg" alt="Start state 0 consumes one a to reach double-circle accepting state 1.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/literal.svg">Open full-size diagram</a></p>

## 2. Run the complete experiment

~~~python
from jautomata import accepts, compile_regex, epsilon_closure
from jautomata.model import Automaton, Transition

literal = compile_regex("a")
assert literal.states == frozenset({0, 1})
assert literal.start_state == 0
assert literal.final_states == frozenset({1})
assert literal.transitions == frozenset({Transition(0, "a", 1)})
assert literal.alphabet == frozenset({"a"})
assert epsilon_closure(literal, {0}) == frozenset({0})
assert epsilon_closure(literal, {1}) == frozenset({1})

# The same single-edge topology with different, independently chosen IDs.
hand_built = Automaton(
    states={10, 20},
    start_state=10,
    final_states={20},
    transitions={Transition(10, "a", 20)},
)
cases = {"": False, "a": True, "b": False, "aa": False, "ab": False}
for word, expected in cases.items():
    assert accepts(literal, word) == expected, word
    assert accepts(hand_built, word) == expected, word
assert literal != hand_built  # Graph values include the state IDs.

# A fresh compilation has its own allocator; numbering may restart at zero.
another = compile_regex("a")
assert another == literal
assert another is not literal

# Two occurrences inside ONE compilation must remain distinct fragments.
two_occurrences = compile_regex("a.a")
assert two_occurrences.states == frozenset({0, 1, 2, 3})
assert two_occurrences.transitions == frozenset({
    Transition(0, "a", 1),
    Transition(1, None, 2),
    Transition(2, "a", 3),
})
assert not accepts(two_occurrences, "a")
assert accepts(two_occurrences, "aa")

# A non-ASCII literal still labels one consuming edge.
unicode_literal = compile_regex("λ")
assert unicode_literal.transitions == frozenset({Transition(0, "λ", 1)})
assert accepts(unicode_literal, "λ")
assert not accepts(unicode_literal, "")
assert not accepts(unicode_literal, "λλ")

print("literal checks passed")
~~~

Expected output:

~~~text
literal checks passed
~~~

## 3. Trace what the assertions mean

The closure checks demonstrate that neither state has a non-consuming way to reach the other. The consuming edge is necessary.

| Word | State after the first step | What remains? | Result |
| --- | --- | --- | --- |
| `""` | start `0` | no input, but `0` is not final | reject |
| `"a"` | `1` | no input, and `1` is final | accept |
| `"aa"` | `1` after the first `a` | another `a`, with no outgoing edge | reject |

The manually built graph uses `10` and `20` for the same roles. Both graphs have exactly one start-to-final path consuming `a`, which explains language equivalence for all words. The five fixtures check concrete cases; the path argument supplies the general reasoning.

The two `a` occurrences in `a.a` instead occupy four distinct states. The edge labelled `None` is the epsilon connector introduced by [concatenation](../theory/concatenation.md). It is not another literal `a` and does not consume input.

## 4. Predict, then reveal

**Exercise A:** Replace both the compiled literal and the hand-built edge label with `λ`. Which expectations in `cases` need to change?

<details>
<summary>Reveal the answer and reason</summary>

Add `"λ": True` and make `"a": False`; the empty word and every two-character word still reject. Also update the structural assertions for the compiled edge and alphabet. State IDs and the two-state shape stay the same because only the literal value changed. The final section of the program already checks the Unicode version independently.

</details>

**Exercise B:** Suppose you add the start state to `literal.final_states` when constructing an alternative graph. Does its language remain `{a}`?

<details>
<summary>Reveal the answer and reason</summary>

No. Making the start final adds the empty word to the language. The existing `a` edge still accepts `a`, so the language becomes `{ε, a}`. No loop was added, so `aa` would still reject. Construct a new `Automaton` to explore this: the delivered model's collections are immutable.

</details>

## Common mistakes and checks

- If an assertion comparing edges fails, inspect `source`, `symbol`, and `target` separately. `Transition(0, "a", 1)` consumes `a`; `Transition(0, None, 1)` consumes nothing.
- Fresh states mean disjoint fragments within one construction. Two independently compiled machines may have equal values and the same ID numbers.
- One final state is a Thompson-fragment convention. It does not limit every hand-built automaton to one final state.

## Source evidence

**Original commentary:** [Java's basic-construction comment and body, lines 64–84](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L64-L84), describe one character and unique state names. The comment's counter parameter is absent from the actual method signature.

**Verified behavior:** [Python allocation, lines 37–42](../../python/src/jautomata/thompson.py#L37-L42), and [literal construction, lines 56–63](../../python/src/jautomata/thompson.py#L56-L63), explain the exact IDs and edge asserted here. [Final graph assembly, lines 123–130](../../python/src/jautomata/thompson.py#L123-L130), makes the fragment exit the single final state.

**Supplement:** Renumbering the hand-built graph, the prediction exercises, and the path argument are teaching examples. They extend the [source curriculum](../reference/source-curriculum.md) without changing runtime behavior.

## Recap and stop/resume cue

You checked topology, whole-string acceptance, fresh allocation, and a differently numbered equivalent graph.

**Stop:** Keep the two-state drawing and the reason `aa` rejects. **Resume:** Open the [concatenation tutorial](concatenation.md) and connect two independently allocated literal fragments.
