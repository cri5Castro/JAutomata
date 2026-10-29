# Thompson construction: positive closure

**Objective:** Distinguish one-or-more operand repetitions from consuming at least one character, including the nullable-operand case.

**Prerequisite:** [Kleene star, bypasses, and nullable operands](kleene-star.md).

**Route:** Compare the three-edge wrapper with star, trace `a+`, then resolve `(a*)+`. Run the [positive-closure tutorial](../tutorials/positive-closure.md) to check the distinctions.

## Require one operand word

The expression `a+` accepts `a`, `aa`, and every longer all-`a` word. It rejects empty input. The plus means **one or more repetitions of the operand**, not “one or more characters” in every possible expression.

If `L` is the operand language, `L+` contains concatenations of one or more words from `L`. When `L` contains the empty word, choosing that word once already satisfies the repetition requirement while consuming nothing.

That last case matters. The language of `a*` contains the empty word, so `(a*)+` accepts empty input even though `a+` does not.

## The wrapper has no bypass

Like star, positive closure adds a fresh entry and exit around a completed operand. For `a+`, the literal uses IDs `0` and `1`, and the wrapper uses `2` and `3`:

**Read the figure:** Enter the operand, consume `a`, then choose repeat or finish. There is no entry-to-final bypass.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Positive closure: enter before finishing, scrollable diagram" style="--diagram-width: 917px">
  <img class="diagram" src="/JAutomata/diagrams/positive-closure.svg" alt="Start 2 enters 0 by epsilon; after a reaches 1, epsilon repeats at 0 or finishes at final 3. There is no bypass from 2 to 3.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/positive-closure.svg">Open full-size diagram</a></p>

| Edge | Role | Shared with star? |
| --- | --- | --- |
| `2 --ε--> 0` | Enter the first operand traversal | yes |
| `1 --ε--> 0` | Begin another traversal | yes |
| `1 --ε--> 3` | Finish after a traversal | yes |
| `2 --ε--> 3` | Skip every traversal | **absent** for plus |

The wrapper maintains one entry and one exit. Its state IDs must be fresh relative to the operand. Removing the bypass is the only edge difference between the compiler's wrappers for `a*` and `a+`; it does not remove empty paths already inside an operand.

## Work through `a+`

| Input prefix | States after epsilon moves | Interpretation |
| --- | --- | --- |
| empty | `{0, 2}` | Ready to enter the literal; final `3` is absent |
| `a` | `{0, 1, 3}` | One operand word finished; can stop or repeat |
| `aa` | `{0, 1, 3}` | Another complete traversal finished |
| `aab` | empty set | No active state can consume `b` |

The first `a` makes the important difference: it crosses the literal edge to the operand exit. After that, star and plus have the same repeat-or-finish possibilities for this operand.

For `(a.b)+`, one traversal consumes the block `ab`. The shortest accepted word is `ab`; `abab` accepts, but `a`, `b`, and `aba` reject. Plus does not allow stopping partway through a block.

## Work through the nullable operand

The compiler first builds `a*` with entry `2` and exit `3`, including its bypass `2 --ε--> 3`. It then wraps that fragment for outer `+`, allocating entry `4` and exit `5`.

The outer wrapper adds `4 --ε--> 2`, `3 --ε--> 2`, and `3 --ε--> 5`. It does **not** add `4 --ε--> 5`. Nevertheless, this path exists:

**Read the figure:** Follow this **one accepting path** through `(a*)+`; other states and edges are omitted. Each shown edge consumes nothing.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="One empty-word path through (a*)+, scrollable diagram" style="--diagram-width: 981px">
  <img class="diagram" src="/JAutomata/diagrams/nullable-positive-path.svg" alt="One path in (a*)+ follows epsilon from start 4 through 2 and 3 to final 5, consuming nothing; other states and edges are omitted.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/nullable-positive-path.svg">Open full-size diagram</a></p>

All three edges consume nothing. The machine traversed one whole operand word: the empty word accepted by the inner star. Therefore the outer plus accepts empty input.

Its initial epsilon closure is `{0, 2, 3, 4, 5}`. The pair `2 --ε--> 3` and `3 --ε--> 2` also forms a cycle. A visited set makes closure finite; it does not delete the valid empty-word route.

## Predict before revealing

**Prediction 1:** Which of these accept empty input: `a+`, `(a.b)+`, `(a*)+`, `(a+)*`?

<details>
<summary>Reveal the answer and reason</summary>

`a+` and `(a.b)+` reject: their operands require characters on every successful traversal. `(a*)+` accepts because its operand is nullable. `(a+)*` also accepts, for a different immediate reason: its outer star can bypass its non-nullable operand entirely.

</details>

**Prediction 2:** Can plus be expressed using concatenation and star? What must remain separate in the resulting construction?

<details>
<summary>Reveal the answer and reason</summary>

At the language level, `L+ = LL*`: choose the first operand word, then zero or more additional words. Thus `a+` and `a.a*` recognize the same language. Constructing `R.R*` requires independent copies of `R` with disjoint state IDs. Reusing one mutable fragment for both occurrences could add unintended cycles or shortcuts. The dedicated plus wrapper avoids duplicating the operand graph.

</details>

## Optional: exact relationship between star and plus

<details>
<summary>Read the set definition and nullability argument</summary>

This is supplemental reasoning. If `Lⁿ` denotes concatenation of `n` words from `L`, then `L+` is the union of `Lⁿ` for all `n ≥ 1`. In comparison, `L*` includes the `n = 0` case. Therefore `L* = {ε} ∪ L+`.

If `ε` belongs to `L`, one operand traversal can consume it, so `ε` belongs to `L+` and `L+ = L*`. Conversely, if a finite concatenation of one or more words has length zero, every word in that concatenation has length zero. At least one operand word is therefore `ε`, so the operand must be nullable.

This proves the useful rule: `R+` accepts empty input exactly when `R` does. The common statement “plus rejects empty input” is correct only for non-nullable operands.

</details>

## Common mistakes

- **Equating repetitions with character count.** A repetition is one word from the operand language; that word can have length zero or several characters.
- **Assuming no direct bypass means no epsilon route.** Inspect the whole operand, as `(a*)+` demonstrates.
- **Changing the evaluator to reject empty input whenever the regex has `+`.** Acceptance follows the graph, not a blanket operator shortcut.

## Source evidence

- **Original commentary:** [Java's positive closure, lines 144–164](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L144-L164), describes the positive-closure operation.
- **Documented meaning:** [Python's positive-closure node, lines 72–75](../../python/src/jautomata/regex.py#L72-L75), states one-or-more repetition.
- **Verified source behavior:** [Shared repeat wrapper and conditional bypass, lines 84–92](../../python/src/jautomata/thompson.py#L84-L92), adds a bypass only for `*`. The tutorial checks both its absence and the nullable operand's indirect path.
- **Supplement:** The nullable-language proof, `L+ = LL*`, and the worked closure traces are explanatory additions. See the [source map](../reference/source-curriculum.md).

## Recap and resume

Positive closure requires at least one complete operand traversal. It lacks star's direct bypass, but an operand may itself traverse from entry to exit without consuming input.

**Stopping point:** Explain the empty path through `(a*)+` without saying “plus has a bypass.” **Resume:** Run the [positive-closure tutorial](../tutorials/positive-closure.md), then study [epsilon closure](epsilon-closure.md) to see how all these possibilities are collected safely.
