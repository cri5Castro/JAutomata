---
title: "Thompson construction: one fragment at a time"
---

import TracePlayer from '../../../components/TracePlayer.astro';

**Objective:** trace how a valid regex becomes an epsilon-NFA without needing
to draw every implementation detail at once.

Thompson construction keeps a stack of *fragments*. A fragment has one entry
state and one exit state. A literal creates two states and one labeled edge;
each operator pops completed fragments and pushes one new fragment.

## Worked trace: `a.b`

The parser emits postfix `a b .`.

1. `a` creates `0 --a--> 1`.
2. `b` creates `2 --b--> 3`.
3. `.` adds `1 --ε--> 2` and keeps entry `0` and exit `3`.

The resulting NFA accepts `"ab"`. The epsilon edge joins the fragments but
does not consume a character.

Read the figure from start 0 to double-circle final 3: the epsilon seam consumes no input.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Concatenation: a then b, scrollable diagram" style="--diagram-width: 746px">
  <img class="diagram" src="/JAutomata/diagrams/concatenation.svg" alt="Start 0 consumes a to 1, follows epsilon to 2, then consumes b to accepting state 3." />
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/concatenation.svg">Open full-size diagram</a></p>

| State | Transition | Meaning |
| --- | --- | --- |
| 0 | `a → 1` | consume the first literal |
| 1 | `ε → 2` | connect the fragments without input |
| 2 | `b → 3` | consume the second literal |
| 3 | accepting | the whole expression matched |

<TracePlayer trace="thompson-ab" />

~~~python
from jautomata import accepts, compile_regex

ab = compile_regex("a.b")
assert len(ab.states) == 4
assert accepts(ab, "ab") is True
assert accepts(ab, "a") is False
~~~

**Expected output:** the assertions succeed; this implementation uses four
states for `a.b` because concatenation epsilon-links two literal fragments.

### Common mistake

Do not assume that an NFA has one outgoing edge per symbol. Union creates a
choice: the evaluator must retain every reachable branch, not pick one.

<details>
<summary>Exercise — explain why <code>a*</code> accepts the empty string.</summary>

Star adds a new entry and exit plus an epsilon bypass from the new entry to the
new exit. That bypass gives a complete path with zero literal edges.

~~~python
from jautomata import accepts, compile_regex

star = compile_regex("a*")
assert accepts(star, "") is True
assert accepts(star, "aaa") is True
~~~
</details>

## From textbook rule to this package

`|`, `*`, and `+` add fresh entry/exit states and epsilon links; `+` omits the
zero-repetition bypass. Each call allocates a fresh immutable `Automaton`, so a
later compilation cannot mutate an earlier one. The builder consumes postfix
with an explicit Python list, so nesting and long concatenation chains do not
depend on Python recursion depth.

The corresponding Java class explicitly identifies Thompson construction
([comment](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L9-L14)).
Its active concatenation can fuse mutable states; Python keeps the simpler,
value-oriented epsilon-link variant described by
[`compile_regex`](../python-api.md#compile_regexexpression).

**Next:** follow the zero-cost arrows safely in
[Epsilon closure](epsilon-closure.md).
