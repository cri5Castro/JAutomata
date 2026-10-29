# Complete DFAs: give every symbol a destination

**Objective:** Check totality over a DFA's source alphabet and explain when conversion needs the empty-subset sink.

**Before you start:** [Subset construction](subset-construction.md). **Then practice:** [Runnable complete-DFA tutorial](../tutorials/complete-dfa.md).

A transition can be unambiguous yet missing. Separating those two properties explains the converter's complete-DFA policy and prevents an incorrect test that checks only symbols already present at a particular state.

## Determinism and totality answer different questions

In this lesson, a transition relation is **deterministic** when it has no epsilon edges and at most one target for each state/symbol pair. It is **total over alphabet Σ** when every state has a target for every symbol in `Σ`. Together they give exactly one target per pair.

Some textbooks reserve “DFA” for total machines and say “partial DFA” for a deterministic graph with missing transitions. The distinction here makes both properties visible. `to_dfa` returns a complete DFA over the source NFA's alphabet.

The alphabet `Σ` is a finite set of consuming labels. In this model it is derived from all transitions, excluding `None`. It is not the set of characters seen in the current test word, and it is not recomputed separately for each state.

## A source alphabet can include unreachable edges

Consider this NFA, with start 0 and final state 1:

**Read the figure:** Compare the two separate components. The `z` loop contributes to the alphabet even though the start cannot reach it.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="The alphabet includes unreachable edges, scrollable diagram" style="--diagram-width: 443px">
  <img class="diagram" src="/JAutomata/diagrams/complete-alphabet.svg" alt="Start 0 reaches accepting state 1 on a. Disconnected state 9 loops on z, so the source alphabet is {a, z}.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/complete-alphabet.svg">Open full-size diagram</a></p>

Its alphabet is `{a, z}` because both labels occur in the source graph. State 9 is unreachable, but its label still contributes to the source alphabet. The language is just the one-character word `a`; this is an inference from the graph.

Conversion discovers these subsets:

| DFA ID | Represented subset | Final? | On `a` | On `z` |
| --- | --- | --- | --- | --- |
| 0 | `{0}` | no | 1 | 2 |
| 1 | `{1}` | yes | 2 | 2 |
| 2 | `∅` | no | 2 | 2 |

No subset contains NFA state 9, because it cannot be reached from the start. Nevertheless every DFA row has a `z` transition, as required by the whole source alphabet. IDs happen to share numbers with some NFA states; their meaning is the subset column.

## Why the empty subset loops

When no NFA state can consume a symbol, `move(S, a) = ∅`. Closing it still gives `∅`. The converter records this as a state representing “no possible NFA state remains.”

From `∅`, every subsequent move is empty, and so is its closure. Therefore each alphabet symbol returns to that same state. It cannot be final, because `∅` intersects no final-state set. We call it the **empty-subset sink**.

A nonempty rejecting subset can also trap every future input in some machines. That is a broader use of “sink.” Here we specifically track the state representing `∅`, whose transitions follow directly from the subset rules.

**Predict:** Does every converted DFA need an empty-subset sink? Consider one final state with an `a` self-loop and alphabet `{a}`.

<details>
<summary>Reveal the reachability condition</summary>

No. The initial subset contains that state, and every `a` returns to the same nonempty subset. The empty subset is never reached, so the converter does not create it. The output is already complete: there is exactly one transition for its only state/symbol pair. Completion requires a destination, not an extra state in every machine.

</details>

## Three boundary cases

| Case | What happens | Why |
| --- | --- | --- |
| Empty alphabet | The output has the initial closed subset and no transitions | There are no state/symbol pairs to fill |
| No final states | Every output subset is nonfinal | No subset can intersect an empty final-state set |
| A character outside the source alphabet | `accepts` rejects any word containing it | No source transition can consume that character |

With an empty alphabet, the only word over that alphabet is empty input. An epsilon-only NFA can accept it if its initial closure contains a final state. Conversion then produces a single final state and zero edges. A single nonfinal state with zero edges is equally complete over the empty alphabet, but rejects empty input.

Completeness over `{a, z}` does not require a `b` edge. The API accepts arbitrary Python strings as queries; an out-of-alphabet character empties the active set and returns rejection. It does not expand the machine's alphabet or implicitly add a new transition.

<details>
<summary>Optional depth: total transition functions and vacuous conditions</summary>

A complete DFA's transition function has type `δ: Q × Σ → Q`, where `Q` is its state set and `Q × Σ` is the set of all state/symbol pairs. Each pair must have exactly one destination.

Subset construction defines `δ(S, a) = C(move(S, a))`. Both move and closure are defined for empty results, so this definition always supplies a destination subset. The implementation visits every symbol of the source alphabet for every discovered subset, discovering the empty set when necessary. After all pending subsets have been processed, every reachable row is complete.

If `Σ = ∅`, then `Q × Σ = ∅`. The statement “every pair has exactly one destination” is true because there are no pairs that could violate it. This is called vacuous truth. A DFA still needs an initial state, so zero alphabet symbols do not mean zero states.

For `R` returned states and `A` source symbols, completeness gives exactly `R × A` transitions. Count alone is not a sufficient check: two destinations for one pair could hide a missing pair elsewhere. A structural checker should inspect every pair and prohibit epsilon edges.

</details>

## Common mistakes

- Checking only the labels on each state's outgoing edges. A state with no outgoing edges would incorrectly pass for a nonempty alphabet.
- Removing symbols found only on unreachable source edges before checking this API's contract. Its policy uses the whole source alphabet.
- Calling the sink an error or accepting state. It records a valid rejecting situation: all NFA paths have died.
- Assuming no final states implies no states. A rejecting complete graph may still need transitions and a sink.

## Exercise: complete over which alphabet?

Take one nonfinal state with an `a` self-loop. Is it deterministic? Is it complete over `{a}`? Is it complete over `{a, b}`? What if its alphabet were empty?

<details>
<summary>Reveal the alphabet-sensitive answer</summary>

It is deterministic and complete over `{a}`. Over `{a, b}`, it is missing the `b` transition, so it is not complete. Under this project's model its alphabet cannot be empty while the `a` edge exists, because the alphabet is derived from consuming edges. If you remove that edge, the graph has an empty alphabet and is complete with zero transitions. It still rejects every word because there are no final states.

</details>

## Where the lesson comes from

**Source commentary:** The Python [module policy](../../python/src/jautomata/subsets.py#L1-L11) and [conversion contract](../../python/src/jautomata/subsets.py#L64-L82) specify complete output and a reachable empty-subset sink. **Actual implementation:** [Alphabet extraction](../../python/src/jautomata/model.py#L128-L134) scans all consuming edges, and [the conversion loop](../../python/src/jautomata/subsets.py#L106-L117) builds a transition for every source-alphabet symbol.

The empty-alphabet argument, transition-function notation and unreachable-edge example are supplemental reasoning from those rules. They do not claim that historical Java comments established the same policy. The [source curriculum map](../reference/source-curriculum.md) separates that historical evidence from current Python guarantees.

## Recap and resume

Determinism limits each pair to one destination; totality supplies a destination for every alphabet symbol. The empty subset supplies missing moves and loops forever once reached. Its existence depends on reachability, while completeness always depends on a stated alphabet.

**Stop cue:** Save the three-row table and circle the `z` column. **Resume cue:** Run the [complete-DFA tutorial](../tutorials/complete-dfa.md) to check the unreachable-symbol and empty-alphabet cases. Then compare state sets, graph equality and language equivalence in [identity](identity.md).
