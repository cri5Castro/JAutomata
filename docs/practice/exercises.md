# Practice: predict, trace, then run

Use the learning path in order when you are new to automata. These exercises
move from a single operator to the compound expression in the existing
[tutorial](../tutorial.md). Each answer is hidden until you choose to reveal it.

## 1. Explicit concatenation

**Objective:** distinguish the accepted grammar from familiar regex dialects.

What should happen when you compile `"ab"`? What expression accepts that same
two-character word in this package?

<details>
<summary>Reveal solution</summary>

`"ab"` raises `RegexSyntaxError`: adjacent operands have no implicit
concatenation. Write `"a.b"`.

~~~python
from jautomata import RegexSyntaxError, compile_regex

try:
    compile_regex("ab")
except RegexSyntaxError:
    pass
else:
    raise AssertionError("implicit concatenation must be rejected")
~~~
</details>

## 2. Follow an epsilon path

**Objective:** use closure before consuming input.

For the `cycle` machine in [Epsilon closure](../learn/epsilon-closure.md), why
is `"a"` accepted even though state `0` has no `a` edge?

<details>
<summary>Reveal solution</summary>

The start closure includes state `1`; `1 --a--> 2`, and `2` is final. The
machine is not forced to choose only the start state after closure.

Read the figure: epsilon makes state 1 available before the `a` is consumed.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Epsilon closure: visit a cycle, then consume a, scrollable diagram" style="--diagram-width: 593px">
  <img class="diagram" src="/JAutomata/diagrams/epsilon-closure.svg" alt="Start 0 and state 1 form an epsilon cycle; state 1 consumes a to reach double-circle final 2.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/epsilon-closure.svg">Open full-size diagram</a></p>
</details>

## 3. Predict the compound tutorial

**Objective:** separate a local empty match from an outer repetition rule.

For `(a.b|a*.c)+`, classify `""`, `"c"`, `"ac"`, `"ab"`, and `"a"` before
running the example.

<details>
<summary>Reveal solution</summary>

The outcomes are `False, True, True, True, False`. The `a*` part may be empty
inside the `.c` branch, but the outer `+` still requires one whole branch.

~~~python
from jautomata import accepts, compile_regex, to_dfa

nfa = compile_regex("(a.b|a*.c)+")
dfa = to_dfa(nfa)
expected = {"": False, "c": True, "ac": True, "ab": True, "a": False}
for text, answer in expected.items():
    assert accepts(nfa, text) == answer
    assert accepts(dfa, text) == answer
~~~
</details>

## 4. Explain the sink

**Objective:** connect a missing transition to the empty subset.

Why does a complete DFA for `a.b*` need a transition on `a` from a state that
has already consumed its initial `a` and then reads another `a`?

<details>
<summary>Reveal solution</summary>

The original NFA has no such move, so the subset transition leads to `{}`. The
complete DFA represents `{}` as a reachable non-final sink, which must also
have a destination for every alphabet symbol. This does not change acceptance;
it makes the transition function total over the source alphabet.
</details>

## What to do next

Run the end-to-end [tutorial](../tutorial.md), then use the
[API reference](../python-api.md) while building your own automata. If a term
slows you down, use the [Glossary](../reference/glossary.md) instead of trying
to infer it from a later section.
