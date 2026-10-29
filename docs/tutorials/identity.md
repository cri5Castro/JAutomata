# Tutorial: test identity without confusing it with language

**Goal:** observe caller isolation, duplicate collapse, value equality and consistent state renaming in one runnable program.

**Prerequisites:** [identity theory](../theory/identity.md), [automata](../theory/automata.md) and basic Python sets. This lesson explains why a reusable machine remains stable when the collections used to create it change.

**Setup:** follow [Getting started](../getting-started.md). Save the complete program below as `identity_demo.py` in the repository root, then run:

~~~sh
uv run --project python python identity_demo.py
~~~

## Predict and trace

We construct a two-state machine accepting exactly `a`. We supply the same transition twice, then clear the original collections. Next we compare two compiler results and a relabeled graph.

| Step | Prediction to make |
| --- | --- |
| Duplicate equal edges enter a frozen set | One edge or two? |
| Original caller sets are cleared | Does the stored machine disappear? |
| `a = compile_regex("a")`, then another compilation | Same object? Same value? |
| Every ID is increased by 10 | Same value? Same accepted words? |

## Run the complete program

~~~python
from dataclasses import FrozenInstanceError
from itertools import product
from jautomata import accepts, compile_regex
from jautomata.model import Automaton, Transition

states = {0, 1}
finals = {1}
edges = [Transition(0, "a", 1), Transition(0, "a", 1)]
machine = Automaton(states, 0, finals, edges)
alias = machine
assert alias is machine
assert len(machine.transitions) == 1
assert isinstance(machine.states, frozenset)

# Caller-owned containers are independent of the normalized graph.
states.clear()
finals.clear()
edges.clear()
assert machine.states == frozenset({0, 1})
assert machine.final_states == frozenset({1})
assert accepts(machine, "a")
assert not accepts(machine, "")
assert not accepts(machine, "aa")

try:
    machine.start_state = 1
except FrozenInstanceError:
    pass
else:
    raise AssertionError("Automaton should be frozen")

first = compile_regex("a")
second = compile_regex("a")
assert first is not second
assert first == second == machine
assert hash(first) == hash(second)
assert {first: "stored"}[second] == "stored"
assert len({frozenset({0, 1}), frozenset({1, 0})}) == 1

# Relabel every occurrence of every state ID, including start and finals.
rename = {state: state + 10 for state in machine.states}
renamed = Automaton(
    states={rename[state] for state in machine.states},
    start_state=rename[machine.start_state],
    final_states={rename[state] for state in machine.final_states},
    transitions={
        Transition(rename[edge.source], edge.symbol, rename[edge.target])
        for edge in machine.transitions
    },
)
assert machine != renamed
assert renamed.start_state == 10
assert renamed.final_states == frozenset({11})

checked = 0
for length in range(4):
    for letters in product("ab", repeat=length):
        word = "".join(letters)
        expected = word == "a"
        assert accepts(machine, word) is expected
        assert accepts(renamed, word) is expected
        checked += 1
assert checked == 15

print("stored states:", sorted(machine.states))
print("stored transitions:", len(machine.transitions))
print("same object:", first is second)
print("equal values:", first == second)
print("relabeled equal value:", machine == renamed)
print("words checked:", checked)
~~~

Expected output:

~~~text
stored states: [0, 1]
stored transitions: 1
same object: False
equal values: True
relabeled equal value: False
words checked: 15
~~~

## Interpret the results

Normalization preserves the **values** supplied at construction. It does not retain a live view into the caller's mutable collections. Duplicate edges disappear because a transition is a value containing source, symbol and target. Changing any of those fields describes a different transition.

The two compiler calls use separate builders, each starting its local numbering at zero. Matching numbers make their stored graphs equal, while `is` remains false. The renamed graph fails value equality because its stored IDs differ.

The 15 tests cover all words over `{a, b}` of lengths 0 through 3: `1 + 2 + 4 + 8`. They give bounded evidence. The stronger equivalence argument is that the renaming is a bijection preserving every edge label, the start and finality, so every complete path has a matching path.

## Exercise: which changes preserve the language?

Predict the effect of these edits separately: add another identical edge; add a `b` edge from start to final; rename only the start to 10.

<details>
<summary>Answer and reason</summary>

The identical edge collapses and changes nothing. The new `b` edge makes `b` accepted, changing the language. Renaming only the start to 10 while leaving states `{0, 1}` raises `ValueError`; a valid relabeling must update every relevant field consistently. If state 10 were added without its corresponding edges, the graph would be valid but its language would change.

</details>

**Common mistake:** assuming equal hashes prove equal graphs. Hash collisions are allowed; dictionary lookup combines hash and equality. Another is merging separately compiled graphs without renaming colliding IDs first.

## Source connection

**Commentary:** the [historical copy helpers](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L188-L221) discuss copying but share existing mutable objects. The [name-only equality note](../../src/Model/AutomataStructure/Estado.java#L172-L175) is a historical design comment, not a language-equivalence definition.

**Verified behavior:** [frozen transition values](../../python/src/jautomata/model.py#L34-L64), [normalization](../../python/src/jautomata/model.py#L101-L125), and [new compiler builder](../../python/src/jautomata/thompson.py#L123-L130) support the assertions above. **Supplement:** the relabeling construction and finite test set are teaching examples added here.

## Recap and stop point

The graph survives caller edits; identical edges collapse; independent compilations can be equal; renamed graphs can accept the same words without being equal.

**Stop here:** explain each of the three Boolean output lines. **Resume:** read [pure execution](../theory/pure-execution.md) to see why traversal state also needs clear ownership.
