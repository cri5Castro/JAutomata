# Subset construction: a set becomes one state

**Objective:** Build a DFA whose states represent complete epsilon-closed NFA sets, then explain why both machines recognize the same words.

**Before you start:** [NFA simulation](nfa-simulation.md). **Then practice:** [Runnable subset tutorial](../tutorials/subset-construction.md).

NFA simulation already knows how to update a set of active states after one character. Subset construction makes those sets into a reusable graph: one DFA state per discovered set, one transition per input symbol. A DFA state number is a label for a set; it is not one selected NFA state.

## The three construction rules

Write `C` for epsilon closure and `move(S, a)` for all matching targets from set `S`.

- **Initial state:** represent `C({NFA start})`.
- **Transition:** from represented set `S` on `a`, go to `C(move(S, a))`.
- **Final state:** mark `S` final exactly when `S ∩ F` is nonempty, where `F` is the NFA final-state set and `∩` means intersection.

Apply finality to every discovered set, including the initial set. A final NFA state reached only through epsilon still counts.

## Reuse the six-state NFA

The [simulation lesson](nfa-simulation.md) uses start 0, finals `{4, 5}`, and these edges:

**Read the figure:** Start at `0`; keep both direct `a` branches and the `ε` route to `1`. Double circles mark finals `4` and `5`.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Three ways to consume a, then follow b, scrollable diagram" style="--diagram-width: 596px">
  <img class="diagram" src="/JAutomata/diagrams/competing-paths.svg" alt="Start 0 has epsilon to 1 and a edges to 2 and 3; 1 has a to final 5, 3 has epsilon to final 4, 2 has b to 5, and 4 loops on b.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/competing-paths.svg">Open full-size diagram</a></p>

The alphabet is `{a, b}`. The initial set is `{0, 1}`. We will number each new set when first discovered, starting at 0. Process the pending sets in first-in, first-out order (breadth-first search, or BFS), and consider symbols in sorted order: `a` before `b`.

## Fill the complete table

A **kernel** is the result of `move` before epsilon closure. The **target subset** is its closure. Only the latter names the next DFA state.

| DFA ID | Represented NFA set | Symbol | Move kernel | Target subset | Target ID |
| --- | --- | --- | --- | --- | --- |
| 0 | `{0, 1}` | a | `{2, 3, 5}` | `{2, 3, 4, 5}` | 1 |
| 0 | `{0, 1}` | b | `∅` | `∅` | 2 |
| 1 | `{2, 3, 4, 5}` | a | `∅` | `∅` | 2 |
| 1 | `{2, 3, 4, 5}` | b | `{4, 5}` | `{4, 5}` | 3 |
| 2 | `∅` | a | `∅` | `∅` | 2 |
| 2 | `∅` | b | `∅` | `∅` | 2 |
| 3 | `{4, 5}` | a | `∅` | `∅` | 2 |
| 3 | `{4, 5}` | b | `{4}` | `{4}` | 4 |
| 4 | `{4}` | a | `∅` | `∅` | 2 |
| 4 | `{4}` | b | `{4}` | `{4}` | 4 |

Process ID 0 first: it discovers IDs 1 and 2. Processing ID 1 next discovers ID 3. ID 2 adds nothing. ID 3 discovers ID 4. After ID 4, no undiscovered targets remain.

Final DFA IDs are `{1, 3, 4}` because each represented set intersects `{4, 5}`. ID 2 represents the empty set and is nonfinal. Stable numbering follows from BFS and sorted symbols, not from a meaningful ordering of NFA state numbers.

**Predict:** If the NFA final-state set changed to `{1}`, which DFA IDs would be final? Would the transition table change?

<details>
<summary>Reveal the initial-finality check</summary>

Only ID 0 would be final, because only `{0, 1}` contains state 1. The table of transitions would be unchanged: discovery depends on edges, not on finality. Empty input would now accept. Failing to inspect the initial subset would lose that word.

</details>

## Set identity is complete membership

Two subsets are the same DFA state when they contain exactly the same NFA states. Order and duplicate appearances do not matter. Python uses a `frozenset` as the dictionary key so that membership, rather than object identity or insertion order, determines reuse.

Kernel identity alone does not describe what the next DFA state can do. In our graph, kernels `{3}` and `{3, 4}` have the same closure `{3, 4}` because 3 has an epsilon edge to 4. Treating those closed destinations as different states would duplicate a represented set. Looking only at kernel `{3}` for finality would also miss final state 4.

The full subset determines possible future moves and finality. Even two **different** full subsets can accept the same suffix language. For this example, `{4, 5}` and `{4}` both accept exactly strings of zero or more `b`s. The converter keeps them separate: subset construction does **not** perform DFA minimization.

<details>
<summary>Optional depth: equivalence proof and the exponential bound</summary>

Let `R(w)` be the complete NFA active set after consuming word `w`, as defined in the simulation lesson. Let `D(w)` be the subset represented by the DFA state reached after the same word.

Base case: `D("") = C({start}) = R("")`. Induction step: if `D(w) = R(w)`, the DFA transition on `a` represents `C(move(D(w), a))`, which equals `C(move(R(w), a)) = R(wa)`. Therefore `D(w) = R(w)` for every finite word over the source alphabet. Both machines accept precisely when that set intersects the NFA finals. Symbols outside the alphabet have no corresponding NFA move and reject; the next lesson makes the alphabet boundary explicit.

This proof relies on complete closure and all move targets. It does not rely on the integer names assigned by BFS. Comparing both machines on every word up to length four checks a finite sample, not the induction step for every length.

For `N` NFA states, each state can either be inside or outside a subset: at most `2^N` choices. Only reachable epsilon-closed subsets are actually discovered, often far fewer. If `R` subsets are reached and `A` symbols are in the alphabet, the complete DFA has `R × A` transitions. Processing each subset still costs work to move and close it. The possible number of subsets makes worst-case conversion exponential; BFS does not remove that bound.

</details>

## Common mistakes

- Starting at `{start}` without closure. Epsilon-reachable initial possibilities vanish.
- Keeping a kernel as the represented state. Free continuations and epsilon-only final states are lost.
- Making a subset final only if every member is final. One accepting NFA path is sufficient.
- Assuming fewer states means an incorrect conversion, or that a correct conversion is minimal. Reachability and minimization are different questions.

## Exercise: two paths, one destination set

Imagine two moves produce kernels `{3}` and `{3, 4}` in this graph. How many DFA destination states should they create? Is that destination final with NFA finals `{4, 5}`? Then explain why our table still has distinct IDs 3 and 4.

<details>
<summary>Reveal the distinction</summary>

Both kernels close to `{3, 4}`, so they should reuse one destination state. It is final because it contains 4. IDs 3 and 4 in the table represent `{4, 5}` and `{4}`, which are different sets despite accepting the same suffix language in this graph. Subset identity merges equal sets; minimization would investigate language-equivalent states. The delivered converter only does the former.

</details>

## Where the lesson comes from

**Source commentary:** The Java [work-list explanation](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L35-L43) motivates processing pending subsets. The Python [BFS and full-subset contract](../../python/src/jautomata/subsets.py#L57-L87) specifies the current policy. **Actual implementation:** [Discovery, finality and transitions](../../python/src/jautomata/subsets.py#L91-L124) use full immutable sets, including the initial set.

**Historical distinction:** Java [kernel equality experiments](../../src/AFDtoAFDbySubsets/Subconjunto.java#L53-L67) are historical design evidence. Its informal initial-state wording refers to a newly represented subset, not reuse of the NFA start object. Its finality handling is inconsistent: [the initial state is not marked](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L44-L48), and [move/closure inspect source subsets or kernels rather than consistently inspecting full destination subsets](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L93-L114). These are static limitations recorded in the [Java audit](../java-reference.md#defects-and-port-decisions), not a claim that every historical conversion fails. The proof, bound and table above are supplemental explanations.

## Recap and resume

Start with a closure, give every discovered closed set one ID, compute moves for every symbol, and mark finality by intersection. This preserves the simulation invariant but does not minimize the result.

**Stop cue:** Save the five ID-to-subset mappings. **Resume cue:** Check them against the [runnable tutorial](../tutorials/subset-construction.md). Next, [complete DFAs](complete-dfa.md) explain why the empty subset gets transitions too.
