# Thompson construction: union

**Objective:** Explain how four epsilon edges and two fresh states preserve both alternatives of a union.

**Prerequisites:** [Literal fragments](literal.md) and [concatenation](concatenation.md).

**Route:** Start with the two routes in the diagram, trace one input, then check the shared-prefix exercise. Pair this lesson with the [runnable union tutorial](../tutorials/union.md).

## Either alternative may succeed

The expression `a|b` describes the language `{a, b}`. The operator `|` means union: a word belongs if it belongs to either operand language, including words that belong to both. It does not concatenate the alternatives.

To combine two completed fragments, allocate a fresh entry and a fresh exit. Add epsilon edges from the new entry into both operands, and from both operand exits into the new exit:

**Read the figure:** From start `4`, follow either literal branch to the shared double-circle final `5`. Count four `ε` edges.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Union: split into alternatives, then join, scrollable diagram" style="--diagram-width: 745px">
  <img class="diagram" src="/JAutomata/diagrams/union.svg" alt="Start 4 splits by epsilon to 0 and 2; a takes 0 to 1 and b takes 2 to 3; both exits join final 5 by epsilon.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/union.svg">Open full-size diagram</a></p>

The two labelled edges belong to the original literal fragments. The four `ε` edges perform the split and join without consuming input. State `4` is the new entry, and state `5` is the only final state of the completed graph. Being a start state does not imply having the smallest ID.

## Why fresh wrapper states help

The left and right operands already have disjoint state IDs. The wrapper needs IDs different from every operand state, so the new boundaries cannot accidentally coincide with an internal state.

The new entry has no incoming edges, and the new exit has no outgoing edges. Thus the enclosing graph is again a single-entry/single-exit fragment, ready for another operator. The old exits `1` and `3` are now internal states; they are not additional finals in the compiled graph.

The wrapper is compositional: it needs only the two operands' boundary IDs. The operands may be large graphs with cycles, not just single literal edges.

## Work through the possibilities

Before consuming input, follow all available epsilon moves from the new start. From `4`, either `0` or `2` is reachable, so the initial active set is `{0, 2, 4}`. An **active set** contains all graph states possible after the same consumed prefix.

| Input prefix | Matching consuming move | After epsilon moves | Final reached? |
| --- | --- | --- | --- |
| empty | none yet | `{0, 2, 4}` | no |
| `a` | `0 --a--> 1` | `{1, 5}` | yes |
| `b` | `2 --b--> 3` | `{3, 5}` | yes |
| `ab` | after `a`, neither `1` nor `5` has a `b` edge | empty set | no |

The `a` and `b` rows are separate runs. In either run, every branch compatible with the input remains possible. A failed branch does not cause the whole machine to reject if another branch can finish.

**Nondeterminism** describes these multiple possible paths. It does not require threads, random choice, or choosing a branch once and refusing to reconsider it. The delivered evaluator tracks a set of possibilities.

## Shared prefixes expose the important rule

Consider `(a.b)|(a.c)`. Both alternatives can consume the first `a`. After that prefix, the left branch expects `b` and the right branch expects `c`. Keeping both possibilities allows both `ab` and `ac` to succeed.

Choosing only the first matching `a` edge would lose one of those words. Conversely, combining leftover characters from unrelated branches would accept words with no real path. A correct active-set update follows actual edges from all currently possible states.

The expression `(a|b).c` groups the union before concatenation. It accepts `ac` and `bc`: first choose an alternative, then consume `c`. Parentheses control how the fragment rules are nested.

## Predict before revealing

**Prediction 1:** Does `a|a` accept `aa` because it has two `a` edges?

<details>
<summary>Reveal the answer and reason</summary>

No. The edges are on alternative routes, not on one sequential route. Each successful route consumes one `a`, then joins the wrapper exit. The language is still `{a}`. Two successful paths for the same word do not change the set of accepted words.

</details>

**Prediction 2:** If one operand of a union accepts the empty word, must the entire union accept it?

<details>
<summary>Reveal the answer and reason</summary>

Yes. Follow the new entry's epsilon edge into that operand, take its empty-word path, then follow the epsilon edge to the new exit. For example, `a*|b` accepts the empty word through its left operand. The union wrapper itself has no direct bypass, but its operand can provide a non-consuming route.

</details>

## Optional: connect graph paths to set union

<details>
<summary>Read the short correctness argument</summary>

This is supplemental reasoning. Suppose the operands recognize `L` and `M`. Every entry-to-exit path through the wrapper enters an operand and leaves through that operand's exit. The operands are disjoint and have no cross-edges. The consumed word therefore belongs to `L` or `M`.

Conversely, a successful path for a word in either operand can be extended by the wrapper's entry and exit epsilon edges. It consumes the same word because those extra edges consume nothing. Therefore the resulting language is exactly `L ∪ M`, where `∪` denotes set union.

The proof permits overlap between `L` and `M`; union does not mean exclusive choice.

</details>

## Common mistakes

- **Adding only the two splitting edges.** Both operand exits still need edges to the new common exit.
- **Accepting the first available branch as the only branch.** Shared prefixes require retaining all compatible states.
- **Reading `|` as “then.”** `a|b` accepts one symbol; `a.b` accepts two symbols in order.

## Source evidence

- **Original commentary:** [Java's union construction, lines 119–143](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L119-L143), describes the two operand automata and their combination.
- **Documented contract:** [Python's correspondence note, lines 116–121](../../python/src/jautomata/thompson.py#L116-L121), identifies fresh-entry/fresh-exit union topology.
- **Verified source behavior:** [Union allocation and its four edges, lines 72–82](../../python/src/jautomata/thompson.py#L72-L82), supplies the exact graph checked in the tutorial.
- **Supplement:** The set-union proof, active-set trace, and shared-prefix explanation connect source behavior to language semantics. See the [source map](../reference/source-curriculum.md).

## Recap and resume

Union adds two fresh states and four epsilon edges. Its alternatives remain possible until the input rules them out. One successful complete path is enough for acceptance.

**Stopping point:** Count the four epsilon edges in the diagram and explain each one's purpose. **Resume:** Run the [union tutorial](../tutorials/union.md), then learn how [Kleene star](kleene-star.md) adds repetition.
