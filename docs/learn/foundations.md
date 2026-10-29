# Foundations: read an automaton before you run one

**Objective:** identify the parts of a finite automaton and predict whether a
small machine accepts a string. Start here if terms such as *state* or
*transition* are new.

## Before you start

You need basic Python: run a command, import a function, and read a set such as
`{0, 1}`. You do **not** need a previous automata course. Work through one
trace at a time; the notation below is introduced before the later lessons use
it.

## Notation

- `Q` is a finite set of states, such as `{0, 1, 2}`.
- `q0` is the start state: where a run begins.
- `F` is the set of accepting (or final) states.
- `q --a--> r` means that reading one `a` can move from `q` to `r`.
- `ε` means “consume no input.” In this Python package it is represented by
  `None`, not by the string `""`.
- `δ` names the transition rule. An NFA may have zero, one, or many possible
  next states for the same `(state, symbol)` pair.

## A two-state machine

For the language containing only `"a"`, use `Q = {0, 1}`, `q0 = 0`,
`F = {1}`, and `0 --a--> 1`.

Read the figure: the start arrow enters 0; one `a` reaches double-circle final 1.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="One literal, two states, scrollable diagram" style="--diagram-width: 442px">
  <img class="diagram" src="/JAutomata/diagrams/literal.svg" alt="Start state 0 consumes one a to reach double-circle accepting state 1.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/literal.svg">Open full-size diagram</a></p>

| Input | Active states after the next character | Accept? |
|---|---|---|
| `""` | `{0}` | no: `0` is not final |
| `"a"` | `{1}` | yes |
| `"aa"` | `{1}`, then `{}` | no |

The last row is important: a run that has no matching transition has no active
states. It does not remain in the old state.

~~~python
from jautomata import accepts, compile_regex

one_a = compile_regex("a")
assert accepts(one_a, "a") is True
assert accepts(one_a, "") is False
assert accepts(one_a, "aa") is False
~~~

**Expected output:** the snippet prints nothing. Every assertion succeeds.

### Common mistake

Do not treat a final state as “accept at any time.” The machine accepts only
when input is exhausted *and* an active state is final. That is why `"aa"` is
rejected above.

<details>
<summary>Exercise — describe the language of <code>a*</code>, then check it.</summary>

`a*` accepts zero or more `a` characters: `""`, `"a"`, and `"aa"` are
accepted; `"b"` is not.

~~~python
from jautomata import accepts, compile_regex

many_a = compile_regex("a*")
assert [accepts(many_a, text) for text in ("", "a", "aa", "b")] == [True, True, True, False]
~~~
</details>

## Deeper: the recognition invariant

After the first `i` characters, the active set is exactly the set of states
reachable by a path labeled with the first `i` characters, including any
epsilon moves around that path. The evaluator keeps that set rather than a
mutable flag on a state. Its public contract is documented in
[the Python API](../python-api.md#acceptsautomaton-text), and its work-list
implementation is the intentional correction to the original Java evaluator's
state-flag approach ([Java commentary](../java-reference.md#defects-and-port-decisions)).

**Next:** learn the small regex language that creates these machines in
[Regex syntax](regex-syntax.md).
