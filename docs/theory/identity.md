# Identity, equality and immutable graphs

**Goal:** decide whether two names refer to one object, two automata have the same stored graph, or two automata recognize the same language. These questions need different evidence.

**Before you start:** [Automata](automata.md), [concatenation](concatenation.md) and [subset construction](subset-construction.md). You need only sets, transitions and the idea of a DFA state representing a set of NFA states.

**Route:** compare → follow an alias → rename a graph → predict. Then run the [paired tutorial](../tutorials/identity.md).

## Three questions that look alike

Let `L(M)` mean the set of all words accepted by machine `M`.

| Question | Meaning | Example |
| --- | --- | --- |
| Object identity | Are these names attached to the same Python object? Use `is`. | `alias = machine` creates another name for that object. |
| Structural value equality | Are all stored fields equal? Use `==` for these immutable dataclasses. | Same integer states, start, final set and transition set. |
| Language equivalence | Is `L(A) = L(B)` for every possible input word? | Renaming every state consistently preserves the language. |

A **state identifier** is an integer meaningful inside its automaton. State `0` in two separately compiled automata does not make those automata one graph. Within one machine, using `0` twice refers to the same state; it does not allocate two states.

Two calls to `compile_regex("a")` return distinct objects with equal values. Their state IDs are allocated afresh within each compilation. Equal values imply the same language under the same evaluator. The converse fails: different stored graphs can recognize the same words.

## Follow one alias

An alias is another reference to an existing object. Copying a container can leave its elements shared:

**Read the figure:** Follow both list references to the same object. These arrows represent references between objects.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Two collections share the same mutable objects, scrollable diagram" style="--diagram-width: 823px">
  <img class="diagram" src="/JAutomata/diagrams/shared-identity.svg" alt="Original and copied lists point to the same mutable state, which refers to a mutable transition; arrows represent shared references.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/shared-identity.svg">Open full-size diagram</a></p>

The historical Java helper calls its action a copy, but `copiarEstados` inserts existing state objects. The transition helpers reuse transition objects and change their origins. Mutating a shared object is visible through every alias to it. This is a source-flow observation, not a new execution of the Java program.

Python's `Automaton` instead normalizes caller collections into `frozenset` values. Clearing a caller's original list or set cannot remove elements from the stored machine. Its transitions are themselves frozen values, so safely sharing a transition needs no deep copy. Immutability is what makes that sharing useful.

## Why sets collapse duplicates

A set represents membership, not insertion order or multiplicity. Therefore two equal `Transition(0, "a", 1)` values become one edge when normalized. Two edges with different targets remain distinct and can represent nondeterminism.

A dictionary key or set member must be **hashable**: it supplies a stable hash used to choose where to look. Equal objects must have equal hashes; unequal objects may still have the same hash, so Python also checks equality. Never use a hash value as a unique state identity or compare graphs only by their hashes.

An ordinary mutable `set` is unhashable. A `frozenset` of integers is hashable and suitable for subset-construction dictionary keys. `{1, 2}` and `{2, 1}` describe the same mathematical subset. The Python converter keys on the **full epsilon-closed subset**, not an ordered discovery list or just the pre-closure move targets.

## Worked trace: rename every state

Consider two machines whose only final state is marked by a double circle:

**Read the figure:** Compare the two machines. The labels change from `0, 1` to `10, 11`; the consuming edge and accepting role stay the same.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Rename states and preserve the language, scrollable diagram" style="--diagram-width: 454px">
  <img class="diagram" src="/JAutomata/diagrams/relabeling.svg" alt="Machine A is start 0 to final 1 on a; machine B is start 10 to final 11 on a, with all state references renamed consistently.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/relabeling.svg">Open full-size diagram</a></p>

The renaming sends `0 → 10` and `1 → 11`. It must change the start, final set, and both endpoints of every edge.

| Input | A finishes at | B finishes at | Result |
| --- | --- | --- | --- |
| empty | 0 | 10 | reject |
| `a` | 1 | 11 | accept |
| `aa` | no active state | no active state | reject |

The graphs are unequal values because their IDs differ. The labels along corresponding paths are unchanged, so the languages agree. Forgetting to rename a final state would either violate model validation or change the machine's meaning.

<details>
<summary>Optional depth: the renaming argument</summary>

Let `f` be a bijection, meaning a one-to-one correspondence, between the two state sets. Require that it maps the start to the start, maps exactly the final states to final states, and maps every edge `(p, x, q)` to `(f(p), x, f(q))` in both directions. Here `x` is either an input symbol or epsilon.

Each path in one graph then has a corresponding path in the other with the same consumed word. Initial and final conditions are preserved, so acceptance agrees for every word. This proves equivalence for this renaming construction. Testing finitely many words is useful evidence but cannot by itself establish the universal claim.

</details>

## Predict before revealing

Two states both have no outgoing edges. One is final; the other is not. Do their outgoing edges alone establish the same accepted suffixes?

<details>
<summary>Answer and reason</summary>

No. Starting at the final state accepts the empty suffix; starting at the other rejects it. Even matching outgoing edge labels would not be enough without knowing where those edges lead and which states are final. The historical suggestion to compare transitions is not a definition of language equivalence.

</details>

**Common mistake:** combining two independently compiled machines by taking the union of their integer state sets. Both may use `0` and `1`; the union would merge unrelated states. Composition needs fresh IDs or a consistent relabeling. The Thompson builder owns one allocator per compilation to avoid that collision inside a compiled expression.

## Source evidence

- **Commentary:** [Java's temporary name-equality note](../../src/Model/AutomataStructure/Estado.java#L172-L175) and [copying comments and shared objects](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L188-L221).
- **Verified implementation:** [Python normalization and graph validation](../../python/src/jautomata/model.py#L101-L125), [fresh per-compilation allocation](../../python/src/jautomata/thompson.py#L30-L42), and [full closed-subset keys](../../python/src/jautomata/subsets.py#L91-L117).
- **Historical distinction:** [the abandoned nested-loop equality and active kernel equality](../../src/AFDtoAFDbySubsets/Subconjunto.java#L53-L67) are source history, not a language-equivalence oracle.
- **Supplemental reasoning:** the three-way comparison, hash explanation and relabeling proof above explain consequences of these choices; they are not claims quoted from Java comments.

## Recap and stop point

Identity names an object; value equality compares stored data; language equivalence compares all accepted words. Immutable values prevent caller-container changes from leaking into a graph and make subset keys reliable.

**Stop here:** explain why renaming IDs changes equality but preserves paths. **Resume:** open the [identity tutorial](../tutorials/identity.md), predict its three comparisons, then run its complete program.
