# Thompson construction: Kleene star

**Objective:** Explain zero-or-more repetition using an entry edge, a bypass, a repeat edge, and an exit edge.

**Prerequisites:** [Literal fragments](literal.md), [concatenation](concatenation.md), and [union](union.md).

**Route:** Learn the four edges, trace two letters, then inspect what happens when the operand already accepts empty input. Continue with the [runnable star tutorial](../tutorials/kleene-star.md).

## Zero is a real choice

The expression `a*` accepts `""`, `"a"`, `"aa"`, and every longer word made only of `a`. The star applies to its operand expression. Thus `(a.b)*` repeats the whole block `ab`, not just its last letter.

If `L` is a language, `L*` contains the words formed by concatenating zero or more words from `L`. The zero-word concatenation is the empty word, written `ε`. Therefore every star expression accepts empty input, regardless of its operand's language.

The construction wraps one completed operand in two fresh states. For `a*`, the operand is `0 --a--> 1` and the wrapper states are `2` and `3`:

| Edge | Purpose |
| --- | --- |
| `2 --ε--> 0` | Enter the first repetition |
| `2 --ε--> 3` | Bypass the operand: zero repetitions |
| `1 --ε--> 0` | Repeat after completing an operand word |
| `1 --ε--> 3` | Finish after completing an operand word |

~~~text
                   +-------- ε bypass --------+
                   |                          v
start 2 --ε--> 0 --a--> 1 --------ε-----------> 3 final
               ^        |
               +--- ε --+
                  repeat
~~~

The wrapper's entry has no incoming edges and its exit has no outgoing edges. The child's boundaries become internal and acquire the connections needed for repetition. The enclosing fragment still has one entry and one exit.

## Work through `aa`

An epsilon closure is the set of states reachable through zero or more epsilon edges, including the starting states. The [epsilon-closure lesson](epsilon-closure.md) explains the algorithm in detail; here it lets us inspect the construction.

| Input consumed | Consuming destination | After all epsilon moves |
| --- | --- | --- |
| nothing | Start at `2` | `{0, 2, 3}` |
| first `a` | `0 --a--> 1` | `{0, 1, 3}` |
| second `a` | `0 --a--> 1` again | `{0, 1, 3}` |

The initial set already contains final state `3`, so empty input accepts. After each `a`, the repeat edge makes `0` available for another letter and the exit edge makes `3` available if the input ends. These are simultaneous possibilities, not a fixed decision made in advance.

An input `b` has no matching edge from the initial set. An input `aab` loses every active possibility on its last character. A final state being reachable after a prefix does not accept a longer word whose suffix cannot be consumed.

## Repeating a block

For `(a.b)*`, one completed repetition consumes `ab`. The bypass still accepts empty input, but the first non-empty accepted word is `ab`, followed by `abab`.

The word `a` cannot exit halfway through a repetition: the repeat and exit edges leave the operand's exit, after its `b`. The word `abb` also rejects because the next repetition must begin with `a`. Thinking in operand words prevents “star means any mixture of these letters” mistakes.

## Nullable operands and epsilon cycles

An expression is **nullable** when it accepts the empty word. A star is always nullable. In `(a*)*`, the outer operand `a*` can finish without consuming input, and the outer repeat edge returns to its entry. That creates a cycle consisting entirely of epsilon edges.

There can be infinitely many graph walks through such a cycle, but only finitely many reachable states. Recognition needs the reachable states, not a separate record of every walk. The delivered epsilon-closure algorithm keeps a visited set, so reaching an already visited state does not restart its exploration forever.

For this compiler's `(a*)*` graph, the inner bypass is `2 --ε--> 3` and the outer repeat edge is `3 --ε--> 2`. Starting from outer entry `4` reaches `{0, 2, 3, 4, 5}` without consuming input. It cannot reach state `1` until an `a` is consumed. The tutorial checks both the cycle and these exact sets.

## Predict before revealing

**Prediction 1:** Remove only the bypass edge `2 --ε--> 3` from the `a*` diagram. What happens to empty input and to `aaa`?

<details>
<summary>Reveal the answer and reason</summary>

Empty input rejects because the literal operand cannot finish without reading an `a`. `aaa` still accepts: enter the operand, repeat twice, then exit. The resulting graph is the positive-closure construction for `a+`.

</details>

**Prediction 2:** Does nesting the star in `(a*)*` introduce any new words compared with `a*`?

<details>
<summary>Reveal the answer and reason</summary>

No. Grouping an all-`a` word into several all-`a` words still produces an all-`a` word, and zero repetitions still gives empty input. Conversely, any word of `a*` can serve as one outer operand word. The graph has more states and an epsilon cycle, while the language is unchanged.

</details>

## Optional: define the repetition language precisely

<details>
<summary>Read the formal definition and path argument</summary>

This is supplemental reasoning. Define `L⁰ = {ε}` and `Lⁿ⁺¹ = LⁿL`, using language concatenation. Then `L*` is the union of `Lⁿ` for all integers `n ≥ 0`.

The bypass recognizes `L⁰`. A non-bypass successful path traverses the operand one or more times, using the repeat edge between traversals and the exit edge after the last one. If there are `n` traversals, its label is a concatenation of `n` words in `L`, so it belongs to `Lⁿ`. Conversely, successful operand paths for any such finite sequence can be joined by the repeat edges.

An infinite walk is not a successful completed input path. Epsilon cycles can make finite paths redundant, but do not alter the language argument or require infinite execution.

</details>

## Common mistakes

- **Forgetting the zero-repetition case.** Every star accepts empty input; the bypass explains why.
- **Looping from the operand entry instead of its exit.** Repetition follows a completed operand word, not an arbitrary prefix.
- **Using unguarded recursive epsilon traversal.** A nullable operand can create epsilon-only cycles. Use the delivered cycle-safe evaluator.

## Source evidence

- **Original commentary:** [Java's Kleene closure, lines 165–186](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L165-L186), describes the star construction.
- **Documented meaning:** [Python's star node, lines 64–68](../../python/src/jautomata/regex.py#L64-L68), specifies zero-or-more repetition.
- **Verified source behavior:** [Repeat and star-only bypass, lines 84–92](../../python/src/jautomata/thompson.py#L84-L92), builds these edges; [the visited work list, lines 67–77](../../python/src/jautomata/simulation.py#L67-L77), terminates on cycles.
- **Supplement:** The language definition, closure tables, and nested-star argument explain the source. See the [source map](../reference/source-curriculum.md).

## Recap and resume

Star provides both a zero-repetition bypass and a repeat-after-completion edge. Repetition applies to whole operand words, which may themselves be empty.

**Stopping point:** Name the edge responsible for empty-input acceptance. **Resume:** Run the [star tutorial](../tutorials/kleene-star.md), then study the carefully different rule for [positive closure](positive-closure.md).
