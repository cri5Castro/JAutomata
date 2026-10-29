# Build and test a finite automaton

**Goal:** construct an immutable automaton by hand, predict its language, and check acceptance and invalid graph definitions with executable assertions.

**Prerequisites:** [Automata theory](../theory/automata.md), basic Python sets and function calls, and the environment from [Getting started](../getting-started.md).

You will use the existing `Automaton`, `Transition`, and `accepts` APIs. The program has no third-party runtime dependencies.

## 1. Predict the graph's language

~~~text
start → (0) --a--> (1) --ε--> (2) --b--> ((3))
~~~

This graph has one path from start to final. The epsilon edge contributes no character, so the path spells `ab`.

Before running anything, fill in the expected result for `""`, `a`, `ab`, `aba`, and `b`. Pay particular attention to `aba`: encountering state `3` after a prefix does not finish the input.

<details>
<summary>Reveal the prediction</summary>

Only `ab` is accepted. Empty input stops in nonfinal state `0`. Input `a` reaches `{1, 2}`, neither final. `aba` has a leftover character after reaching `3`, and no edge consumes it. Input `b` cannot leave `0`.

</details>

## 2. Save and run the complete program

From the repository root, save this block as `automata_lesson.py`. Each edge constructor takes arguments in the order **source, symbol, target**.

~~~python
from jautomata import accepts, epsilon_closure
from jautomata.model import Automaton, Transition

machine = Automaton(
    states={0, 1, 2, 3},
    start_state=0,
    final_states={3},
    transitions={
        Transition(0, "a", 1),
        Transition(1, None, 2),
        Transition(2, "b", 3),
    },
)

# A None label belongs to the graph, but not to the input alphabet.
assert machine.states == frozenset({0, 1, 2, 3})
assert machine.alphabet == frozenset({"a", "b"})
assert epsilon_closure(machine, {0}) == frozenset({0})
assert epsilon_closure(machine, {1}) == frozenset({1, 2})
assert epsilon_closure(machine, set()) == frozenset()

expected = {
    "": False,
    "a": False,
    "ab": True,
    "aba": False,
    "b": False,
    "xab": False,
}
for word, result in expected.items():
    observed = accepts(machine, word)
    assert observed is result, (word, observed, result)
    print(f"{word!r}: {observed}")

# A valid graph may have no final states: its language is empty.
empty_language = Automaton({0}, 0, set(), set())
assert not accepts(empty_language, "")
assert not accepts(empty_language, "a")

# A final start with no edges accepts exactly the empty word.
empty_word_only = Automaton({0}, 0, {0}, set())
assert accepts(empty_word_only, "")
assert not accepts(empty_word_only, "a")
assert empty_word_only.alphabet == frozenset()

# An epsilon edge can also accept empty input without a final start.
epsilon_path = Automaton({0, 1}, 0, {1}, {Transition(0, None, 1)})
assert accepts(epsilon_path, "")
assert not accepts(epsilon_path, "ε")
assert epsilon_path.alphabet == frozenset()

# The Unicode epsilon character is an ordinary consuming label.
literal_epsilon = Automaton({0, 1}, 0, {1}, {Transition(0, "ε", 1)})
assert accepts(literal_epsilon, "ε")
assert not accepts(literal_epsilon, "")
assert literal_epsilon.alphabet == frozenset({"ε"})

# Invalid graphs fail at construction, before recognition begins.
invalid_definitions = [
    ("empty state set", lambda: Automaton(set(), 0, set(), set())),
    ("missing start", lambda: Automaton({0}, 1, set(), set())),
    ("missing final", lambda: Automaton({0}, 0, {1}, set())),
    (
        "missing endpoint",
        lambda: Automaton({0}, 0, set(), {Transition(0, "a", 1)}),
    ),
    ("empty label", lambda: Transition(0, "", 1)),
    ("two-character label", lambda: Transition(0, "ab", 1)),
]
for description, build_invalid in invalid_definitions:
    try:
        build_invalid()
    except ValueError:
        pass
    else:
        raise AssertionError(f"Expected ValueError: {description}")

print("All structure and language checks passed.")
~~~

Run from the repository root:

~~~sh
uv run --project python python automata_lesson.py
~~~

Expected output:

~~~text
'': False
'a': False
'ab': True
'aba': False
'b': False
'xab': False
All structure and language checks passed.
~~~

## 3. Interpret the evidence

The alphabet assertion checks that epsilon is absent from the input vocabulary. The closure assertions show that a seed state remains reachable from itself and that the epsilon target is added. These are separate from the acceptance fixtures, which exercise complete words.

| Consumed prefix of `aba` | Active set after epsilon closure | Consequence |
| --- | --- | --- |
| `""` | `{0}` | Start before any input |
| `a` | `{1, 2}` | Both states remain possible |
| `ab` | `{3}` | A final state is active, but one character remains |
| `aba` | `∅` | No path consumes the last character; reject |

The three empty-input machines separate three claims. No finals gives an empty language. A final start with no edges gives the language `{ε}`. A nonfinal start connected by epsilon to a final state also accepts empty input. Finally, a literal `"ε"` edge requires that actual character in the word.

The invalid-definition cases check the model's contract, not the language. A rejected word is a normal `False` result from a valid machine. An invalid graph raises an exception because the requested machine is structurally inconsistent.

**Stop point:** if the program passes and you can explain why `aba` fails, you have completed the core tutorial. On return, try changing final states in the next exercise.

## 4. Change one feature at a time

**Exercise A:** keep the original graph but make state `0` final as well as state `3`. Predict the new language before constructing it.

<details>
<summary>Reveal the answer and an independently runnable check</summary>

The language is `{ε, ab}`. The new final start accepts empty input, but it creates no new transitions.

~~~python
from jautomata import accepts
from jautomata.model import Automaton, Transition

machine = Automaton(
    {0, 1, 2, 3},
    0,
    {0, 3},
    {Transition(0, "a", 1), Transition(1, None, 2), Transition(2, "b", 3)},
)
assert accepts(machine, "")
assert accepts(machine, "ab")
assert not accepts(machine, "a")
assert not accepts(machine, "aba")
~~~

This block succeeds silently.

</details>

**Exercise B:** instead of adding a final state, replace the epsilon edge with `Transition(1, "c", 2)`. What changes in the accepted word and alphabet?

<details>
<summary>Reveal the answer</summary>

The only accepted word becomes `acb`, and the alphabet becomes `{a, b, c}`. The edge now consumes one character. Input `ab` fails at its second character because state `1` requires `c` before the machine can reach the `b` edge.

</details>

**Exercise C:** replace the final-state set with an empty set. Is the graph invalid?

<details>
<summary>Reveal the answer</summary>

It remains valid and recognizes the empty language. The constructor requires a nonempty state set and valid state references; it permits zero final states.

</details>

## Mistakes to diagnose

- **`""` used as an edge label:** use `None` for epsilon. Empty input is still `""` when passed to `accepts`.
- **Only a substring seems to match:** recognition starts at the designated start and consumes the complete supplied word; it does not retry at later positions.
- **An edge points to an undeclared state:** add the state to `states` or fix the endpoint before evaluating words.
- **A loop seems to require a new state for every character:** states can be revisited. The graph's size is independent of the input's length.

## Source grounding

**Commentary:** [model.py:1–17](../../python/src/jautomata/model.py#L1-L17) explains the immutable representation and epsilon convention; [model.py:69–94](../../python/src/jautomata/model.py#L69-L94) states the invariants.

**Verified implementation:** [model.py:54–64](../../python/src/jautomata/model.py#L54-L64) checks transition labels; [model.py:102–134](../../python/src/jautomata/model.py#L102-L134) normalizes collections, checks membership, and derives the alphabet. [simulation.py:143–153](../../python/src/jautomata/simulation.py#L143-L153) computes the state sets and tests finality after the input loop.

**Supplemental explanation:** this particular graph, its language description, and the trace table are teaching examples derived from those rules. The historical Java epsilon representation differs: see [Transicion.java:12–36](../../src/Model/AutomataStructure/Transicion.java#L12-L36).

## Recap and resume

You built a recognizer, checked the whole-word rule, separated epsilon from an empty word, and tested graph validation. Passing fixtures verify those selected cases; the graph's single path explains why its entire language is `{ab}`.

**Next action:** read [Regex theory](../theory/regex.md), then use [Regex tutorial](regex.md) to describe languages with expressions instead of hand-writing every edge.
