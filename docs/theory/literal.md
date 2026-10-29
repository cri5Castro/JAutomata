# Thompson construction: a literal

**Objective:** Explain why one literal needs two states and one consuming edge, then use that fragment as a reliable building block.

**Prerequisites:** [Automata and whole-string acceptance](automata.md), [regex notation](regex.md), and [postfix construction order](parsing.md).

**Route:** Read the diagram, follow the trace, then answer the prediction. The formal argument is optional. Continue with the [runnable literal tutorial](../tutorials/literal.md) when ready.

## One character, one edge

A **literal** stands for itself. The expression `a` describes the language `{a}`: the set containing the one-character word `a`. It does not describe every word containing `a`.

Thompson construction builds a small graph for each expression and connects those graphs. For a literal, create two distinct states and connect them with the literal character:

~~~text
entry / start                  exit / final
     0 ----------- a -------------> 1
~~~

The arrow consumes exactly one `a`. State `0` is the start; state `1` is the only final state of this completed machine. With no input, the machine remains at `0` and rejects. After reading `a`, it reaches `1` and accepts. Another character cannot be consumed because `1` has no outgoing edge.

Here and throughout these lessons, `ε` on an arrow means an **epsilon transition**, which consumes no input. The literal fragment has no such arrow. In Python an epsilon edge has `symbol=None`; a diagram's `ε` is mathematical notation, not a special epsilon token in this regex dialect.

## The fragment contract

A **fragment** is a partial machine with one designated entry and one designated exit. For these constructions, before the fragment is embedded in a larger graph, no edge enters its entry and no edge leaves its exit. Its internal paths describe exactly the words of its expression.

That boundary is useful: a later construction can connect to the entry and exit without inspecting every internal state. Embedding a child can add incoming or outgoing edges to the child's boundaries. The boundary rule then applies to the resulting enclosing fragment.

There is one exit per fragment, but this is a construction invariant, not a universal restriction on finite automata. General automata may have several final states or none. At the end of compilation, the compiler marks only the enclosing fragment's exit as final.

**Fresh** IDs keep separate fragments separate. Compiling `a.a` creates one `a` edge from `0` to `1` and another from `2` to `3`. Using the same letter does not mean reusing the same states. Otherwise, connecting the pieces could create accidental loops or shortcuts.

Allocation is local to a compilation. A separate call compiling `b` may also use IDs `0` and `1`; those numbers belong to a different graph. They are not globally unique identifiers.

## Work through the base case

The validated postfix sequence for `a` contains just the token `a`. The fragment stack starts empty.

| Step | Builder action | Fragment stack, bottom to top |
| --- | --- | --- |
| Before the token | No states or edges exist | empty |
| Read `a` | Allocate distinct IDs `0` and `1` | empty |
| Add the edge | Store `0 --a--> 1` | empty |
| Finish the token | Push the pair `(entry=0, exit=1)` | `(0, 1)` |
| Finish compilation | Use entry `0` as start and exit `1` as final | one completed fragment |

Recognition of a word is a separate operation from this construction. For the completed graph:

| Input | Trace | Result |
| --- | --- | --- |
| empty word, written `ε` or Python `""` | Stay at `0` | reject |
| `a` | `0 --a--> 1`, all input consumed | accept |
| `b` | No matching edge from `0` | reject |
| `aa` | First `a` reaches `1`; second has no edge | reject |

Stop here if you can explain both rejections without running code. That is the main idea.

## Predict before revealing

**Prediction 1:** Would a single state that is both start and final, with an `a` self-loop, recognize the same language?

<details>
<summary>Reveal the answer and reason</summary>

No. A start state that is final accepts the empty word before taking an edge. The self-loop also accepts `aa`, `aaa`, and every longer all-`a` word. That graph recognizes `a*`, not the literal `a`. Two distinct endpoints prevent both the empty-word shortcut and repetition.

</details>

**Prediction 2:** The compiler sees two literal tokens with the same value in `a.a`. How many states do the two base fragments require before they are joined?

<details>
<summary>Reveal the answer and reason</summary>

Four. Each occurrence creates its own two-state fragment. Equality of character labels does not imply equality of state IDs. The concatenation operation will add an epsilon edge between the fragments; it does not need to create more states.

</details>

## Optional: why the base case is correct

<details>
<summary>Read the short correctness argument</summary>

This is supplemental reasoning, not a quotation from the original comments. Let `L(R)` mean the language described by expression `R`. For a literal `c`, `L(c) = {c}`.

The fragment's only path from entry to exit is its single `c` edge. Therefore every successful path consumes `c`, and consuming `c` provides a successful path. These are the two directions required to show that the fragment recognizes exactly `{c}`. Distinct endpoints rule out a zero-edge accepting path.

Later construction rules assume their operand fragments already recognize the correct languages. This literal argument supplies the base case for that compositional proof.

</details>

## Common mistakes

- **Accepting a prefix instead of the whole input.** Reaching the final state after the first `a` does not accept `ab`; every input character must be consumed.
- **Treating `None` as a character.** It labels a non-consuming edge. A literal such as `a` labels a consuming edge.
- **Reusing states for repeated letters.** State identity records position in the construction, not the letter on an edge.

## Source evidence

- **Original commentary:** [Java's basic construction, lines 64–84](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L64-L84), describes the one-character construction and avoiding repeated state names. Its comment mentions a counter parameter, but the method signature takes only the character.
- **Documented contract:** [Python fragment and allocator, lines 22–55](../../python/src/jautomata/thompson.py#L22-L55), state the single-entry/single-exit and fragment-stack design.
- **Verified source behavior:** [Literal allocation, lines 56–63](../../python/src/jautomata/thompson.py#L56-L63), creates two fresh states and one edge. The [tutorial](../tutorials/literal.md) checks this exact shape.
- **Supplement:** The language notation, boundary reasoning, trace, and correctness argument above explain the implementation. See the [curriculum source map](../reference/source-curriculum.md) for the wider provenance.

## Recap and resume

A literal fragment has two distinct states, one consuming edge, one entry, and one exit. Fresh IDs allow independently constructed pieces to be composed safely.

**Stopping point:** Write down why `a` rejects both `""` and `"aa"`. **Resume:** Run the [literal tutorial](../tutorials/literal.md), then learn how [concatenation](concatenation.md) joins two fragments.
