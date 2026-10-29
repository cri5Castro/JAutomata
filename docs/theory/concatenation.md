# Thompson construction: concatenation

**Objective:** Connect two fragments in the correct order and explain when an epsilon link and endpoint fusion describe the same language.

**Prerequisite:** [Literal fragments and their boundary invariant](literal.md).

**Route:** Follow `a.b` through the diagram and trace. The fusion comparison is part of this lesson; the formal proof is optional. Then use the [runnable concatenation tutorial](../tutorials/concatenation.md).

## Left word, then right word

Concatenation puts words end to end. If `L` and `M` are languages, their concatenation is `LM = {xy | x is in L and y is in M}`. Here `xy` means the characters of `x` followed by the characters of `y`; it is not multiplication.

For example, `{a}{b} = {ab}`. Reversing the operands gives `{ba}`, a different language. This project writes concatenation explicitly with a dot: `a.b` describes `ab`. The dot is an operator and is not consumed from the input.

The Thompson rule connects the left fragment's exit to the right fragment's entry with an epsilon edge. The result keeps the left entry and the right exit:

**Read the figure:** Follow left to right: consume `a`, cross the free `ε` seam, then consume `b`. Double circles mark accepting states.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Concatenation: a then b, scrollable diagram" style="--diagram-width: 747px">
  <img class="diagram" src="/JAutomata/diagrams/concatenation.svg" alt="Start 0 consumes a to 1, follows epsilon to 2, then consumes b to accepting state 3.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/concatenation.svg">Open full-size diagram</a></p>

An epsilon edge advances through the graph without consuming a character. It lets the machine finish the left word before starting the right word. No fresh wrapper states are needed for this rule, but the two operand fragments must already have disjoint state IDs.

## Work through `a.b`

The postfix order is `a b .`. The stack first receives the literal fragment `(0, 1)`, then the literal fragment `(2, 3)`. On `.` the builder pops the **right** operand first because it is on top, then the left operand. It adds `1 --ε--> 2` and pushes `(0, 3)`.

| Input consumed | Possible states after epsilon moves | What changed? |
| --- | --- | --- |
| nothing | `{0}` | The start has no epsilon edge |
| `a` | `{1, 2}` | Consuming `a` reaches `1`; the connector also reaches `2` |
| `ab` | `{3}` | `b` is available from `2`; `3` is final |

The state set `{1, 2}` does not mean input was consumed twice. Both positions are possible after the same prefix `a` because crossing the connector costs no input.

The word `a` rejects because neither `1` nor `2` is final. The word `b` rejects immediately. The word `ba` rejects because order matters. The word `aba` reaches the final state after `ab` but cannot consume the last `a`.

## Compare the two concatenation shapes

The historical Java source contains both an epsilon-link operation and an endpoint-fusion operation. The Python compiler chooses the epsilon-link variant. For two literal fragments, a carefully constructed fused diagram looks like this:

**Read the figure:** Compare one graph at a time. The `ε` seam keeps two states; the fused seam uses a single state `X`.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Two seams, the same word ab, scrollable diagram" style="--diagram-width: 683px">
  <img class="diagram" src="/JAutomata/diagrams/concatenation-seams.svg" alt="Compare the four-state epsilon-linked a.b graph with a separate three-state graph whose seam is X; both finish at 3.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/concatenation-seams.svg">Open full-size diagram</a></p>

Both diagrams recognize `ab`. They do not have the same graph structure: the first has four states and three edges; the second has three states and two edges. Equality of languages does not require equality of graphs.

Why can the seam be fused here? Before joining ordinary Thompson fragments, the left exit has no outgoing edges and the right entry has no incoming edges. Their IDs are disjoint, and only the outer entry and exit will determine the combined machine's start and finality. Under these conditions, identifying these two boundary states removes a non-consuming handoff without allowing a new way to enter or leave either operand.

These are conditions to check, not permission to merge arbitrary states. A general automaton may have cycles through an entry or exit, several final states, or external edges into either endpoint. Fusion in those graphs can create paths that switch back and forth between operands. The tutorial gives a concrete counterexample.

The historical mutating helper is evidence of the attempted fusion strategy, not a general graph-equivalence theorem. Its copying and transition-ownership behavior also needs care; see [identity and ownership](identity.md). The delivered compiler avoids that mutation by retaining distinct states and adding the explicit link.

## Predict before revealing

**Prediction 1:** What words can `a*.b` accept if the left fragment can finish without consuming input? Does concatenation always require both sides to consume a character?

<details>
<summary>Reveal the answer and reason</summary>

It accepts `b`, `ab`, `aab`, and so on. The left language contains the empty word, so choosing that left word leaves only the right word `b`. Concatenation requires a word from each operand's language, but one of those words may be empty. The epsilon connector itself never contributes a character.

</details>

**Prediction 2:** If a three-state fused `ab` graph agrees with the four-state compiler graph on `""`, `"a"`, `"b"`, `"ab"`, and `"ba"`, have those tests proved language equivalence?

<details>
<summary>Reveal the answer and reason</summary>

No. They provide evidence for five words. A proof needs reasoning about every path or every possible input. In this small example, both graphs have exactly one entry-to-exit route, consuming exactly `ab`, which supplies the missing general argument.

</details>

## Optional: the composition argument

<details>
<summary>Read why the epsilon-link rule preserves the language</summary>

This is supplemental reasoning. Assume the left fragment recognizes exactly `L` and the right fragment exactly `M`, with disjoint states and the boundary invariant described above.

A path through the new fragment must first reach the left exit, cross the connector, and then reach the right exit. It consumes some `x` in `L` followed by some `y` in `M`, so every accepted word lies in `LM`. Conversely, a successful path for any `x` in `L` can be followed by the connector and a successful path for any `y` in `M`. Thus every word of `LM` is accepted.

The argument includes empty operand words. It relies on the boundary invariant to prevent an unintended escape or return across the seam.

</details>

## Common mistakes

- **Popping left before right from a stack.** Postfix places the right fragment on top. Reversing them changes `ab` to `ba`.
- **Leaving the left exit final.** That would accept a completed left word before the required right word. Only the combined exit is final.
- **Deleting epsilon edges without a replacement argument.** Removing the connector disconnects the machine; merging its endpoints needs the conditions above.

## Source evidence

- **Original commentary and implementation:** [Java's two concatenation variants, lines 87–117](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L87-L117), describe the left and right inputs and show linking versus fusion.
- **Documented contract:** [Python's ownership policy, lines 1–10](../../python/src/jautomata/thompson.py#L1-L10), explicitly selects epsilon-link concatenation.
- **Verified source behavior:** [Ordered stack pops and connector, lines 65–70](../../python/src/jautomata/thompson.py#L65-L70), implement the four-state `a.b` topology checked in the tutorial.
- **Supplement:** Language concatenation, the path proof, and safe-fusion conditions are explanatory reasoning. The [source map](../reference/source-curriculum.md) separates these from historical commentary.

## Recap and resume

Concatenation joins the left exit to the right entry without consuming input. It preserves order and may concatenate an empty operand word. Endpoint fusion is a conditional graph transformation, not a general state-merging rule.

**Stopping point:** Sketch `a.b` and circle its only final state. **Resume:** Run the [concatenation tutorial](../tutorials/concatenation.md), then compare sequential composition with [union](union.md).
