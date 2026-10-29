# Automata: graphs that recognize languages

**Goal:** describe a finite automaton, trace whether it accepts an entire word, and distinguish the different meanings of “empty.” You will build the pictured machine in the [paired tutorial](../tutorials/automata.md).

**Prerequisites:** basic Python values and loops. This page introduces the sets, strings, and graph notation you need. No earlier theory lesson is required.

**First pass:** read through the trace, answer the prediction, then stop at the checkpoint. The formal definition is optional on your first visit.

## 1. A machine remembers its place

A finite automaton is a graph used as a recognizer. Its **states** represent possible places in a computation. Its directed **transitions** tell you where the computation can go. One state is the **start**; zero or more states are **final**, also called accepting states.

An edge labeled `a` consumes one `a` from the input. An **epsilon transition**, written `ε` in a diagram, moves without consuming any input. Python represents this edge label with `None`.

Here is a machine that accepts exactly the word `ab`:

~~~text
start → (0) --a--> (1) --ε--> (2) --b--> ((3))
~~~

Single parentheses mark ordinary states; double parentheses mark a final state. The integers are names. State `3` is not “more accepting” than state `1`; its membership in the final-state set gives it that role.

Why build such a graph? It replaces an unbounded history of input characters with a finite amount of state. More elaborate machines can recognize infinitely many words using loops, while retaining finitely many states.

## 2. Sets, alphabets, words, and languages

A **set** is a collection without ordering or duplicates. For example, `{a, b}` and `{b, a}` are the same set. We write `x ∈ S` when `x` belongs to set `S`, and `A ⊆ B` when every member of `A` belongs to `B`.

An **alphabet**, written `Σ` (sigma), is a finite set of input symbols. Our machine's alphabet is `{a, b}`. Epsilon is not an input symbol, so it is absent from this set.

A **word** or **string** is a finite ordered sequence of symbols. `ab` and `ba` are different words. A word's **length** is its number of symbols: `ab` has length 2. The **empty word**, written `ε` in mathematics and `""` in Python, has length 0.

A **language** is a set of words. This machine's language is `{ab}`: a set with one member, the two-symbol word `ab`. The notation `Σ*` means all finite words over `Σ`, including the empty word. A machine's recognized language is a subset of `Σ*`.

| Object | Example | What its members mean |
| --- | --- | --- |
| State set `Q` | `{0, 1, 2, 3}` | Places in the graph |
| Alphabet `Σ` | `{a, b}` | Characters the machine can consume |
| A word | `ab` | An ordered sequence, not a set |
| A language `L` | `{ab}` | Words the machine accepts |
| Final-state set `F` | `{3}` | States where a complete run may accept |

These definitions are supplemental mathematics. The repository implements them using integer state IDs, character labels, sets, and `Automaton` values.

## 3. Trace the entire input

In a nondeterministic automaton, several states can be possible at once. Maintain an **active set** containing every possible state after the consumed prefix, including all states reachable by epsilon edges. A **prefix** is the part of the word already read.

For each character, first follow all matching consuming transitions, then include states reachable by epsilon edges. The epsilon-reachable expansion is called **epsilon closure**; the later [epsilon-closure lesson](epsilon-closure.md) studies its algorithm.

For `ab` the trace is:

| Input consumed | Action | Active states | Is the word finished? |
| --- | --- | --- | --- |
| `""` | Start at `0`; no epsilon edge leaves it | `{0}` | No |
| `a` | Follow `0 --a--> 1`, then `1 --ε--> 2` | `{1, 2}` | No |
| `ab` | Follow `2 --b--> 3` | `{3}` | Yes: accept |

The active set contains both `1` and `2` after `a`: epsilon movement adds a possibility without requiring input. It does not delete the source state from the possibilities.

Acceptance requires **both** of these conditions:

1. Every character of the input has been consumed.
2. At least one active state is final.

Thus `a` is rejected: it finishes in `{1, 2}`, which contains no final state. `aba` is also rejected: after `ab` the machine is at `{3}`, but the remaining `a` has no matching outgoing edge, leaving the active set empty. `accepts` tests a whole word; it does not search for a matching substring.

**Predict before revealing:** does the machine accept `""`, `b`, or `xab`?

<details>
<summary>Reveal the three traces</summary>

It rejects all three. Empty input leaves the initial closure `{0}`, and `0` is not final. Input `b` has no matching edge from `0`. Input `xab` loses all paths on its first character, `x`; the later substring `ab` cannot restart the machine.

</details>

**Stop here if needed.** You can already explain the diagram and acceptance rule. On return, compare the four empty cases below, then run the tutorial.

## 4. Four different kinds of empty

The same mathematical glyph can serve related roles, but the types of objects matter.

| Concept | Notation or Python representation | Meaning |
| --- | --- | --- |
| Empty input word | `ε`, or `""` | A word containing zero characters |
| Epsilon edge | Diagram label `ε`, Python label `None` | A graph movement that consumes zero characters |
| Empty language | `∅`, represented conceptually by `set()` | A set containing no words |
| Empty active set | `∅`, or `frozenset()` | No surviving run for this input prefix |

The language `{ε}` is **not** empty: it contains one word, the empty word. A machine whose start state is final and has no edges recognizes `{ε}`. A machine with no final states recognizes the empty language, regardless of how many states it has.

An empty active set describes a particular evaluation. It does not imply the machine's whole language is empty. Our machine accepts `ab` even though its active set becomes empty while evaluating `b`.

In Python, `Transition(1, None, 2)` is an epsilon edge. `Transition(1, "", 2)` is invalid: a non-epsilon transition must carry exactly one character. The character `"ε"` is also different from `None`; it consumes a literal Greek epsilon character.

## 5. Deterministic and nondeterministic machines

An **NFA** is a nondeterministic finite automaton. Its transitions may offer multiple destinations for the same input symbol. An **epsilon-NFA** also permits epsilon edges. Acceptance means that at least one complete path succeeds; a failing branch does not veto a successful branch.

A **DFA** is a deterministic finite automaton. It has no epsilon transitions and has at most one destination for each state/symbol pair. A **complete DFA** has exactly one such destination for every state and alphabet symbol. A missing transition in an incomplete deterministic graph means rejection for that attempted move.

`Automaton` is a general graph representation; constructing one does not enforce determinism. The [subset-construction lesson](subset-construction.md) explains how the project builds a complete DFA with the same recognized language.

<details>
<summary>Optional formal definition: the five-part machine</summary>

An epsilon-NFA can be written `M = (Q, Σ, δ, q₀, F)`:

- `Q` is a finite, nonempty set of states.
- `Σ` is a finite alphabet that excludes epsilon.
- `δ` maps each state and label in `Σ ∪ {ε}` to a set of destination states. A missing edge corresponds to the empty set.
- `q₀ ∈ Q` is the start state.
- `F ⊆ Q` is the set of final states, possibly empty.

For the diagram, `δ(0, a) = {1}`, `δ(1, ε) = {2}`, and `δ(2, b) = {3}`. All other entries are empty. The Python object stores edges rather than a complete table for `δ`; its alphabet is derived from all non-epsilon edge labels.

Let `E(S)` denote the epsilon closure of a state set `S`. For a word `c₁…cₙ`, set `A₀ = E({q₀})` and `Aᵢ = E(⋃ {δ(q, cᵢ) : q ∈ Aᵢ₋₁})`. The union symbol `⋃` means collect all members of the destination sets. Acceptance is `Aₙ ∩ F ≠ ∅`: the final active set and final-state set share at least one member.

For empty input, `n = 0`; no character step occurs. The same rule checks `A₀ ∩ F`. This explains how an epsilon path to a final state can accept an empty word even when the start state itself is not final.

</details>

## 6. Practice and common mistakes

**Exercise:** keep the same four states and edges, but change the final-state set to `{0, 3}`. Which of `""`, `a`, `ab`, and `aba` are accepted?

<details>
<summary>Reveal the answer and reason</summary>

Empty input and `ab` are accepted. The initial active set contains final state `0`, and the trace for `ab` reaches final state `3`. Input `a` finishes in `{1, 2}`; `aba` finishes with no active states. Making the start final does not make every word acceptable: finality is tested after the entire word.

</details>

**Exercise:** remove every final state without removing any edge. What language remains?

<details>
<summary>Reveal the answer</summary>

The empty language `∅`. There are paths in the graph, but none can finish in a final state. This is a valid `Automaton`: only the state set itself must be nonempty.

</details>

Common mistakes are accepting as soon as a final state appears, treating a missing transition as a fresh start, and confusing `None`, `""`, and `"ε"`. Correct each by asking separately: how much input remains, which states remain possible, and what type of object is being represented?

## Source grounding

- **Source commentary:** [model.py:1–17](../../python/src/jautomata/model.py#L1-L17) explains immutable graph values and internal epsilon; [model.py:69–94](../../python/src/jautomata/model.py#L69-L94) documents structural invariants.
- **Verified implementation:** [model.py:35–64](../../python/src/jautomata/model.py#L35-L64) validates labels; [model.py:102–134](../../python/src/jautomata/model.py#L102-L134) validates graph membership and derives the alphabet. [simulation.py:113–153](../../python/src/jautomata/simulation.py#L113-L153) applies the whole-word acceptance rule.
- **Historical implementation:** [Transicion.java:12–36](../../src/Model/AutomataStructure/Transicion.java#L12-L36) distinguishes a Java empty-string epsilon label from a consuming transition. Python deliberately uses `None` for that role.
- **Supplemental explanation:** the five-part tuple, set notation, language definitions, and hand-built example above explain the implementation; they are not quotations from the historical comments.

## Recap and resume

A finite graph recognizes a language of complete words. Its active set tracks possible states, epsilon changes state without consuming input, and acceptance requires a final state after all input is consumed.

**Next action:** build and test this exact graph in [Automata tutorial](../tutorials/automata.md). After that, learn how [regular expressions](regex.md) describe languages without drawing every edge.
