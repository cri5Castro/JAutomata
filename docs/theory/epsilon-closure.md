# Epsilon closure: reach every free destination

**Objective:** Compute every state reachable from a seed set without consuming a character, and explain why the traversal terminates on cycles.

**Before you start:** [Automata and state sets](automata.md), [literal fragments](literal.md). **Then practice:** [Runnable closure tutorial](../tutorials/epsilon-closure.md).

An epsilon transition changes the current state without reading input. Before deciding what character an NFA can consume next, we need all the states available through these free transitions. Epsilon closure gathers those possibilities.

## One rule, including zero steps

Write `C(S)` for the epsilon closure of a set of states `S`. Include every seed, then every state reachable from those seeds using only epsilon edges. The zero-step path explains why a seed belongs even when it has no outgoing edge. In Python, an epsilon edge has symbol `None`; the string `"ε"` would be an ordinary consuming character.

This example uses six states. The start state is 0; final states are 3 and 5. Finality does not affect the closure calculation.

**Read the figure:** Begin at `0` and follow only `ε` arrows. Keep the `a` edge and the separate component out of that closure.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Epsilon closure with cycles and separate components, scrollable diagram" style="--diagram-width: 752px">
  <img class="diagram" src="/JAutomata/diagrams/theory-epsilon-closure.svg" alt="Epsilon cycles connect 0, 1 and 2; reaching final 3 requires a. Separate state 4 reaches final 5 by epsilon, and 1 and 5 have epsilon self-loops.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/theory-epsilon-closure.svg">Open full-size diagram</a></p>

The return edge goes from 2 to 0. State 1 also has an epsilon self-loop. The following edge list records the same transitions:

| Source | Label | Target |
| --- | --- | --- |
| 0 | ε | 1 |
| 1 | ε | 1 |
| 1 | ε | 2 |
| 2 | ε | 0 |
| 2 | a | 3 |
| 4 | ε | 5 |
| 5 | ε | 5 |

Starting from `{0}`, closure reaches `{0, 1, 2}`. It does not reach 3: that edge requires consuming `a`. It does not reach 4 or 5: they are in another reachable region.

## Trace a work list

Keep two collections: `visited`, every discovered state, and `pending`, discovered states whose epsilon edges still need inspection. Add a state to `visited` **before** putting it on `pending`. A state already in `visited` is never scheduled again.

Here is one valid stack order; the result does not depend on traversal order.

| Action | Newly discovered | Visited | Pending, next item at right |
| --- | --- | --- | --- |
| Seed with 0 | 0 | `{0}` | `[0]` |
| Pop 0; inspect its epsilon edge | 1 | `{0, 1}` | `[1]` |
| Pop 1; ignore its self-loop; follow 1 → 2 | 2 | `{0, 1, 2}` | `[2]` |
| Pop 2; 0 is already visited | none | `{0, 1, 2}` | `[]` |

The consuming edge 2 → 3 is not part of this traversal. The empty work list means every discovered state's epsilon edges have been inspected. A cycle can lead back to a discovered state, but cannot create another copy of its work.

**Pause and predict:** What are `C({3})`, `C({0, 4})`, and `C(∅)`? Here `∅` means the empty set, not the empty string.

<details>
<summary>Reveal the three closures</summary>

`C({3}) = {3}` because the seed remains even without outgoing epsilon edges. `C({0, 4}) = {0, 1, 2, 4, 5}` because we explore from both seeds. `C(∅) = ∅`: no seed means no path to start following. Closure does not automatically insert the automaton's start state; the caller chooses its seeds.

</details>

## Three properties you can use

These mathematical explanations supplement the implementation's contract.

- **Extensiveness:** `S ⊆ C(S)`. Every seed is retained.
- **Idempotence:** `C(C(S)) = C(S)`. The first pass already found every free destination; closing again adds nothing.
- **Least fixed point:** Start with `S` and repeatedly add epsilon successors until the set stops changing. The result is the smallest epsilon-closed set containing `S`.

A fixed point is simply a set unchanged by another round of the same operation. “Smallest” matters: the entire automaton might also be epsilon-closed, but would include states unreachable from these seeds.

**Stop here if you have the picture:** The tutorial checks these properties on the graph above. The next section explains why they hold.

<details>
<summary>Optional depth: reachability invariant, termination and cost</summary>

Let `Q` be the finite set of states and let `Eε` be the epsilon edges. Define `Nextε(X)` as the set of targets of epsilon edges whose sources are in `X`. Starting with `X₀ = S`, repeatedly use `Xₖ₊₁ = Xₖ ∪ Nextε(Xₖ)`. This sequence only grows and is contained in finite `Q`, so it stabilizes.

The work-list invariant is: every visited state has an epsilon path from a seed; every visited but unprocessed state is pending; every processed state's epsilon successors are visited. Initialization satisfies this using zero-length paths. Discovering a successor extends a real path by one edge and preserves the invariant. At termination every discovered state is processed. Following any epsilon path from a seed therefore cannot leave the visited set. This proves both soundness (nothing spurious) and completeness (nothing reachable missing).

Each state is scheduled at most once. With adjacency lists ready, the traversal costs `O(Ve + Ee)`, where `Ve` is the number of epsilon-reachable states and `Ee` is the number of their epsilon edges inspected. This Python API first builds local adjacency maps over **all** `T` transitions, costing `O(T)` per call. Seed validation also examines the supplied iterable. For a seed set, the combined bound is `O(T + Ve + Ee)`; a long iterable with duplicates also incurs its input-reading cost. An empty closure can still pay setup cost.

Extensiveness follows from initialization. The returned set has no epsilon successor outside it, so closing it again changes nothing: idempotence. Every epsilon-closed superset of `S` must contain each discovered successor, proving the least-fixed-point claim.

</details>

## Common mistakes

- Stopping at the first final state. Closure computes reachability; it does not test whether a whole word is accepted.
- Following a consuming edge during closure. That silently changes the amount of input consumed.
- Marking a state only after recursive exploration finishes. A cycle can re-enter it before that mark exists.
- Returning only newly reached states. The seeds themselves belong in the result.

## Exercise: a closed set is not always this closure

For the graph above, `{0, 1, 2, 3}` is epsilon-closed. Does that make it `C({0})`? Would adding an epsilon edge from 2 to 3 change your answer?

<details>
<summary>Reveal a reasoned answer</summary>

Initially, no. State 3 is extra: the only listed edge into it consumes `a`. Being closed means no epsilon successor escapes the set; it does not establish reachability from a particular seed. After adding 2 → 3 with label epsilon, state 3 becomes epsilon-reachable and `C({0})` becomes `{0, 1, 2, 3}`. Both sets still contain the seed and are fixed points; the least reachable one changed with the graph.

</details>

## Where the lesson comes from

**Source commentary:** The Python [closure contract and cost](../../python/src/jautomata/simulation.py#L80-L106) describe epsilon reachability, immutability and cycle safety. **Actual implementation:** The [visited work list](../../python/src/jautomata/simulation.py#L67-L77) implements those guarantees; [local adjacency setup](../../python/src/jautomata/simulation.py#L42-L64) explains the setup cost.

**Historical distinction:** A Java [progress comment says closure and move were fixed](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L51-L54), but the [recursive closure still has no visited guard](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L119-L133). The comment is historical intent, not proof of termination. This is a source-flow finding; the lesson does not run the defective recursion. The properties and proof above are supplemental mathematical reasoning.

## Recap and resume

Closure means seeds plus every free destination. A visited set prevents repeated work on self-loops and cycles; the result is an epsilon-closed fixed point.

**Stop cue:** Save the three closures from the prediction check. **Resume cue:** Open the [closure tutorial](../tutorials/epsilon-closure.md) and compare them with assertions. Next, use closure before and after each consumed character in [NFA simulation](nfa-simulation.md).
